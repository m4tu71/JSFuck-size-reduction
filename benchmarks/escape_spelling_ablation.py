"""Controlled global Unicode escape spelling study.

Compare local per-character minimum against the same fused wrapper with
bounded full-source token-cost substitutions. Default output is unchanged.
"""
from __future__ import annotations

from jsfuck_py.encoder import encode
from jsfuck_py.fused_wrapper_study import direct_unicode_function_candidate

CASES = (
    'console.log("あ")',
    'console.log("漢字")',
    'console.log("漢字仮名交じり文")',
    'console.log("ΩλЖ中")',
    'console.log("😀😃")',
    'console.log("áéíóú")',
    'console.log("ÀÉÖü")',
    'console.log("あい")',
    'console.log("あいう")',
    'console.log("漢字");console.log("あ")',
    'const x="漢字";console.log(x)',
    'console.log("' + "漢字" * 12 + '")',
)


def main() -> None:
    old_total = new_total = 0
    print(f"{'source':35} {'local':>8} {'global':>8} {'saved':>8} {'selected':>8}")
    for source in CASES:
        local = direct_unicode_function_candidate(source)
        global_best = direct_unicode_function_candidate(
            source, search_spellings=True
        )
        assert local is not None and global_best is not None
        existing = encode(source, wrap=True)
        selected = encode(
            source, wrap=True, fuse_wrapped_unicode=True,
            search_escape_spellings=True,
        )
        old_total += min(len(existing), len(local))
        new_total += len(selected)
        print(f"{source[:33]!r:35} {len(local):8} {len(global_best):8} "
              f"{len(local)-len(global_best):8} {len(selected):8}")
        assert len(global_best) <= len(local)
    print(f"Total best-with-local: {old_total} -> {new_total}; "
          f"additional saved: {old_total-new_total}")


if __name__ == "__main__":
    main()
