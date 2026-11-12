"""Generated-output CSE feasibility tests."""
import unittest
import json
import shutil
import subprocess

from jsfuck_py.encoder import _tokens, encode
from jsfuck_py.expression_cse import (
    cse_candidates, known_function_constructor,
)


class ExpressionCSETests(unittest.TestCase):
    def test_known_subexpression_is_jsfuck(self):
        constructor = known_function_constructor(lambda x: _tokens(x, True))
        self.assertLessEqual(set(constructor), set("[]()!+"))

    def test_no_candidate_for_single_occurrence(self):
        constructor = known_function_constructor(lambda x: _tokens(x, True))
        self.assertEqual(
            cse_candidates(
                constructor,
                constructor=constructor,
                encode_source_string=lambda x: encode(x),
            ),
            [],
        )

    @unittest.skipUnless(shutil.which("node"), "Node.js required")
    def test_forced_candidate_preserves_semantics(self):
        constructor = known_function_constructor(lambda x: _tokens(x, True))
        original = constructor + "+[]+" + constructor
        variants = cse_candidates(
            original,
            constructor=constructor,
            encode_source_string=lambda source: encode(source),
            improvements_only=False,
        )
        self.assertTrue(variants)
        selected = variants[0][0]
        self.assertLessEqual(set(selected), set("[]()!+"))
        script = (
            "const xs=" + json.dumps([original, selected]) + ";"
            "process.stdout.write(JSON.stringify(xs.map(x=>eval(x))))"
        )
        proc = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True,
            check=True, timeout=30,
        )
        left, right = json.loads(proc.stdout)
        self.assertEqual(left, right)

    def test_budget_rejects_large_candidate(self):
        constructor = known_function_constructor(lambda x: _tokens(x, True))
        self.assertEqual(
            cse_candidates(
                constructor + "+" + constructor,
                constructor=constructor,
                encode_source_string=lambda x: encode(x),
                limit=10,
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
