"""Measure the marginal length reduction from typed primitive-token search.

The encoder's other transformations are held constant. This isolates the
new optimization from existing mappings, native-string tokens and wrappers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

from jsfuck_py import __version__, encoder

DEFAULT_CASES = Path(__file__).with_name("javascript_samples.json")


def compare(cases: list[str], *, wrap: bool = False) -> list[tuple[str, int, int]]:
    encoder._tokens.cache_clear()
    current = [len(encoder.encode(case, wrap=wrap)) for case in cases]
    encoder._tokens.cache_clear()
    try:
        # The reference candidate here is intentionally never shorter than
        # the legacy optimizer; it disables only typed_concat's contribution.
        with patch.object(
            encoder,
            "shortest_concatenation",
            side_effect=lambda text, *_: encoder._tokens(text, optimize=False),
        ):
            legacy = [len(encoder.encode(case, wrap=wrap)) for case in cases]
    finally:
        encoder._tokens.cache_clear()
    return list(zip(cases, legacy, current, strict=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--wrap", action="store_true")
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or any(not isinstance(x, str) for x in cases):
        parser.error("Expected a JSON array of strings")
    rows = compare(cases, wrap=args.wrap)
    before = sum(old for _, old, _ in rows)
    after = sum(new for _, _, new in rows)
    print(f"Encoder {__version__}, wrap={args.wrap}")
    for value, old, new in rows:
        print(f"{value[:36]!r:40} {old:>8} {new:>8} {old-new:>8}")
    print(f"Total {before} -> {after}; saved {before-after} "
          f"({100*(before-after)/before if before else 0:.2f}%)")


if __name__ == "__main__":
    main()
