"""Compare numeric-batch delimiters by complete emitted JSFuck size.

The current production encoder picks the cheapest one-character separator.
This controlled study tests multi-character primitive spellings such as
"false" and "true", keeping all other generator setup equal.
"""
from __future__ import annotations

from time import perf_counter

from jsfuck_py.encoder import _tokens, encode
from jsfuck_py.numeric_batch import numeric_batch_candidates

DELIMITERS = (
    "f", "a", "t", "e", "n", "l", "r", "i", ".",
    "false", "true", "undefined", "NaN", "at",
)
SOURCES = (
    "ABC" * 20,
    "漢字" * 12,
    "😀😃" * 10,
    "ΩλЖ中" * 12,
    "ABCD" * 12,
    "@#$" * 15,
    "function x(){return 42;}" * 4,
    "あ",
    "".join(chr(0x4e00 + i * 7) for i in range(64)),
    "".join(chr(0x4e00 + i * 11) for i in range(128)),
    "".join(chr(0x1f600 + i) for i in range(48)),
    "".join(chr(0x10000 + i * 71) for i in range(64)),
    "".join(chr(0x3041 + i) for i in range(56)),
    "const message=\'" + "".join(chr(0x4e00 + i * 13) for i in range(48)) + "\';",
)


def alternatives(source: str) -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    enc = lambda text: _tokens(text, True)
    old = numeric_batch_candidates(source, enc)
    winners: dict[str, tuple[str, str]] = {
        method: ("original", expression) for method, expression in old.items()
    }
    for delimiter in DELIMITERS:
        variants = numeric_batch_candidates(source, enc, separators=(delimiter,))
        for method, candidate in variants.items():
            if len(candidate) < len(winners[method][1]):
                winners[method] = (delimiter, candidate)
    return old, winners


def main() -> None:
    total_before = total_after = 0
    size_savings = 0
    started = perf_counter()
    for source in SOURCES:
        old, winners = alternatives(source)
        normal = encode(source)
        revised = min((normal, *(expression for _, expression in winners.values())),
                      key=len)
        total_before += len(normal)
        total_after += len(revised)
        for method, expression in old.items():
            delimiter, best = winners[method]
            size_savings += len(expression) - len(best)
            print(f"source={source[:26]!r:28} method={method:14} "
                  f"existing={len(expression):7} new={len(best):7} "
                  f"delimiter={delimiter!r}")
        print(f"  encoder: {len(normal)} -> {len(revised)}; saved={len(normal)-len(revised)}")
    print(f"Generator-only cumulative savings: {size_savings}")
    print(f"Full encoder: {total_before} -> {total_after}; "
          f"saved={total_before-total_after}")
    print(f"Study elapsed: {perf_counter()-started:.2f}s")


if __name__ == "__main__":
    main()
