"""Controlled ablation of extending repeat-unit length from 8 to 16.

Both branches retain all other encoder optimizations, including repeated
units of 2-8 characters. This isolates the incremental effect of the
change introduced in this PR rather than crediting earlier work.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

from jsfuck_py import encoder, multi_repeat

DEFAULT_CASES = Path(__file__).with_name("segment_generator_cases.json")


def compare(cases: list[str]) -> list[tuple[str, int, int]]:
    encoder._tokens.cache_clear()
    extended = [len(encoder.encode(source)) for source in cases]
    encoder._tokens.cache_clear()
    try:
        with patch.object(multi_repeat, "MAX_UNIT_LENGTH", 8):
            previous = [len(encoder.encode(source)) for source in cases]
    finally:
        encoder._tokens.cache_clear()
    return list(zip(cases, previous, extended, strict=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or any(not isinstance(x, str) for x in cases):
        parser.error("Expected JSON array of strings")
    rows = compare(cases)
    before = sum(old for _, old, _ in rows)
    after = sum(new for _, _, new in rows)
    for source, old, new in rows:
        print(f"{source[:32]!r:35} {old:>8} -> {new:>8} saved={old-new:>8}")
    print(f"Total {before} -> {after}, saved={before-after} "
          f"({100*(before-after)/before if before else 0:.2f}%)")


if __name__ == "__main__":
    main()
