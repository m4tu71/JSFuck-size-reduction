"""Research-only JS Unicode escape spelling checks."""
import unittest

from jsfuck_py.encoder import _tokens, encode
from jsfuck_py.escape_spelling_search import best_spelled_source, escape_spellings
from jsfuck_py.fused_wrapper_study import unicode_literal_source


class EscapeSpellingStudyTests(unittest.TestCase):
    def test_alternative_spellings_are_bounded_and_valid(self):
        self.assertIsNone(best_spelled_source("console.log(1)"))
        self.assertGreaterEqual(len(escape_spellings("😀")), 2)
        self.assertIn("\\u3042", escape_spellings("あ"))

    def test_global_cost_never_exceeds_local_greedy(self):
        for source in (
            'console.log("あ")',
            'console.log("漢字")',
            'console.log("😀😃")',
            "console.log('Ωλ')",
            'console.log("漢字");console.log("あ")',
        ):
            with self.subTest(source=source):
                local = unicode_literal_source(source)
                searched = best_spelled_source(source)
                self.assertIsNotNone(local)
                self.assertIsNotNone(searched)
                self.assertLessEqual(len(_tokens(searched, True)),
                                     len(_tokens(local, True)))
                self.assertTrue(set(_tokens(searched, True)) <= set("[]()!+"))

    def test_production_output_unchanged(self):
        source = 'console.log("あ")'
        self.assertEqual(
            encode(source, wrap=True),
            encode(source, wrap=True, fuse_wrapped_unicode=False),
        )


if __name__ == "__main__":
    unittest.main()
