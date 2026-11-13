"""Semantic validation for the experimental dynamic source compiler."""
import json
import shutil
import subprocess
import unittest
from unittest.mock import patch

from jsfuck_py import encoder

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
            "\ud800",
            "\udc00",
            "\ud800x\udc00",
            "".join(chr(0x4e00 + i * 7) for i in range(32)),
        )
        expressions = []
        expected = []
        for source in sources:
            for expression in dynamic_charcode_candidates(
                source, lambda text: _tokens(text, True),
                delimiters=("f", "false", "true", "NaN"),
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

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_automatic_candidate_and_wrapper(self):
        unicode_text = "".join(chr(0x4e00 + i * 11) for i in range(128))
        with patch.object(encoder, "dynamic_charcode_candidates", return_value={}):
            previous = encoder.encode(unicode_text)
        improved = encoder.encode(unicode_text)
        self.assertLess(len(improved), len(previous))
        self.assertTrue(set(improved) <= set("[]()!+"))

        source = "globalThis.__output='" + unicode_text + "';"
        wrapped = encoder.encode(source, wrap=True)
        script = (
            "eval(" + json.dumps(improved) + ");"
            "const value=eval(" + json.dumps(improved) + ");"
            "eval(" + json.dumps(wrapped) + ");"
            "process.stdout.write(JSON.stringify([value,globalThis.__output]))"
        )
        proc = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True,
            check=True, timeout=40,
        )
        self.assertEqual(json.loads(proc.stdout), [unicode_text, unicode_text])

    def test_bad_delimiters_rejected(self):
        for bad in ((), ("",), ("1",), ("f2",)):
            with self.assertRaises(ValueError):
                dynamic_charcode_candidates(
                    "AB", lambda s: _tokens(s, True), delimiters=bad
                )


if __name__ == "__main__":
    unittest.main()
