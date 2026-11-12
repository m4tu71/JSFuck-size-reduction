"""Semantic validation for the experimental dynamic source compiler."""
import json
import shutil
import subprocess
import unittest

from jsfuck_py.encoder import _tokens
from jsfuck_py.dynamic_charcode import dynamic_charcode_candidates


class DynamicCharCodeStudyTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_utf16_batch_roundtrip(self):
        sources = (
            "ABC",
            "漢字",
            "😀😃",
            "ΩλЖ中",
            "a\x00b",
            "".join(chr(0x4e00 + i * 7) for i in range(32)),
        )
        expressions = []
        expected = []
        for source in sources:
            for expression in dynamic_charcode_candidates(
                source, lambda text: _tokens(text, True)
            ).values():
                self.assertTrue(set(expression) <= set("[]()!+"))
                expressions.append(expression)
                expected.append(source)
        js = (
            "const fs=require('fs');"
            "const expressions=JSON.parse(fs.readFileSync(0,'utf8'));"
            "process.stdout.write(JSON.stringify(expressions.map(x=>eval(x))))"
        )
        proc = subprocess.run(
            ["node", "-e", js], input=json.dumps(expressions),
            capture_output=True, text=True, timeout=40, check=True,
        )
        self.assertEqual(json.loads(proc.stdout), expected)

    def test_bad_delimiters_rejected(self):
        for bad in ((), ("",), ("1",), ("f2",)):
            with self.assertRaises(ValueError):
                dynamic_charcode_candidates(
                    "AB", lambda s: _tokens(s, True), delimiters=bad
                )


if __name__ == "__main__":
    unittest.main()
