"""Cost-based JSFuck candidates for long runs of one character.

String.prototype.repeat is only attractive when amortized over many output
characters. Generate a small bounded set of repeated-run candidates, and let
the main DP retain the original character mapping whenever shorter.
"""
from __future__ import annotations

from functools import lru_cache


MIN_REPEAT = 8
MAX_REPEAT = 256


@lru_cache(maxsize=256)
def repeat_sizes(run_length: int) -> tuple[int, ...]:
    """Test all counts up to 32; larger runs also try powers of two and full length."""
    if run_length < MIN_REPEAT:
        return ()
    initial = set(range(MIN_REPEAT, min(run_length, 32) + 1))
    large = {run_length, min(run_length, MAX_REPEAT)}
    size = 64
    while size <= min(run_length, MAX_REPEAT):
        large.add(size)
        size *= 2
    return tuple(sorted(n for n in initial | large if n <= MAX_REPEAT))


def count_expression(count: int, mapping: dict[str, str], number: callable) -> str:
    """Cheapest tested argument; repeat() coerces digit strings to numbers."""
    digits = str(count)
    candidates = [number(count)]
    if len(digits) > 1:
        candidates.append("+".join(mapping[d] for d in digits))
        candidates.append(number(int(digits[0])) + "+" +
                          "+".join(mapping[d] for d in digits[1:]))
    return min(candidates, key=len)


def repeat_candidates(
    text: str, start: int, mapping: dict[str, str], number: callable,
    repeat_key: str,
) -> list[tuple[int, str]]:
    """Return (end, expression) candidates for one contiguous character run."""
    character = text[start]
    if character not in mapping:
        return []

    end = start + 1
    while end < len(text) and text[end] == character and end - start < MAX_REPEAT:
        end += 1
    run_length = end - start
    if run_length < MIN_REPEAT:
        return []

    # Digit recipes in the mapping denote arrays; force their string value
    # before calling String.prototype.repeat().
    char_expr = mapping[character]
    if character.isascii() and character.isdigit():
        char_expr = "(" + char_expr + "+[])"

    source = "(" + char_expr + ")[" + repeat_key + "]"
    unit_cost = len(mapping[character]) + 1
    candidates: list[tuple[int, str]] = []
    for count in repeat_sizes(run_length):
        expression = source + "(" + count_expression(count, mapping, number) + ")"
        if len(expression) < unit_cost * count - 1:
            candidates.append((start + count, expression))
    return candidates
