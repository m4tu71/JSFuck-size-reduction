"""Build JSFuck-only Unicode strings through dynamically compiled code units.

The existing numeric generator synthesizes apply/bind/reduce calls directly
in JSFuck. This generator instead compiles a body with a comma-separated
UTF-16 code-unit list and executes that body with one Function constructor.

No commas appear in the emitted JSFuck: Array.prototype.join() inserts them
at runtime. The caller compares complete output lengths before selecting it.
"""
from __future__ import annotations

from collections.abc import Callable

from .numeric_batch import _utf16_units

# Non-digit words are cheap as whole primitive tokens. The benchmark found
# "false" generally best on long Unicode, with "NaN" a useful fallback.
# Keep the default search bounded; exhaustive delimiter variants live in
# benchmarks/numeric_separator_study.py.
DELIMITERS = ("false", "NaN")


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
