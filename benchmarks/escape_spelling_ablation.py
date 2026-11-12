"""Controlled local-versus-whole-source Unicode escape spelling study.

The production encoder and its API remain unchanged: this diagnostic alone
tests alternative escape spellings before one Function constructor call.
"""
from __future__ import annotations

from jsfuck_py.encoder import _tokens, encode
from jsfuck_py.fused_wrapper_study import unicode_literal_source
from jsfuck_py.escape_spelling_search import best_spelled_source

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
    setup = len("[][" + _tokens("at", True) + "][" + _tokens("constructor", True) + "]()()")
    for source in CASES:
        local = unicode_literal_source(source)
        global_best = best_spelled_source(source)
        assert local is not None and global_best is not None
        old_cost = setup + len(_tokens(local, True))
        new_cost = setup + len(_tokens(global_best, True))
        baseline = len(encode(source, wrap=True, fuse_wrapped_unicode=True))
        old_total += min(baseline, old_cost)
        new_total += min(baseline, new_cost)
        print(f"{source[:33]!r:35} {old_cost:8} {new_cost:8} "
              f"{old_cost-new_cost:8} {min(baseline, new_cost):8}")
        assert new_cost <= old_cost
    print(f"Total best-with-local: {old_total} -> {new_total}; "
          f"additional saved: {old_total-new_total}")


if __name__ == "__main__":
    main()
