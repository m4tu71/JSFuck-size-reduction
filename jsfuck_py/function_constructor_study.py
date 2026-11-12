"""Measure cost of structurally different ways to obtain Function.

Generator setup is a large part of JSFuck wrappers. This research probes
known type-correct Function constructors before attempting variable sharing.
All expressions are emitted using JSFuck alphabet and verified with Node.js.
No source rewriting or production encoder changes are made.
"""
from __future__ import annotations

from .encoder import _tokens

_NATIVE_FUNCTIONS = (
    "at", "flat", "filter", "map", "find", "sort", "join", "fill",
    "pop", "push", "slice", "splice", "reduce", "some", "every",
    "keys", "values", "entries", "reverse", "shift", "unshift",
)


def function_constructor_candidates() -> dict[str, str]:
    """Return JSFuck-only expressions evaluating to the Function constructor."""
    constructor = "[" + _tokens("constructor", True) + "]"

    candidates: dict[str, str] = {
        "array.constructor.constructor": "[]" + constructor + constructor,
        "string.constructor.constructor": "([]+[])" + constructor + constructor,
        "number.constructor.constructor": "(+[])" + constructor + constructor,
        "boolean.constructor.constructor": "(![])" + constructor + constructor,
    }
    for method in _NATIVE_FUNCTIONS:
        method_key = "[" + _tokens(method, True) + "]"
        candidates[f"array.{method}.constructor"] = "[]" + method_key + constructor
    return candidates


def function_wrapper_candidates(body: str, *, invoke: bool = True) -> dict[str, str]:
    """Compile one body through every Function-constructor expression."""
    payload = _tokens(body, True)
    ending = ")()" if invoke else ")"
    return {
        name: expression + "(" + payload + ending
        for name, expression in function_constructor_candidates().items()
    }
