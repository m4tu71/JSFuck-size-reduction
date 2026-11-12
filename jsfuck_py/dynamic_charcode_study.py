"""Research a single Function call for a batch of UTF-16 code units.

The existing numeric generator synthesizes apply/bind/reduce calls directly in
JSFuck. This alternative constructs JavaScript source text containing a
comma-separated list of character codes and executes it via one Function.

No commas appear in the emitted JSFuck: Array.prototype.join() inserts them
at runtime. The helper remains research-only until complete-cost and semantic
validation establish a benefit.
"""
from __future__ import annotations

from collections.abc import Callable

from .numeric_batch import _utf16_units

DELIMITERS = ("f", "false", "true", "NaN")


def dynamic_charcode_candidates(
    source: str,
    encode_text: Callable[[str], str],
    *,
    delimiters: tuple[str, ...] = DELIMITERS,
) -> dict[str, str]:
    """Generate JSFuck-only source-compilation alternatives for each delimiter."""
    if not source:
        return {}
    if not delimiters or any(
        not separator or any(char.isdigit() for char in separator)
        for separator in delimiters
    ):
        raise ValueError("Each separator must be a non-empty string without digits")

    function = "[][" + encode_text("at") + "][" + encode_text("constructor") + "]"
    # Avoid directly naming the global String constructor: its uppercase S
    # may be unavailable in the underlying direct JSFuck mapping.
    header = encode_text("return ([]+[]).constructor.fromCharCode(")
    tail = encode_text(")")
    split_key = "[" + encode_text("split") + "]"
    join_key = "[" + encode_text("join") + "]"
    codes = tuple(str(value) for value in _utf16_units(source))

    alternatives: dict[str, str] = {}
    for delimiter in delimiters:
        payload = encode_text(delimiter.join(codes))
        arguments = ("(" + payload + ")" + split_key +
                     "(" + encode_text(delimiter) + ")" + join_key + "()")
        compiled_source = (
            "(" + header + ")+(" + arguments + ")+(" + tail + ")"
        )
        alternatives[delimiter] = function + "(" + compiled_source + ")()"
    return alternatives
