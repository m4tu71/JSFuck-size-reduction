"""Controlled measurement of numeric character-code batch candidates.

The old result disables only the new numeric batch alternatives while keeping
all previously merged JSFuck optimizations active.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

from jsfuck_py import __version__, encoder
from jsfuck_py.numeric_batch import numeric_batch_candidates

DEFAULT_CASES = Path(__file__).with_name("long_unicode_cases.json")


def compare(values: list[str]) -> list[dict[str, object]]:
    encoder._tokens.cache_clear()
    current = [len(encoder.encode(value)) for value in values]
    encoder._tokens.cache_clear()
    try:
        with patch.object(encoder, "numeric_batch_candidates", return_value={}):
            previous = [len(encoder.encode(value)) for value in values]
    finally:
        encoder._tokens.cache_clear()

    return [
        {"input": value, "previous": old, "current": new, "saved": old - new}
        for value, old, new in zip(values, previous, current, strict=True)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args()
    values = json.loads(args.cases.read_text(encoding="utf-8"))
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        parser.error("Expected a JSON array of strings")
    results = compare(values)
    before = sum(int(row["previous"]) for row in results)
    after = sum(int(row["current"]) for row in results)
    print(f"Encoder {__version__}")
    for row in results:
        print(f"{str(row['input'])[:30]!r:34} {row['previous']:>8} "
              f"{row['current']:>8} {row['saved']:>8}")
    print(f"Total {before} -> {after}; saved {before-after} "
          f"({(before-after)/before*100 if before else 0:.2f}%)")


if __name__ == "__main__":
    main()
