"""Controlled cost study of Function-constructor access in pure JSFuck."""
from __future__ import annotations

from jsfuck_py.encoder import encode
from jsfuck_py.function_constructor_study import (
    function_constructor_candidates, function_wrapper_candidates,
)

BODIES = ("return 42", "return true", "console.log(1)", 'console.log("hello")')


def main() -> None:
    constructors = function_constructor_candidates()
    baseline = len(constructors["array.at.constructor"])
    print(f"{'constructor':40} {'characters':>10} {'vs at':>9}")
    for name, source in sorted(constructors.items(), key=lambda item: len(item[1])):
        print(f"{name:40} {len(source):10} {len(source)-baseline:9}")
    print()
    for body in BODIES:
        candidates = function_wrapper_candidates(body)
        old = len(candidates["array.at.constructor"])
        short_name, short_expr = min(candidates.items(), key=lambda item: len(item[1]))
        print(f"body={body!r:27} baseline={old} best={len(short_expr)} "
              f"method={short_name} saving={old-len(short_expr)}")

    for original in ('console.log("あ")', "console.log(1)", "const value=42;"):
        expression = encode(original, wrap=True)
        constructor = constructors["array.at.constructor"]
        occurrences = expression.count(constructor)
        print(f"wrapped={original!r:27} JSFuck={len(expression)} "
              f"constructor_occurrences={occurrences}")


if __name__ == "__main__":
    main()
