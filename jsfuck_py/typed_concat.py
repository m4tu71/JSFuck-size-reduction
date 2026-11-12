"""Precedence-safe, typed dynamic programming for JSFuck concatenation.

Treat mapping recipes as opaque JavaScript expressions: a textual '+' inside a
recipe may be an addition, unary operator, or part of property access. Their
syntax cannot safely be spliced into a larger expression without grouping.
The printer groups unknown operands and only elides parentheses for small,
explicitly known atomic primitives.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Expression:
    source: str
    is_string: bool
    # The complete expression may appear on the right of '+' without
    # parentheses. Never infer this from its first or last character.
    atomic_right: bool = False

    def as_string(self) -> "Expression":
        if self.is_string:
            return self
        return Expression(f"({self.source})+[]", True)


def concatenate(left: Expression, right: Expression) -> Expression:
    """Compose JSFuck expressions without changing JavaScript precedence."""
    if not (left.is_string or right.is_string):
        raise ValueError("Two non-string operands can perform numeric addition")
    rhs = right.source if right.atomic_right else f"({right.source})"
    # The complete left expression is already valid; binary '+' is left-
    # associative, so grouping is not needed for an accumulated prefix.
    return Expression(left.source + "+" + rhs, True)


def shortest_concatenation(
    text: str,
    mapping: dict[str, str],
    tokens: dict[str, str],
    primitives: dict[str, str],
    number: Callable[[int], str],
) -> str:
    """Find the shortest string-valued expression using typed token states."""
    if not text:
        return ""

    size = len(text)
    strings: list[Expression | None] = [None] * (size + 1)
    pending: list[Expression | None] = [None] * (size + 1)

    def relax(state: list[Expression | None], end: int, candidate: Expression) -> None:
        old = state[end]
        if old is None or len(candidate.source) < len(old.source):
            state[end] = candidate

    for start in range(size):
        char = text[start]
        # Mapped digits are arrays and become strings when added to strings.
        # The other character mappings are guaranteed string-valued.
        options = [(
            start + 1,
            Expression(mapping[char], not char.isdigit(), char.isdigit())
        )]
        if char.isascii() and char.isdigit():
            options.append((start + 1, Expression(number(int(char)), False)))
        options.extend(
            (
                start + len(word),
                Expression(expr, False, expr in ("![]", "!![]", "[][[]]")),
            )
            for word, expr in primitives.items()
            if text.startswith(word, start)
        )
        options.extend(
            (start + len(word), Expression(expr, True))
            for word, expr in tokens.items()
            if text.startswith(word, start)
        )

        for end, expr in options:
            if start == 0:
                relax(strings if expr.is_string else pending, end, expr)
                if not expr.is_string:
                    relax(strings, end, expr.as_string())
                continue

            prefix = strings[start]
            if prefix is not None:
                relax(strings, end, concatenate(prefix, expr))
            previous = pending[start]
            if previous is not None and expr.is_string:
                relax(strings, end, concatenate(previous, expr))

    candidates = [
        state.source
        for state in (strings[size], pending[size].as_string() if pending[size] else None)
        if state is not None
    ]
    if not candidates:
        raise ValueError("No string-valued JSFuck expression found")
    return min(candidates, key=len)
