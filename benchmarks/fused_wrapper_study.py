"""Compare one Function compilation with the ordinary Unicode decode + wrap.

Research-only: candidate grammar limited to simple console.log("...") calls.
"""
from __future__ import annotations

from jsfuck_py.encoder import encode
from jsfuck_py.fused_wrapper_study import direct_unicode_function_candidate

CASES = (
    'console.log("あ")',
    'console.log("漢字")',
    'console.log("漢字仮名交じり文")',
    'console.log("' + "漢字" * 12 + '")',
    'console.log("' + "漢字" * 36 + '")',
    'console.log("' + "😀😃" * 12 + '")',
    'console.log("' + "😀😃" * 36 + '")',
    'console.log("' + "ΩλЖ中" * 24 + '")',
    'console.log("hello")',
    'console.log("before" + "漢字")',
    'const x="漢字";console.log(x)',
)


def main() -> None:
    print(f"{'source':34} {'baseline':>9} {'direct':>9} {'saving':>9}")
    total_before = total_after = 0
    count = 0
    for source in CASES:
        baseline = encode(source, wrap=True)
        candidate = direct_unicode_function_candidate(source)
        if candidate is None:
            print(f"{source[:32]!r:34} {len(baseline):>9} {'n/a':>9} {'n/a':>9}")
            continue
        count += 1
        total_before += len(baseline)
        total_after += min(len(candidate), len(baseline))
        print(f"{source[:32]!r:34} {len(baseline):>9} {len(candidate):>9} "
              f"{len(baseline)-len(candidate):>9}")
    print(f"Eligible: {count}; best total {total_before} -> {total_after}; "
          f"saved {total_before-total_after}")


if __name__ == "__main__":
    main()
