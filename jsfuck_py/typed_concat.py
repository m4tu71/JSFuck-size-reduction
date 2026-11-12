"""Typed, cost-based concatenation for JSFuck string expressions.

The search distinguishes a standalone non-string operand from a guaranteed
string prefix. This is important because JavaScript addition can be numeric
until at least one operand forces string concatenation.
"""
from __future__ import annotations

from collections.abc import Callable


def shortest_concatenation(
    text: str,
    mapping: dict[str, str],
    tokens: dict[str, str],
    primitives: dict[str, str],
    number: Callable[[int], str],
) -> str:
    """Return a JSFuck expression that evaluates to the given string.

    Search only well-typed additions: when a prefix is not yet a string, its
    next operand must be a mapped character or native string token. The final
    expression is guaranteed to be string-valued.
    """
    if not text:
        return ""

    n = len(text)
    string: list[str | None] = [None] * (n + 1)
    pending: list[str | None] = [None] * (n + 1)

    def relax(table: list[str | None], end: int, candidate: str) -> None:
        current = table[end]
        if current is None or len(candidate) < len(current):
            table[end] = candidate

    def append(prefix: str, expression: str, raw: bool) -> str:
        # A trailing unary plus must be grouped after binary addition.
        operand = "(" + expression + ")" if raw and expression.startswith("+") else expression
        return prefix + "+" + operand

    # Every candidate is (end_offset, expression, guarantees_string).
    for start in range(n):
        choices: list[tuple[int, str, bool]] = []
        character = text[start]
        choices.append((start + 1, mapping[character], not character.isdigit()))
        if character in "0123456789":
            choices.append((start + 1, number(int(character)), False))
        choices.extend(
            (start + len(word), expression, False)
            for word, expression in primitives.items()
            if text.startswith(word, start)
        )
        choices.extend(
            (start + len(word), expression, True)
            for word, expression in tokens.items()
            if text.startswith(word, start)
        )

        for end, expression, is_string in choices:
            if start == 0:
                relax(string if is_string else pending, end, expression)
                if not is_string:
                    relax(string, end, "(" + expression + "+[])")
                continue

            if string[start] is not None:
                relax(string, end, append(string[start], expression, not is_string))
            if pending[start] is not None and is_string:
                relax(string, end, append(pending[start], expression, False))

    results: list[str] = []
    if string[n] is not None:
        results.append(string[n])
    if pending[n] is not None:
        # Force conversion when the entire input consists of a primitive or
        # a one-character digit array. No untyped value escapes this function.
        results.append("(" + pending[n] + "+[])")
    if not results:
        raise ValueError("No typed concatenation for input")
    return min(results, key=len)
