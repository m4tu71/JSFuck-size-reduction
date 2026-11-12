"""Ablation: conservative multi-literal Unicode source fusion.

Compare old `wrap=True` with experimental `fuse_wrapped_unicode=True`.
Unsupported syntax and cases where the candidate loses retain old output.
"""
from __future__ import annotations

from jsfuck_py.encoder import encode
from jsfuck_py.fused_wrapper_study import direct_unicode_function_candidate

CASES = (
    'console.log("あ")',
    'console.log("漢字")',
    'console.log("漢字", "あ")',
    'console.log("あ");console.log("い")',
    'const x="あ";console.log(x)',
    'const x="漢字";console.log(x)',
    'const x="あ";const y="い";console.log(x+y)',
    'let name="あ";console.log(name)',
    'console.log("漢字仮名交じり文")',
    'console.log("' + "😀😃" * 12 + '")',
    'console.log(`あ`)',
    'const x="あ"; // comment',
)


def main() -> None:
    total_old = total_new = 0
    eligible = 0
    print(f"{'input':39} {'before':>8} {'after':>8} {'saved':>8} {'candidate':>10}")
    for source in CASES:
        before = len(encode(source, wrap=True))
        after = len(encode(source, wrap=True, fuse_wrapped_unicode=True))
        candidate = direct_unicode_function_candidate(source)
        if candidate is not None:
            eligible += 1
        assert after <= before
        total_old += before
        total_new += after
        print(f"{source[:37]!r:39} {before:8} {after:8} {before-after:8} "
              f"{len(candidate) if candidate is not None else '-':>10}")
    print(f"Eligible: {eligible}, total {total_old} -> {total_new}, "
          f"saved {total_old-total_new} "
          f"({100*(total_old-total_new)/total_old:.2f}%)")


if __name__ == "__main__":
    main()
