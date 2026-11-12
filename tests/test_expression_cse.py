"""Generated-output CSE feasibility tests."""
import unittest

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
