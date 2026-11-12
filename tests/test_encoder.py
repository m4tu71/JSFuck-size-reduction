import json
import shutil
import subprocess
import unittest

from jsfuck_py.encoder import encode, _mapping


class EncoderTests(unittest.TestCase):
    def test_mapping_alphabet(self):
        self.assertTrue(all(set(v) <= set("[]()!+") for v in _mapping().values()))

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_each_mapped_character(self):
        for character, expression in _mapping().items():
            program = "try {process.stdout.write(JSON.stringify(String(eval(" + json.dumps(expression) + ")))) } catch(e) {process.stderr.write(e.message);process.exit(1)}"
            completed = subprocess.run(["node", "-e", program], text=True,
                                       capture_output=True, timeout=10)
            with self.subTest(character=character):
                self.assertEqual(completed.returncode, 0, repr(character) + ": " + completed.stderr)
                self.assertEqual(json.loads(completed.stdout), character)

    def test_encoder_output_alphabet(self):
        for value in ["", "0", "false", "true", "undefined", "NaN",
                      "console.log(1)", "Hello, world!", "あ😀", "~!~"]:
            with self.subTest(value=value):
                self.assertLessEqual(set(encode(value)), set("[]()!+"))

    @unittest.skipUnless(shutil.which("node"), "Node.js required for JS semantics")
    def test_roundtrip(self):
        values = ["0", "1", "2", "01", "10", "0abc", "1abc", "3", "false", "true", "undefined", "NaN",
                  "Infinity", "Hello world!", "const x=1;", '"\\',
                  "あ😀", "~!~", "a\nb"]
        for value in values:
            with self.subTest(value=value):
                expression = encode(value)
                program = "process.stdout.write(JSON.stringify(eval(" + json.dumps(expression) + ")))"
                completed = subprocess.run(
                    ["node", "-e", program], text=True, capture_output=True,
                    timeout=20, check=False)
                self.assertEqual(completed.returncode, 0, completed.stderr[-650:])
                self.assertEqual(json.loads(completed.stdout), value)

    @unittest.skipUnless(shutil.which("node"), "Node.js required for JS semantics")
    def test_components(self):
        cases = {
            "at": "at", "constructor": "constructor",
            "return_quote": 'return"',
            "function": None,
        }
        for key, expected in cases.items():
            expression = (encode(expected) if expected is not None else
                          "[][" + encode("at") + "][" + encode("constructor") + "]")
            js = ("try {process.stdout.write(String(eval(" + json.dumps(expression) + "))) }"
                  "catch(e){process.stderr.write(e.message);process.exit(1)}")
            result = subprocess.run(["node", "-e", js], capture_output=True, text=True)
            with self.subTest(key=key):
                self.assertEqual(result.returncode, 0, result.stderr)
                if expected is not None:
                    self.assertEqual(result.stdout, expected)
                else:
                    self.assertIn("function Function()", result.stdout)

    def test_return_quote_prefixes(self):
        for i in range(1, len('return"') + 1):
            value = 'return"'[:i]
            expression = encode(value)
            program = ("try {process.stdout.write(String(eval(" + json.dumps(expression) + "))) }"
                       "catch(e){process.stderr.write(e.message);process.exit(1)}")
            result = subprocess.run(["node", "-e", program], capture_output=True, text=True)
            with self.subTest(value=value):
                self.assertEqual(result.returncode, 0, result.stderr[-100:])
                self.assertEqual(result.stdout, value)

    def test_wrap(self):
        expression = encode("globalThis.__jsfuck_test = 42", wrap=True)
        script = "eval(" + json.dumps(expression) + ");console.log(globalThis.__jsfuck_test)"
        completed = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True,
            timeout=20, check=True)
        self.assertEqual(completed.returncode, 0, completed.stderr[-650:])
        self.assertEqual(completed.stdout.strip(), "42")

    def test_optimizer_no_worse_for_direct_mapping(self):
        for value in ["0", "1", "2", "01", "10", "1234", "false", "truefalse", "abc123", "Infinity", "undefined"]:
            self.assertLessEqual(len(encode(value)), len(encode(value, optimize=False)))


if __name__ == "__main__":
    unittest.main()
