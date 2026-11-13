"""Ablation of the optional Function-compiled UTF-16 batch candidate.

The benchmark removes only this candidate while retaining every existing
encoder optimization. Reports target-specific results separately from the
20 ordinary JavaScript examples.
"""
from __future__ import annotations

import json
from pathlib import Path
from contextlib import nullcontext
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


def timed_lengths(
    sources: tuple[str, ...], *, enable_dynamic: bool, clear_cache: bool
) -> tuple[list[int], float]:
    if clear_cache:
        encoder._tokens.cache_clear()
    context = (
        nullcontext() if enable_dynamic else
        patch.object(encoder, "dynamic_charcode_candidates", return_value={})
    )
    with context:
        started = perf_counter()
        lengths = [len(encoder.encode(source)) for source in sources]
        elapsed = perf_counter() - started
    return lengths, elapsed


def measure(sources: tuple[str, ...], label: str) -> None:
    # Cold-cache measurement for both variants, in a fixed documented order.
    previous, old_cold = timed_lengths(
        sources, enable_dynamic=False, clear_cache=True
    )
    current, new_cold = timed_lengths(
        sources, enable_dynamic=True, clear_cache=True
    )
    # Both variants then get the same populated token cache. Timings still
    # remain rough and must not be treated as calibrated performance claims.
    _, old_warm = timed_lengths(
        sources, enable_dynamic=False, clear_cache=False
    )
    _, new_warm = timed_lengths(
        sources, enable_dynamic=True, clear_cache=False
    )

    print(f"CORPUS {label}")
    for source, old, new in zip(sources, previous, current, strict=True):
        assert new <= old
        print(f"{source[:25]!r:28} {old:8} -> {new:8}; saved {old-new:7}")
    before, after = sum(previous), sum(current)
    print(f"TOTAL {before} -> {after}; saved {before-after} "
          f"({100*(before-after)/before if before else 0:.2f}%)")
    print(f"ENCODE elapsed (rough wall clock): "
          f"cold old={old_cold:.3f}s new={new_cold:.3f}s; "
          f"warm old={old_warm:.3f}s new={new_warm:.3f}s")


def main() -> None:
    measure(CASES, "targeted Unicode")
    ordinary = tuple(json.loads(Path("benchmarks/javascript_samples.json").read_text(
        encoding="utf-8"
    )))
    measure(ordinary, "ordinary JavaScript")


if __name__ == "__main__":
    main()
