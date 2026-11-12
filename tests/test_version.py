"""Versioning and reproducibility tests."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

import jsfuck_py
from jsfuck_py import _version


class VersionTests(unittest.TestCase):
    def test_single_source(self):
        self.assertEqual(jsfuck_py.__version__, _version.__version__)
        self.assertRegex(jsfuck_py.__version__, r"^\d+\.\d+\.\d+(?:\.dev\d+)?$")

    def test_cli_version_without_reference_download(self):
        result = subprocess.run(
            [sys.executable, "-m", "jsfuck_py.benchmark", "--version"],
            text=True, capture_output=True, check=True,
        )
        self.assertIn(jsfuck_py.__version__, result.stdout)

    def test_packaging_uses_single_source(self):
        config = Path(__file__).resolve().parents[1] / "pyproject.toml"
        source = config.read_text(encoding="utf-8")
        self.assertIn('version = {attr = "jsfuck_py._version.__version__"}', source)
        self.assertIn("dynamic = [\"version\"]", source)


if __name__ == "__main__":
    unittest.main()
