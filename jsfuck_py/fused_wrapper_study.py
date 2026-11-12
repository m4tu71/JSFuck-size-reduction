"""Conservative lexical fusion of Unicode source literals and JS execution.

When wrap=True, the legacy output can use one Function for Unicode-source
reconstruction and another Function for execution. For a deliberately narrow
lexical subset, encode a source with Unicode escapes *inside simple double
quoted strings* directly as a single Function body.

This is not an ECMAScript parser. Reject constructs that would require one.
The compiler is always selected only if its complete JSFuck length is shorter.
"""
from __future__ import annotations

from functools import lru_cache

from .encoder import _mapping, _tokens

MAX_SOURCE_LENGTH = 4096


def simple_double_quote_spans(source: str) -> tuple[tuple[int, int], ...]:
    """Locate plain quoted literals, rejecting ambiguous lexical contexts.

    Exclude single quotes, template literals, comments, regex literals,
    escapes, and non-ASCII text outside literals. The returned half-open
    ranges contain the literal content, excluding quote characters.
    """
    if len(source) > MAX_SOURCE_LENGTH:
        return ()

    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(source):
        char = source[index]
        if char == '"':
            start = index + 1
            index = start
            while index < len(source) and source[index] != '"':
                if source[index] in "\\\r\n" or 0xD800 <= ord(source[index]) <= 0xDFFF:
                    return ()
                index += 1
            if index == len(source):
                return ()
            spans.append((start, index))
        elif char in "'`/\\":  # Could be quote, template, regexp or comment.
            return ()
        elif ord(char) > 127:
            return ()
        index += 1
    return tuple(spans)


@lru_cache(maxsize=512)
def _unicode_escaped(char: str) -> str:
    """Pick the shortest JSFuck representation among JS literal escapes."""
    code = ord(char)
    units = char.encode("utf-16-be", errors="surrogatepass")
    alternatives = [
        "".join("\\u" + units[i:i+2].hex() for i in range(0, len(units), 2))
    ]
    if code <= 255:
        alternatives.append("\\x" + format(code, "02x"))
    else:
        alternatives.append("\\u{" + format(code, "x") + "}")
    return min(alternatives, key=lambda alt: len(_tokens(alt, True)))


def unicode_literal_source(source: str) -> str | None:
    """Convert Unicode only inside verified unescaped double-quoted strings."""
    spans = simple_double_quote_spans(source)
    if not spans:
        return None

    output: list[str] = []
    position = 0
    changed = False
    for start, end in spans:
        output.append(source[position:start])
        content = source[start:end]
        changed |= any(ord(char) > 127 for char in content)
        output.append("".join(
            char if ord(char) <= 127 else _unicode_escaped(char)
            for char in content
        ))
        position = end
    output.append(source[position:])
    return "".join(output) if changed else None


def direct_unicode_function_candidate(source: str) -> str | None:
    """Generate one Function call for a conservatively rewritten JS source."""
    transformed = unicode_literal_source(source)
    if transformed is None or any(char not in _mapping() for char in transformed):
        return None
    constructor = "[][" + _tokens("at", True) + "][" + _tokens("constructor", True) + "]"
    return constructor + "(" + _tokens(transformed, True) + ")()"


def wrapped_expression(source: str) -> str:
    """Existing wrapper baseline for comparison."""
    from .encoder import encode
    return encode(source, wrap=True)
