import json
import random
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
                  "あ😀", "~!~", "a\nb", "~~", "~~!", "?x?", "\\~\\",
                  "E:R", "a?b!", "\\" + "\\" + "~", "あい", "😀😀", "t~t~", "xfalse", "xtrue", "xundefined", "xNaN",
                  "xInfinity", "falsefalse", "1false", "0NaN",
                  "truefalse", "xfalsefalse"]
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

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_whole_native_function_tokens(self):
        for method in ("at", "flat", "map", "join"):
            source = f"function {method}() {{ [native code] }}"
            output = encode(source)
            baseline = encode(source, optimize=False)
            self.assertLess(len(output), len(baseline))
            program = ("process.stdout.write(JSON.stringify(eval(" +
                       json.dumps(output) + ")))")
            result = subprocess.run(["node", "-e", program], text=True,
                                    capture_output=True, timeout=15, check=True)
            self.assertEqual(json.loads(result.stdout), source)

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_native_suffixes(self):
        from jsfuck_py.encoder import _mapping, _number
        from jsfuck_py.substring_search import native_suffix_tokens

        choices = native_suffix_tokens(_mapping(), _number)
        for value in ("at() { [native code] }", "() { [native code] }",
                      "native code] }", "map() { [native code] }"):
            with self.subTest(value=value):
                self.assertIn(value, choices)
                expression = encode(value)
                self.assertLess(len(expression), len(encode(value, optimize=False)))
                program = "process.stdout.write(JSON.stringify(eval(" + json.dumps(expression) + ")))"
                result = subprocess.run(
                    ["node", "-e", program], capture_output=True, text=True,
                    timeout=20, check=True,
                )
                self.assertEqual(json.loads(result.stdout), value)

    def test_native_suffix_candidates_are_jsfuck(self):
        from jsfuck_py.encoder import _mapping, _number
        from jsfuck_py.substring_search import native_suffix_tokens

        tokens = native_suffix_tokens(_mapping(), _number)
        self.assertTrue(tokens)
        self.assertTrue(all(set(expr) <= set("[]()!+") for expr in tokens.values()))

    def test_native_method_shortcuts(self):
        # These savings rely on the pinned reference/native function format.
        self.assertEqual(len(encode("native")), 162)
        self.assertLess(len(encode("function add(a,b){return a+b}")), 1602)
        for text in ("native", "function add(a,b){return a+b}", "at"):
            with self.subTest(text=text):
                self.assertLessEqual(len(encode(text)), len(encode(text, optimize=False)))

    def test_trailing_primitive_cost(self):
        for value in ("xfalse", "xtrue", "xundefined", "xNaN",
                      "xInfinity", "falsefalse", "truefalse", "1false"):
            with self.subTest(value=value):
                self.assertLess(len(encode(value)), len(encode(value, optimize=False)))

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_typed_primitive_tokens_in_middle(self):
        values = (
            "afalseb", "atruen", "xundefinedy", "xNaNy",
            "aInfinityb", "falsefalsefalse", "1true2", "0NaN1",
            "false0true", "1false2true3", "truefalse",
        )
        for value in values:
            with self.subTest(value=value):
                result = encode(value)
                program = (
                    "process.stdout.write(JSON.stringify(eval(" +
                    json.dumps(result) + ")))"
                )
                completed = subprocess.run(
                    ["node", "-e", program], capture_output=True, text=True,
                    timeout=20, check=True,
                )
                self.assertEqual(json.loads(completed.stdout), value)
                self.assertLessEqual(len(result), len(encode(value, optimize=False)))

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_ambiguous_punctuation_baseline(self):
        value = "1undefined!+"
        for optimized in (False, True):
            expr = encode(value, optimize=optimized)
            script = "process.stdout.write(JSON.stringify(eval(" + json.dumps(expr) + ")))"
            result = subprocess.run(
                ["node", "-e", script], capture_output=True, text=True,
                timeout=20,
            )
            with self.subTest(optimized=optimized):
                self.assertEqual(result.returncode, 0, "suffix="+repr(expr[-200:])+"; "+result.stderr[-300:])
                self.assertEqual(json.loads(result.stdout), value)

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_typed_concatenation_seeded_roundtrips(self):
        # Deterministic mutation corpus: operator precedence and coercion
        # bugs often escape one-off examples. Evaluate all cases in one Node
        # subprocess to keep this regression test inexpensive.
        generator = random.Random(20261112)
        pieces = (
            "false", "true", "undefined", "NaN", "Infinity",
            "0", "1", "2", "3", "a", "b", "x", "!",
            "+", "[]", "at", "foo",
        )
        values = [
            "".join(generator.choices(pieces, k=generator.randint(1, 5)))
            for _ in range(120)
        ]
        expressions = [encode(value) for value in values]
        script = (
            "const fs=require('fs');"
            "const xs=JSON.parse(fs.readFileSync(0,'utf8'));"
            "process.stdout.write(JSON.stringify(xs.map((x,i)=>{"
            "try{return eval(x)}catch(e){throw Error(i+\":\"+e.message+\":\"+x.slice(-80))}"
            "})))"
        )
        result = subprocess.run(
            ["node", "-e", script], input=json.dumps(expressions),
            capture_output=True, text=True, check=False, timeout=40,
        )
        self.assertEqual(result.returncode, 0, result.stderr[-900:])
        self.assertEqual(json.loads(result.stdout), values)

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_precedence_safe_typed_printer(self):
        from jsfuck_py.encoder import _SIMPLE, _mapping, _native_tokens, _number
        from jsfuck_py.typed_concat import shortest_concatenation

        values = (
            "1undefined", "falseNaNtrue", "0NaN1", "1true2",
            "falsefalsefalse", "2false3", "afalseb", "1undefinedt",
            "Infinitytrue", "NaNfalse", "1true2false3",
        )
        expressions = [
            shortest_concatenation(value, _mapping(), _native_tokens(), _SIMPLE, _number)
            for value in values
        ]
        script = (
            "const fs=require('fs');const xs=JSON.parse(fs.readFileSync(0,'utf8'));"
            "process.stdout.write(JSON.stringify(xs.map(x=>eval(x))))"
        )
        process = subprocess.run(
            ["node", "-e", script], input=json.dumps(expressions),
            text=True, capture_output=True, timeout=30, check=True,
        )
        self.assertEqual(json.loads(process.stdout), list(values))
        self.assertTrue(all(set(expr) <= set("[]()!+") for expr in expressions))

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_special_character_escape_pipeline_roundtrip(self):
        for value in ("1undefined!+", "false!+true", "a+true+b", "++!!", "[]+[]"):
            encoded = encode(value)
            script = "process.stdout.write(JSON.stringify(eval(" + json.dumps(encoded) + ")))"
            result = subprocess.run(
                ["node", "-e", script], capture_output=True, text=True,
                timeout=20, check=True,
            )
            self.assertEqual(json.loads(result.stdout), value)

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_repeated_character_tokens(self):
        examples = ("a" * 64, "x" * 32, "0" * 64,
                    "ab" + "z" * 40 + "cd", "false" * 15,
                    "console.log(\'" + "x" * 64 + "\')", "?" * 40)
        expressions = [encode(value) for value in examples]
        script = (
            "const fs=require('fs');const xs=JSON.parse(fs.readFileSync(0,'utf8'));"
            "process.stdout.write(JSON.stringify(xs.map(x=>eval(x))))"
        )
        completed = subprocess.run(
            ["node", "-e", script], input=json.dumps(expressions),
            capture_output=True, text=True, timeout=30, check=True,
        )
        self.assertEqual(json.loads(completed.stdout), list(examples))
        baselines = [len(encode(value, optimize=False)) for value in examples[:4]]
        self.assertTrue(any(len(expression) < baseline for expression, baseline in zip(expressions[:4], baselines)))
        for expression, baseline in zip(expressions[:4], baselines):
            self.assertLessEqual(len(expression), baseline)

    def test_repeat_cost_search(self):
        from jsfuck_py.repetition import repeat_candidates, repeat_sizes
        from jsfuck_py.encoder import _mapping, _number

        self.assertEqual(repeat_sizes(7), ())
        self.assertIn(32, repeat_sizes(64))
        self.assertTrue(
            repeat_candidates("x" * 64, 0, _mapping(), _number, encode("repeat"))
        )

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_batched_character_codes(self):
        from jsfuck_py.encoder import _tokens
        from jsfuck_py.numeric_batch import numeric_batch_candidates

        values = (
            "AB", "a☃", "漢字", "😀", "😀😃",
            "あ" * 30, "😀" * 20, "Ωλ" * 25,
            "const msg='" + "☃" * 25 + "';",
        )
        for value in values:
            candidates = numeric_batch_candidates(value, lambda s: _tokens(s, True))
            for method, expression in candidates.items():
                with self.subTest(input=value[:15], method=method):
                    self.assertTrue(set(expression) <= set("[]()!+"))
                    script = "process.stdout.write(JSON.stringify(eval(" + json.dumps(expression) + ")))"
                    completed = subprocess.run(
                        ["node", "-e", script], capture_output=True, text=True,
                        timeout=30, check=False,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr[-700:])
                    self.assertEqual(json.loads(completed.stdout), value)

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_batched_encoder_roundtrip(self):
        values = ("☃" * 30, "漢字" * 24, "😀" * 20, "AB" * 40)
        for value in values:
            expression = encode(value)
            script = "process.stdout.write(JSON.stringify(eval(" + json.dumps(expression) + ")))"
            completed = subprocess.run(
                ["node", "-e", script], capture_output=True, text=True,
                timeout=30, check=False,
            )
            with self.subTest(input=value[:10]):
                self.assertEqual(completed.returncode, 0, completed.stderr[-700:])
                self.assertEqual(json.loads(completed.stdout), value)

    def test_precedence_printer_rejects_numeric_addition(self):
        from jsfuck_py.typed_concat import Expression, concatenate

        with self.assertRaises(ValueError):
            concatenate(Expression("+[]", False), Expression("+!+[]", False))
        self.assertEqual(
            concatenate(Expression("[]+[]", True), Expression("!+[]+!+[]", False)).source,
            "[]+[]+(!+[]+!+[])",
        )

    def test_typed_primitive_reductions(self):
        # Middle tokens are not optimized by the older trailing-token rule.
        from jsfuck_py.encoder import _mapping, _native_tokens, _number, _SIMPLE
        from jsfuck_py.typed_concat import shortest_concatenation

        text = "afalseb"
        candidate = shortest_concatenation(
            text, _mapping(), _native_tokens(), _SIMPLE, _number
        )
        self.assertLess(len(candidate), len(encode(text, optimize=False)))

    def test_optimizer_no_worse_for_direct_mapping(self):
        for value in ["0", "1", "2", "01", "10", "1234", "false", "truefalse", "abc123", "Infinity", "undefined"]:
            self.assertLessEqual(len(encode(value)), len(encode(value, optimize=False)))


if __name__ == "__main__":
    unittest.main()
