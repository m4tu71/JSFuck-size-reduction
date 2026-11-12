"""Ablation of the optional Function-compiled UTF-16 batch candidate.

The benchmark removes only this candidate while retaining every existing
encoder optimization. Reports target-specific results separately from the
20 ordinary JavaScript examples.
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

from jsfuck_py import encoder

CASES = (
    "".join(chr(0x4e00 + i * 7) for i in range(64)),
    "".join(chr(0x4e00 + i * 11) for i in range(96)),
    "".join(chr(0x4e00 + i * 11) for i in range(128)),
    "".join(chr(0x4e00 + i * 11) for i in range(192)),
    "".join(chr(0x1f600 + i) for i in range(48)),
    "".join(chr(0x10000 + i * 71) for i in range(64)),
    "".join(chr(0x3041 + i) for i in range(56)),
    "const message='" + "".join(chr(0x4e00 + i * 13) for i in range(48)) + "';",
)


def measure(sources: tuple[str, ...], label: str) -> None:
    new_time_start = perf_counter()
    current = [len(encoder.encode(source)) for source in sources]
    new_seconds = perf_counter() - new_time_start

    old_time_start = perf_counter()
    with patch.object(encoder, "dynamic_charcode_candidates", return_value={}):
        previous = [len(encoder.encode(source)) for source in sources]
    old_seconds = perf_counter() - old_time_start

    print(f"CORPUS {label}")
    for source, old, new in zip(sources, previous, current, strict=True):
        assert new <= old
        print(f"{source[:25]!r:28} {old:8} -> {new:8}; saved {old-new:7}")
    before, after = sum(previous), sum(current)
    print(f"TOTAL {before} -> {after}; saved {before-after} "
          f"({100*(before-after)/before if before else 0:.2f}%)")
    print(f"ENCODE elapsed (wall clock, warm caches, non-isolated): "
          f"old={old_seconds:.3f}s new={new_seconds:.3f}s")


def main() -> None:
    measure(CASES, "targeted Unicode")
    ordinary = tuple(json.loads(Path("benchmarks/javascript_samples.json").read_text(
        encoding="utf-8"
    )))
    measure(ordinary, "ordinary JavaScript")


if __name__ == "__main__":
    main()
