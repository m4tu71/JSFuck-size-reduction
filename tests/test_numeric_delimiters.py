"""Numeric batch separator research regression tests."""
import json
import shutil
import subprocess
import unittest

from jsfuck_py.encoder import _tokens
from jsfuck_py.numeric_batch import numeric_batch_candidates


class NumericDelimiterTests(unittest.TestCase):
    def test_invalid_delimiters_rejected(self):
        for separators in ((), ("",), ("0",), ("false1",)):
            with self.subTest(separators=separators):
                with self.assertRaises(ValueError):
                    numeric_batch_candidates(
                        "AB", lambda text: _tokens(text, True),
                        separators=separators,
                    )

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_primitive_word_separator_roundtrip(self):
        source_strings = (
            "ABCABC",
            "漢字",
            "😀😃",
            "ΩλЖ中",
        )
        expressions = []
        expected = []
        for source in source_strings:
            for delimiter in ("false", "true", "NaN", "at"):
                for expression in numeric_batch_candidates(
                    source,
                    lambda text: _tokens(text, True),
                    separators=(delimiter,),
                ).values():
                    with self.subTest(source=source, delimiter=delimiter):
                        self.assertTrue(set(expression) <= set("[]()!+"))
                        expressions.append(expression)
                        expected.append(source)

        script = (
            "const fs=require('fs');"
            "const expressions=JSON.parse(fs.readFileSync(0,'utf8'));"
            "process.stdout.write(JSON.stringify(expressions.map(x=>eval(x))))"
        )
        completed = subprocess.run(
            ["node", "-e", script],
            input=json.dumps(expressions),
            capture_output=True, text=True, timeout=45, check=True,
        )
        self.assertEqual(json.loads(completed.stdout), expected)


if __name__ == "__main__":
    unittest.main()
