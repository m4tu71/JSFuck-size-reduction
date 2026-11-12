"""Ablation of repeated-character token candidates.

The baseline keeps all other encoder optimizations active and suppresses only
String.prototype.repeat candidate insertion.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

from jsfuck_py import __version__, encoder

DEFAULT_CASES = Path(__file__).with_name("repetition_cases.json")


def compare(values: list[str]) -> list[dict[str, object]]:
    encoder._tokens.cache_clear()
    optimized = [len(encoder.encode(value)) for value in values]
    encoder._tokens.cache_clear()
    try:
        with patch.object(encoder, "repeat_candidates", return_value=[]):
            old = [len(encoder.encode(value)) for value in values]
    finally:
        encoder._tokens.cache_clear()
    return [
        {"input": value, "without_repeat": baseline,
         "with_repeat": current, "saved": baseline - current}
        for value, baseline, current in zip(values, old, optimized, strict=True)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args()
    values = json.loads(args.cases.read_text(encoding="utf-8"))
    if not isinstance(values, list) or not all(isinstance(x, str) for x in values):
        parser.error("Expected a JSON array of strings")
    results = compare(values)
    previous = sum(int(row["without_repeat"]) for row in results)
    current = sum(int(row["with_repeat"]) for row in results)
    print(f"Encoder: {__version__}")
    for row in results:
        print(f"{str(row['input'])[:35]!r:38} {row['without_repeat']:>8} "
              f"{row['with_repeat']:>8} {row['saved']:>8}")
    print(f"Total {previous} -> {current}; saved {previous-current} "
          f"({100*(previous-current)/previous if previous else 0:.2f}%)")


if __name__ == "__main__":
    main()
