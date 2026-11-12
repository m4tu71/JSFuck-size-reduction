"""Cost-driven alternatives for characters in Array.prototype.at's native text.

All recipes are compiled against a frozen snapshot of the standard mapping;
this prevents substitutions from becoming self-referential. The native
Function#toString representation is implementation-dependent, just like
upstream JSFuck's native-function recipes.
"""
from __future__ import annotations

from collections.abc import Callable

NATIVE_METHODS = ("at", "flat", "fill", "find", "map", "filter", "join", "sort", "entries")

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

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def index_for(position: int) -> str:
        digits = str(position)
        candidates = [number(position)]
        if position >= 10:
            candidates.append("+".join(baseline[d] for d in digits))
            candidates.append(number(int(digits[0])) + "+" +
                              "+".join(baseline[d] for d in digits[1:]))
        return min(candidates, key=len)

    for method in NATIVE_METHODS:
        if any(ch not in baseline for ch in method):
            continue
        method_key = "+".join(baseline[ch] for ch in method)
        native_method = "[][" + method_key + "]"
        native_text = f"function {method}() {{ [native code] }}"
        for prefix, expression in PREFIXES:
            source = "(" + expression + "+" + native_method + ")"
            rendered = prefix + native_text
            for offset, character in enumerate(rendered):
                if character not in mapping:
                    continue
                candidate = source + "[" + index_for(offset) + "]"
                if len(candidate) < len(mapping[character]):
                    mapping[character] = candidate
    # Iterator objects offer capital letters in "[object Array Iterator]".
    # A prefixed offset can make the index cheaper than extracting a letter
    # from a method name or a longer primitive string.
    if all(ch in baseline for ch in "entries"):
        iterator_method = "[][" + "+".join(baseline[ch] for ch in "entries") + "]()"
        for prefix, expression in PREFIXES:
            source = "(" + expression + "+" + iterator_method + ")"
            rendered = prefix + "[object Array Iterator]"
            for offset, character in enumerate(rendered):
                if character not in mapping:
                    continue
                candidate = source + "[" + index_for(offset) + "]"
                if len(candidate) < len(mapping[character]):
                    mapping[character] = candidate

    changes = {key: (len(value), len(mapping[key]))
               for key, value in baseline.items()
               if len(mapping[key]) < len(value)}
    return mapping, changes

def native_string_tokens(baseline: dict[str, str]) -> dict[str, str]:
    """Whole native-function strings offered as dynamic-programming tokens.

    The recipes are stable snapshots of the base mapping. Using the full
    native text avoids paying to encode its characters individually.
    """
    tokens: dict[str, str] = {}
    for method in NATIVE_METHODS:
        if any(ch not in baseline for ch in method):
            continue
        key = "+".join(baseline[ch] for ch in method)
        literal = f"function {method}() {{ [native code] }}"
        expression = "([]+[][" + key + "])"
        tokens[literal] = expression
    return tokens
