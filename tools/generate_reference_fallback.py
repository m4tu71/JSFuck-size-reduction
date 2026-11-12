"""Regenerate optional ASCII fallbacks from the pinned official JSFuck encoder.

This is a development-time tool only. The Python encoder does not execute
JavaScript or fetch resources at runtime.
"""
from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path
from urllib.request import urlopen

from jsfuck_py.benchmark import REFERENCE_COMMIT, REFERENCE_URL

CHARACTERS = "E R:?".replace(" ", "")
JS = """
const fs = require('fs');
const { source, chars } = JSON.parse(fs.readFileSync(0, 'utf8'));
const exports = {};
new Function('exports', source)(exports);
const output = Object.fromEntries(
  [...chars].map(char => [char, exports.JSFuck.encode(char, false, false)])
);
process.stdout.write(JSON.stringify(output));
"""


def main() -> None:
    reference = urlopen(REFERENCE_URL, timeout=20).read().decode("utf-8")
    completed = subprocess.run(
        ["node", "-e", JS],
        input=json.dumps({"source": reference, "chars": CHARACTERS}),
        capture_output=True, text=True, check=True,
    )
    encoded = json.loads(completed.stdout)
    if set(encoded) != set(CHARACTERS):
        raise RuntimeError("Official reference did not produce every expected recipe")
    allowed = set("[]()!+")
    if any(not isinstance(expr, str) or set(expr) - allowed for expr in encoded.values()):
        raise RuntimeError("Reference produced non-JSFuck characters")
    payload = base64.b64encode(
        json.dumps(encoded, separators=(",", ":")).encode("ascii")
    ).decode("ascii")
    print(f"OFFICIAL_FALLBACK_BASE64={payload}")
    print(f"Reference commit: {REFERENCE_COMMIT}")
    print("Character lengths:", {char: len(expr) for char, expr in encoded.items()})


if __name__ == "__main__":
    main()
