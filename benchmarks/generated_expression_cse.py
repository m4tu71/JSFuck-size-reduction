"""Measure generated-expression CSE, separate from source-substring sharing."""
from __future__ import annotations

import json

from jsfuck_py.encoder import _tokens, encode
from jsfuck_py.expression_cse import cse_candidates, known_function_constructor


CASES = (
    ("false", False),
    ("false", True),
    ("?", False),
    ("?", True),
    ("あ", True),
    ("console.log(1)", True),
    ("const a=1;", True),
)


def main() -> None:
    constructor = known_function_constructor(lambda text: _tokens(text, True))
    print("Generated Function constructor expression:", len(constructor), "characters")
    print(f"{'source':22} {'wrap':>5} {'size':>7} {'count':>6} {'forced':>8} {'saving':>7}")
    for source, wrap in CASES:
        output = encode(source, wrap=wrap)
        choices = cse_candidates(
            output, constructor=constructor,
            encode_source_string=lambda code: encode(code),
            improvements_only=False,
        )
        forced = min((len(item[0]) for item in choices), default=None)
        print(f"{source[:22]!r:22} {str(wrap):>5} {len(output):7} "
              f"{output.count(constructor):6} "
              f"{str(forced) if forced is not None else '-':>8} "
              f"{len(output)-forced if forced is not None else 0:7}")


if __name__ == "__main__":
    main()
