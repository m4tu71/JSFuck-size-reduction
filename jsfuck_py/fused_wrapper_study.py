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


def simple_literal_spans(source: str) -> tuple[tuple[int, int, str], ...]:
    """Identify unescaped single/double-quoted literals in a limited JS subset.

    Single quotes are normalized to double quotes, so they must not contain
    literal double quotes. Backslash escapes, comments, regular expressions,
    and template literals require an ECMAScript lexer and are rejected.
    """
    if len(source) > MAX_SOURCE_LENGTH:
        return ()

    spans: list[tuple[int, int, str]] = []
    index = 0
    while index < len(source):
        char = source[index]
        if char in ("'", '"'):
            quote = char
            start = index + 1
            index = start
            while index < len(source) and source[index] != quote:
                current = source[index]
                if current in "\\\r\n" or 0xD800 <= ord(current) <= 0xDFFF:
                    return ()
                if quote == "'" and current == '"':
                    return ()
                index += 1
            if index == len(source):
                return ()
            spans.append((start, index, quote))
        elif char in "`/\\" or ord(char) > 127:
            return ()
        index += 1
    return tuple(spans)


def simple_double_quote_spans(source: str) -> tuple[tuple[int, int], ...]:
    """Legacy helper exposing spans of double-quoted-only safe input."""
    spans = simple_literal_spans(source)
    if any(quote != '"' for _, _, quote in spans):
        return ()
    return tuple((start, end) for start, end, _ in spans)


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
    """Convert Unicode in safe literals, normalizing simple single quotes."""
    spans = simple_literal_spans(source)
    if not spans:
        return None

    output: list[str] = []
    position = 0
    changed = False
    for start, end, quote in spans:
        # Opening quote is at start-1; close quote is at end.
        output.append(source[position:start - 1])
        output.append('"')
        content = source[start:end]
        changed |= any(ord(char) > 127 for char in content)
        output.append("".join(
            char if ord(char) <= 127 else _unicode_escaped(char)
            for char in content
        ))
        output.append('"')
        position = end + 1
    output.append(source[position:])
    return "".join(output) if changed else None


def direct_unicode_function_candidate(
    source: str, *, search_spellings: bool = False
) -> str | None:
    """Generate one Function call for a conservatively rewritten JS source."""
    if search_spellings:
        from .escape_spelling_search import best_spelled_source
        transformed = best_spelled_source(source)
    else:
        transformed = unicode_literal_source(source)
    if transformed is None or any(char not in _mapping() for char in transformed):
        return None
    constructor = "[][" + _tokens("at", True) + "][" + _tokens("constructor", True) + "]"
    return constructor + "(" + _tokens(transformed, True) + ")()"


def wrapped_expression(source: str) -> str:
    """Existing wrapper baseline for comparison."""
    from .encoder import encode
    return encode(source, wrap=True)
