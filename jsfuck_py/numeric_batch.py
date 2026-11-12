"""Batch character-code reconstruction using JSFuck-only JavaScript syntax.

A direct multi-argument invocation would need commas, which are outside the
JSFuck alphabet. A two-element array and Array.prototype.reduce instead call
the unbound Function.prototype.apply with (thisArg, argumentsArray).

For example (ordinary JavaScript, NOT the emitted syntax):
    [[], ["65", "66"]].reduce(String.fromCharCode.apply.bind(String.fromCharCode))
The numeric strings are implicitly converted by fromCharCode/fromCodePoint.

The result is a string and does not evaluate the supplied JavaScript source.
"""
from __future__ import annotations

from collections.abc import Callable


def _utf16_units(source: str) -> tuple[int, ...]:
    encoded = source.encode("utf-16-be", errors="surrogatepass")
    return tuple(
        int.from_bytes(encoded[index:index + 2], "big")
        for index in range(0, len(encoded), 2)
    )


def _code_points(source: str) -> tuple[int, ...]:
    return tuple(ord(character) for character in source)


def numeric_batch_candidates(
    source: str, encode_text: Callable[[str], str]
) -> dict[str, str]:
    """Create two pure-JSFuck string-returning alternatives.

    All JavaScript property names are compiled through the existing Python
    character encoder. UTF-16 units preserve even unpaired surrogates.
    """
    if not source:
        return {}

    string_constructor = "([]+[])[" + encode_text("constructor") + "]"
    apply_key = "[" + encode_text("apply") + "]"
    bind_key = "[" + encode_text("bind") + "]"
    concat_key = "[" + encode_text("concat") + "]"
    reduce_key = "[" + encode_text("reduce") + "]"
    split_key = "[" + encode_text("split") + "]"

    # Choose the cheapest delimiter absent from decimal character-code data.
    separators = ("f", "a", "t", "e")
    sep = min(separators, key=lambda ch: len(encode_text(ch)))

    output: dict[str, str] = {}
    from_char_code = string_constructor + "[" + encode_text("fromCharCode") + "]"

    # Uppercase 'P' is not part of the current direct JSFuck mapping.
    # Bootstrap it from char code 80 when considering fromCodePoint.
    p_expression = from_char_code + "(" + encode_text("80") + ")"
    from_code_point_key = "+".join(
        "(" + p_expression + ")" if char == "P" else encode_text(char)
        for char in "fromCodePoint"
    )
    methods = (
        ("fromCharCode", _utf16_units(source), from_char_code),
        ("fromCodePoint", _code_points(source),
         string_constructor + "[" + from_code_point_key + "]"),
    )

    for method, codes, target in methods:
        if len(codes) == 1:
            # Single argument: no apply, split or array construction.
            output[method] = target + "(" + encode_text(str(codes[0])) + ")"
            continue

        payload = encode_text(sep.join(map(str, codes)))
        args = "(" + payload + ")" + split_key + "(" + encode_text(sep) + ")"
        array = "[[]]" + concat_key + "([" + args + "])"
        callback = target + apply_key + bind_key + "(" + target + ")"
        output[method] = array + reduce_key + "(" + callback + ")"

    return output
