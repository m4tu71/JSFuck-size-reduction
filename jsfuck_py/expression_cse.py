"""Experimental CSE of *generated JSFuck expressions*, not source text.

Only the known side-effect-free Function constructor expression is eligible.
CSE introduces a temporary parameter in a private, dynamically constructed
function, where the original JSFuck expression is evaluated as its body.

The complete encoded helper cost often exceeds the recovered duplication;
this candidate is *never* selected without an actual emitted-size win.
"""
from __future__ import annotations

from collections.abc import Callable

LOCAL_NAMES = ("a", "t", "f", "l", "n", "r", "e")
MAX_OUTPUT_LENGTH = 4000


def known_function_constructor(encode_token: Callable[[str], str]) -> str:
    """The concrete JSFuck-only expression used throughout the encoder."""
    return "[][" + encode_token("at") + "][" + encode_token("constructor") + "]"


def cse_candidates(
    output: str,
    *,
    constructor: str,
    encode_source_string: Callable[[str], str],
    limit: int = MAX_OUTPUT_LENGTH,
) -> list[tuple[str, str, int]]:
    """Build viable (output, parameter, occurrence count) candidates.

    This is deliberately a *semantic* target rather than textual substring
    replacement over arbitrary JSFuck. A generic replacement might cut through
    operators or property access and change program meaning.
    """
    count = output.count(constructor)
    if count < 2 or len(output) > limit:
        return []

    choices: list[tuple[str, str, int]] = []
    for name in LOCAL_NAMES:
        # Group references to prevent a neighboring +, ! or property lookup
        # from binding differently after substitution.
        rewritten = output.replace(constructor, "(" + name + ")")
        body = "return function(" + name + "){return " + rewritten + "}"
        encoded_body = encode_source_string(body)
        expression = constructor + "(" + encoded_body + ")()(" + constructor + ")"
        if len(expression) < len(output):
            choices.append((expression, name, count))

    return sorted(choices, key=lambda candidate: (len(candidate[0]), candidate[1]))
