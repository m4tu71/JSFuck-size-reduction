"""Execution checks for alternative Function constructor access paths."""
import json
import shutil
import subprocess
import unittest

from jsfuck_py.function_constructor_study import (
    function_constructor_candidates, function_wrapper_candidates,
)


@unittest.skipUnless(shutil.which("node"), "Node.js required")
class FunctionConstructorStudyTests(unittest.TestCase):
    def test_all_candidates_are_function_constructor(self):
        candidates = function_constructor_candidates()
        self.assertGreaterEqual(len(candidates), 8)
        self.assertTrue(all(set(expr) <= set("[]()!+") for expr in candidates.values()))

        script = (
            "const fs=require('fs');"
            "const source=JSON.parse(fs.readFileSync(0,'utf8'));"
            "process.stdout.write(JSON.stringify(source.map(s=>eval(s)===Function)))"
        )
        result = subprocess.run(
            ["node", "-e", script], input=json.dumps(list(candidates.values())),
            capture_output=True, text=True, timeout=40, check=True,
        )
        self.assertEqual(json.loads(result.stdout), [True] * len(candidates))

    def test_alternative_wrappers_execute_identically(self):
        variants = function_wrapper_candidates("return 42")
        script = (
            "const fs=require('fs');"
            "const source=JSON.parse(fs.readFileSync(0,'utf8'));"
            "process.stdout.write(JSON.stringify(source.map(s=>eval(s))))"
        )
        result = subprocess.run(
            ["node", "-e", script], input=json.dumps(list(variants.values())),
            capture_output=True, text=True, timeout=40, check=True,
        )
        self.assertEqual(json.loads(result.stdout), [42] * len(variants))

    def test_returned_shortest_access_is_no_longer_than_at(self):
        candidates = function_constructor_candidates()
        short = min(candidates.values(), key=len)
        self.assertLessEqual(len(short), len(candidates["array.at.constructor"]))


if __name__ == "__main__":
    unittest.main()
