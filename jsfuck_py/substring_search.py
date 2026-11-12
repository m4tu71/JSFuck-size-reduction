"""Generate substring candidates with total JSFuck expression costs.

JavaScript's String.prototype.slice accepts one argument to extract a suffix.
This is cheaper than synthesizing an unavailable comma for two arguments.
Candidates use a frozen mapping snapshot to avoid recursive definitions.
"""
from __future__ import annotations

from collections.abc import Callable

from .at_optimization import NATIVE_METHODS


def _index_expression(position: int, mapping: dict[str, str], number: Callable[[int], str]) -> str:
    """Return the cheapest tested expression coercible to a slice index."""
    digits = str(position)
    options = [number(position)]
    if position >= 10:
        options.extend((
            "+".join(mapping[d] for d in digits),
            number(int(digits[0])) + "+" + "+".join(mapping[d] for d in digits[1:]),
        ))
    return min(options, key=len)


def native_suffix_tokens(mapping: dict[str, str], number: Callable[[int], str]) -> dict[str, str]:
    """Find cost-effective suffixes of native function source strings.

    Store a candidate only when it is cheaper than the mapped-character
    concatenation. Full native strings are handled separately.
    """
    if any(ch not in mapping for ch in "slice"):
        return {}

    slice_key = "+".join(mapping[ch] for ch in "slice")
    result: dict[str, str] = {}

    for method in NATIVE_METHODS:
        if any(ch not in mapping for ch in method):
            continue

        method_key = "+".join(mapping[ch] for ch in method)
        native = f"function {method}() {{ [native code] }}"
        source = "([]+[][" + method_key + "])"

        for offset in range(1, len(native)):
            suffix = native[offset:]
            if len(suffix) < 4:
                continue

            # No comma is needed with a single starting index.
            candidate = source + "[" + slice_key + "](" + _index_expression(
                offset, mapping, number
            ) + ")"
            character_cost = sum(len(mapping[ch]) for ch in suffix) + len(suffix) - 1
            if len(candidate) >= character_cost:
                continue

            previous = result.get(suffix)
            if previous is None or len(candidate) < len(previous):
                result[suffix] = candidate

    return result
