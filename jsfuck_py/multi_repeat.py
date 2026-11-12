"""Bounded repeated-substring generation for the JSFuck token DP.

The generator operates only on a contiguous repeated segment. The repeated
unit is encoded as a normal JSFuck string, not an ordinary JavaScript literal.
Count and method-access costs are included in each candidate.
"""
from __future__ import annotations

from collections.abc import Callable

from .repetition import MAX_REPEAT

MAX_UNIT_LENGTH = 16


def repeated_unit_at(text: str, start: int, unit_len: int) -> int:
    """Return consecutive occurrences of a multi-character unit."""
    unit = text[start:start + unit_len]
    if len(unit) != unit_len:
        return 0
    count = 1
    while (
        count * unit_len < MAX_REPEAT
        and text.startswith(unit, start + count * unit_len)
    ):
        count += 1
    return count


def has_multi_repeat(text: str, *, min_copies: int = 3) -> bool:
    """Cheap preflight to avoid paying for a repeat property on normal text."""
    for length in range(2, MAX_UNIT_LENGTH + 1):
        for start in range(len(text) - length * min_copies + 1):
            unit = text[start:start + length]
            if text.startswith(unit, start + length) and text.startswith(
                unit, start + length * 2
            ):
                return True
    return False


def multi_repeat_candidates(
    text: str,
    start: int,
    encode_fragment: Callable[[str], str],
    count_expression_factory: Callable[[int], str],
    repeat_key: str,
    *,
    min_copies: int = 3,
) -> list[tuple[int, str]]:
    """Return cost-filtered (end, expression) for repeated substrings."""
    candidates: list[tuple[int, str]] = []
    for unit_len in range(2, MAX_UNIT_LENGTH + 1):
        copies = repeated_unit_at(text, start, unit_len)
        if copies < min_copies:
            continue
        unit = text[start:start + unit_len]
        # Bound count exploration without losing a candidate for the full run.
        counts = {min_copies, copies}
        counts.update(range(4, min(copies, 12) + 1))
        encoded_unit = encode_fragment(unit)
        source = "(" + encoded_unit + ")[" + repeat_key + "]"
        for count in sorted(counts):
            expression = source + "(" + count_expression_factory(count) + ")"
            # This is a conservative filter: the DP makes the definitive
            # comparison against all other available token combinations.
            naive_cost = len(encoded_unit) * count + count - 1
            if len(expression) < naive_cost:
                candidates.append((start + count * unit_len, expression))
    return candidates
