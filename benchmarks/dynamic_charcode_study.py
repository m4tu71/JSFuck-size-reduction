"""Cost comparison: Function-compiled UTF-16 batches vs apply/bind/reduce."""
from __future__ import annotations

from time import perf_counter

from jsfuck_py.encoder import _tokens, encode
from jsfuck_py.numeric_batch import numeric_batch_candidates
from jsfuck_py.dynamic_charcode import dynamic_charcode_candidates

SOURCES = (
    "漢字" * 12,
    "😀😃" * 10,
    "".join(chr(0x4e00 + i * 7) for i in range(64)),
    "".join(chr(0x4e00 + i * 11) for i in range(128)),
    "".join(chr(0x1f600 + i) for i in range(48)),
    "".join(chr(0x3041 + i) for i in range(56)),
    "const message='" + "".join(chr(0x4e00 + i * 13) for i in range(48)) + "';",
    "ABCD" * 12,
)


def main() -> None:
    before = after = 0
    started = perf_counter()
    for source in SOURCES:
        ordinary = encode(source)
        standard = numeric_batch_candidates(source, lambda s: _tokens(s, True))
        generated = dynamic_charcode_candidates(source, lambda s: _tokens(s, True))
        short_method, short_expr = min(generated.items(), key=lambda pair: len(pair[1]))
        before += len(ordinary)
        after += min(len(ordinary), len(short_expr))
        print(
            f"source={source[:24]!r:27} ordinary={len(ordinary):7} "
            f"old_batch={min(map(len,standard.values())):7} "
            f"dynamic={len(short_expr):7} sep={short_method!r:8} "
            f"net_saved={max(0,len(ordinary)-len(short_expr)):7}"
        )
    print(f"Full encoder {before} -> {after}, saved={before-after}")
    print(f"Study elapsed: {perf_counter()-started:.2f}s")


if __name__ == "__main__":
    main()
