import json
import shutil
import subprocess
import unittest

from jsfuck_py.encoder import encode, _mapping


class EncoderTests(unittest.TestCase):
    def test_mapping_alphabet(self):
        self.assertTrue(all(set(v) <= set("[]()!+") for v in _mapping().values()))

    def test_encoder_output_alphabet(self):
        for value in ["", "0", "false", "true", "undefined", "NaN",
                      "console.log(1)", "Hello, world!", "あ😀", "~!~"]:
            with self.subTest(value=value):
                self.assertLessEqual(set(encode(value)), set("[]()!+"))

    @unittest.skipUnless(shutil.which("node"), "Node.js required for JS semantics")
    def test_roundtrip(self):
        values = ["0", "3", "false", "true", "undefined", "NaN",
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
    def test_wrap(self):
        expression = encode("globalThis.__jsfuck_test = 42", wrap=True)
        script = "eval(" + json.dumps(expression) + ");console.log(globalThis.__jsfuck_test)"
        completed = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True,
            timeout=20, check=True)
        self.assertEqual(completed.returncode, 0, completed.stderr[-650:])
        self.assertEqual(completed.stdout.strip(), "42")

    def test_optimizer_no_worse_for_direct_mapping(self):
        for value in ["false", "truefalse", "abc123", "Infinity", "undefined"]:
            self.assertLessEqual(len(encode(value)), len(encode(value, optimize=False)))


if __name__ == "__main__":
    unittest.main()
