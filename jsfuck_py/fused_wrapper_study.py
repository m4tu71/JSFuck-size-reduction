"""Research whether direct Unicode source escaping can eliminate a Function layer.

The existing wrap=True pipeline first reconstructs source text through a
Function-based string decoder, then passes the result to another Function.
This study directly compiles a JS source string containing unicode escapes.

It is *not* a general program transformation: only one simple double-quoted
console.log call is supported. The candidate is never used by the encoder.
"""
from __future__ import annotations

import re

from .encoder import _mapping, _tokens


_PATTERN = re.compile(r'^(console\.log\()("[^"\\]*")(\);?)$', re.DOTALL)


def direct_unicode_function_candidate(source: str) -> str | None:
    """Return a tested candidate for a simple Unicode string-literal call."""
    match = _PATTERN.fullmatch(source)
    if not match:
        return None
    prefix, literal, suffix = match.groups()
    if not any(ord(char) > 127 for char in literal):
        return None

    def to_js_escape(char: str) -> str:
        if ord(char) <= 127:
            return char
        raw = char.encode("utf-16-be", errors="surrogatepass")
        options = [
            "".join("\\u" + raw[i:i + 2].hex()
                    for i in range(0, len(raw), 2))
        ]
        # Within a JavaScript string literal, both \xHH and \u{H...}
        # represent the same character as UTF-16 \uHHHH escapes.
        if ord(char) <= 0xff:
            options.append("\\x" + format(ord(char), "02x"))
        if ord(char) > 0xff:
            options.append("\\u{" + format(ord(char), "x") + "}")
        return min(options, key=lambda option: len(_tokens(option, True)))

    transformed = prefix + "".join(to_js_escape(ch) for ch in literal) + suffix
    if any(char not in _mapping() for char in transformed):
        return None

    constructor = "[][" + _tokens("at", True) + "][" + _tokens("constructor", True) + "]"
    return constructor + "(" + _tokens(transformed, True) + ")()"


def wrapped_expression(source: str) -> str:
    """The production baseline for wrap=True."""
    from .encoder import encode
    return encode(source, wrap=True)
