"""Compare side effects of the research-only fused Function wrapper."""
import json
import shutil
import subprocess
import unittest

from jsfuck_py.encoder import encode
from jsfuck_py.fused_wrapper_study import direct_unicode_function_candidate


@unittest.skipUnless(shutil.which("node"), "Node.js required")
class FusedWrapperStudyTests(unittest.TestCase):
    def test_unicode_literal_calls_have_identical_stdout(self):
        sources = (
            'console.log("あ")',
            'console.log("漢字")',
            'console.log("' + "漢字" * 24 + '")',
            'console.log("' + "😀😃" * 16 + '")',
            'console.log("' + "ΩλЖ中" * 16 + '")',
        )
        for source in sources:
            candidate = direct_unicode_function_candidate(source)
            with self.subTest(source=source[:30]):
                self.assertIsNotNone(candidate)
                self.assertLessEqual(set(candidate), set("[]()!+"))
                baseline = encode(source, wrap=True)
                actual = []
                for expression in (baseline, candidate):
                    result = subprocess.run(
                        ["node", "-e", "eval(" + json.dumps(expression) + ")"],
                        capture_output=True, text=True, timeout=40, check=True,
                    )
                    actual.append(result.stdout)
                self.assertEqual(actual[0], actual[1])

    def test_reject_unsupported_syntax(self):
        for source in (
            'console.log("hello")',
            "console.log('漢字')",
            'console.log("漢字" + "あ")',
            'const x="漢字";console.log(x)',
            'console.log("漢字\\u0041")',
        ):
            with self.subTest(source=source):
                self.assertIsNone(direct_unicode_function_candidate(source))


if __name__ == "__main__":
    unittest.main()
