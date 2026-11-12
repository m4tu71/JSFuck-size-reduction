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

    def as_string(self) -> "Expression":
        if self.is_string:
            return self
        # Addition is left associative; with an empty array on the right,
        # intermediate numeric additions complete before string conversion.
        return Expression(self.source + "+[]", True)


def needs_rhs_grouping(source: str) -> bool:
    """Determine if a JSFuck expression must be grouped as an addend.

    Skip balanced parenthesized and bracketed subexpressions. A leading unary
    plus would cause a lexical '++' after a binary plus, while top-level
    additions would change grouping if directly appended on the right.
    """
    if source.startswith("+"):
        return True
    depth = 0
    for char in source:
        if char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
            if depth < 0:
                raise ValueError("Unbalanced JSFuck expression")
        elif char == "+" and depth == 0:
            return True
    if depth != 0:
        raise ValueError("Unbalanced JSFuck expression")
    return False


def concatenate(left: Expression, right: Expression) -> Expression:
    """Compose expressions with correct precedence and string semantics."""
    if not (left.is_string or right.is_string):
        raise ValueError("Two non-string operands can perform numeric addition")
    rhs = f"({right.source})" if needs_rhs_grouping(right.source) else right.source
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
            Expression(mapping[char], not char.isdigit())
        )]
        if char.isascii() and char.isdigit():
            options.append((start + 1, Expression(number(int(char)), False)))
        options.extend(
            (
                start + len(word),
                Expression(expr, False),
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
