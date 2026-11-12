"""Cost-driven alternatives for characters in Array.prototype.at's native text.

All recipes are compiled against a frozen snapshot of the standard mapping;
this prevents substitutions from becoming self-referential. The native
Function#toString representation is implementation-dependent, just like
upstream JSFuck's native-function recipes.
"""
from __future__ import annotations

from collections.abc import Callable

NATIVE_AT_TEXT = "function at() { [native code] }"

# (runtime prefix, JSFuck expression). Expression prefixes must be coerced
# into a string by the following native-function object.
PREFIXES = (
    ("", "[]"),
    ("false", "![]"),
    ("true", "!![]"),
    ("undefined", "[][[]]"),
    ("NaN", "+[![]]"),
    ("0", "+[]"),
    ("1", "+!+[]"),
)


def optimize_native_at(
    baseline: dict[str, str], number: Callable[[int], str]
) -> tuple[dict[str, str], dict[str, tuple[int, int]]]:
    """Return a new mapping and {character: (old_size, new_size)} improvements."""
    mapping = baseline.copy()
    at_key = baseline["a"] + "+" + baseline["t"]
    at_method = "[][" + at_key + "]"
    changes = {}

    def index_for(position: int) -> str:
        digits = str(position)
        candidates = [number(position)]
        if position >= 10:
            candidates.append("+".join(baseline[d] for d in digits))
            candidates.append(number(int(digits[0])) + "+" +
                              "+".join(baseline[d] for d in digits[1:]))
        return min(candidates, key=len)

    for prefix, expression in PREFIXES:
        source = "(" + expression + "+" + at_method + ")"
        rendered = prefix + NATIVE_AT_TEXT
        for offset, character in enumerate(rendered):
            if character not in mapping:
                continue
            candidate = source + "[" + index_for(offset) + "]"
            if len(candidate) < len(mapping[character]):
                changes[character] = (len(mapping[character]), len(candidate))
                mapping[character] = candidate
    return mapping, changes
