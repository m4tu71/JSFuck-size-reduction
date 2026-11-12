"""Controlled ablation of multi-character repeat DP candidates.

Compares the same encoder with only the new candidate family disabled.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from jsfuck_py.encoder import encode
from jsfuck_py import encoder

CORPUS = Path(__file__).with_name("segment_generator_cases.json")


def main() -> None:
    cases = json.loads(CORPUS.read_text(encoding="utf-8"))
    current = [len(encode(x)) for x in cases]
    encoder._tokens.cache_clear()
    try:
        with patch.object(encoder, "multi_repeat_candidates", return_value=[]):
            original = [len(encode(x)) for x in cases]
    finally:
        encoder._tokens.cache_clear()
    print(f"{'input':32} {'before':>9} {'after':>9} {'saved':>9}")
    for source, old, new in zip(cases, original, current, strict=True):
        print(f"{source[:30]!r:32} {old:9} {new:9} {old-new:9}")
    print(f"Total: {sum(original)} -> {sum(current)}; "
          f"saved={sum(original)-sum(current)}")


if __name__ == "__main__":
    main()
