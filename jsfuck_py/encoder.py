"""Experimental pure-Python JSFuck encoder, based on JSFuck 0.5.0.

This is an optimization experiment, not a promise of globally shortest output.
"""
from __future__ import annotations

import base64
import json
import re
from functools import lru_cache
from pathlib import Path

from .at_optimization import native_string_tokens, optimize_native_at

_ALLOWED = frozenset("[]()!+")
_SIMPLE = {
    "false": "![]",
    "true": "!![]",
    "undefined": "[][[]]",
    "NaN": "+[![]]",
    "Infinity": "+(+!+[]+(!+[]+[])[!+[]+!+[]+!+[]]+[+!+[]]+[+[]]+[+[]]+[+[]])",
}
_CONSTRUCTORS = {
    "Array": "[]",
    "Number": "(+[])",
    "String": "([]+[])",
    "Boolean": "(![])",
    "Function": '[]["at"]',
    "RegExp": 'Function("return/"+false+"/")()',
}
_GLOBAL = 'Function("return this")()'
_SOURCE = Path(__file__).with_name("mapping.json")


def _number(n: int) -> str:
    if n == 0:
        return "+[]"
    return "+!+[]" if n == 1 else "!+[]" + "+!+[]" * (n - 1)


def _digit(n: int) -> str:
    return "[" + _number(n) + "]"


def _expand_mapping() -> dict[str, str]:
    raw = json.loads(_SOURCE.read_text(encoding="utf-8"))
    mapping = {str(n): _digit(n) for n in range(10)}
    mapping.update({k: v for k, v in raw.items() if v is not None})

    for code in range(32, 127):
        ch = chr(code)
        if ch not in mapping:
            continue
        value = mapping[ch]
        for key, constructor in _CONSTRUCTORS.items():
            value = re.sub(r"\b" + key + r"\b",
                           lambda m, c=constructor: c + '["constructor"]',
                           value, flags=re.IGNORECASE)
        for key, simple in _SIMPLE.items():
            value = re.sub(re.escape(key), lambda m, s=simple: s,
                           value, flags=re.IGNORECASE)

        def expand_number(match: re.Match[str]) -> str:
            digits = match.group()
            head = _number(int(digits[0]))
            return head + "".join("+" + _digit(int(d)) for d in digits[1:])

        value = re.sub(r"\d\d+", expand_number, value)
        value = re.sub(r"\((\d)\)", lambda m: _digit(int(m[1])), value)
        value = re.sub(r"\[(\d)\]", lambda m: _digit(int(m[1])), value)
        value = value.replace("GLOBAL", _GLOBAL).replace('+""', "+[]")
        value = value.replace('""', "[]+[]")
        mapping[ch] = value

    # Quoted strings become concatenations of references to mapped chars.
    for key, value in mapping.items():
        mapping[key] = re.sub(r'"([^"]+)"',
                              lambda m: "+".join(m[1]),
                              value)
    for _ in range(256):
        missing = {k for k, v in mapping.items() if set(v) - _ALLOWED}
        if not missing:
            break
        for key in missing:
            value = mapping[key]
            mapping[key] = "".join(mapping[c] if c in mapping and c not in _ALLOWED
                                   else c for c in value)
    else:
        raise ValueError("Mapping expansion did not converge")
    # Preserve the pinned upstream recipe for backslash. Rebuilding it
    # through RegExp can produce runtime-dependent or oversized expressions.
    mapping["\\"] = base64.b64decode(
        _SOURCE.with_name("backslash_jsfuck_050.b64").read_text(
            encoding="ascii").strip()
    ).decode("ascii")
    for unstable in ("E", "R", ":", "?"):
        mapping.pop(unstable, None)
    mapping, _ = optimize_native_at(mapping, _number)
    assert all(set(v) <= _ALLOWED for v in mapping.values())
    return mapping


@lru_cache(maxsize=1)
def _mapping() -> dict[str, str]:
    return _expand_mapping()


@lru_cache(maxsize=1)
def _native_tokens() -> dict[str, str]:
    return native_string_tokens(_mapping())


def _escape(ch: str) -> str:
    # Escape UTF-16 code units, matching JavaScript String.charCodeAt.
    units = ch.encode("utf-16-be", errors="surrogatepass")
    return "".join(
        ("\\" + format(n, "o") if n < 256 else "\\u" + format(n, "04x"))
        for n in (int.from_bytes(units[i:i + 2], "big")
                  for i in range(0, len(units), 2))
    )


@lru_cache(maxsize=4096)
def _tokens(text: str, optimize: bool) -> str:
    mapping = _mapping()
    if not text:
        return ""
    if not optimize:
        parts = []
        pattern = re.compile("|".join(map(re.escape, _SIMPLE)) + "|.", re.DOTALL)
        for token in pattern.findall(text):
            parts.append("(" + _SIMPLE[token] + "+[])" if token in _SIMPLE
                         else mapping[token])
        return "+".join(parts) + ("+[]" if len(text) == 1 and text.isdigit() else "")

    # Dynamic programming over the actual number of emitted characters.
    # Every segment denotes a string when concatenated with another segment.
    size = len(text)
    best: list[tuple[int, str] | None] = [None] * (size + 1)
    best[size] = (0, "")
    for start in range(size - 1, -1, -1):
        choices = [(start + 1, mapping[text[start]])]
        choices.extend(
            (start + len(word), "(" + expr + "+[])")
            for word, expr in _SIMPLE.items()
            if text.startswith(word, start)
        )
        choices.extend(
            (start + len(literal), expression)
            for literal, expression in _native_tokens().items()
            if text.startswith(literal, start)
        )
        for end, expression in choices:
            assert best[end] is not None
            tail_length, tail = best[end]
            separator = "+" if end != size else ""
            candidate = (len(expression) + len(separator) + tail_length,
                         expression + separator + tail)
            if best[start] is None or candidate[0] < best[start][0]:
                best[start] = candidate
    assert best[0] is not None
    result = best[0][1]
    candidates = [result + "+[]" if len(text) == 1 and text.isdigit() else result]
    if text[0] in "0123456789":
        # A leading numeric primitive can be coerced into a string by the
        # next string-valued operand. Otherwise force string conversion.
        numeric = _number(int(text[0]))
        if len(text) > 1:
            assert best[1] is not None
            candidates.append(numeric + "+" + best[1][1])
        else:
            candidates.append(numeric + "+[]")

    # Once the prefix is already a string, a trailing JS primitive is
    # stringified automatically by '+'. This avoids '(primitive+[])'.
    # Encode the prefix independently to preserve type correctness.
    for literal, primitive in _SIMPLE.items():
        if text.endswith(literal) and len(text) > len(literal):
            prefix = _tokens(text[:-len(literal)], optimize)
            candidates.append(prefix + "+" + primitive)

    return min(candidates, key=len)


def encode(text: str, *, optimize: bool = True, wrap: bool = False,
           parent_scope: bool = False) -> str:
    """Encode JavaScript source as a JSFuck expression.

    With wrap=False, evaluating the expression yields the original source
    as a string. With wrap=True, it executes that source (like JSFuck.com).
    """
    if not text:
        return ""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    mapping = _mapping()
    unmapped_count = sum(ch not in mapping for ch in text)
    if not unmapped_count:
        output = _tokens(text, optimize)
    else:
        # Build both possible escape decoders, measuring the *complete*
        # output including the Function constructor and split/join overhead.
        # The upstream threshold is a heuristic, not a size optimum.
        function = ("[][" + _tokens("at", optimize) + "]["
                    + _tokens("constructor", optimize) + "]")
        prefix = function + "(" + _tokens('return"', optimize) + "+"
        suffix = "+" + _tokens('"', optimize) + ")()"

        direct_payload = "".join(
            _escape(ch) if ch in '"\\' or ch not in mapping else ch
            for ch in text
        )
        direct = prefix + _tokens(direct_payload, optimize) + suffix

        # The placeholder 't' stands for every escape slash. Literal 't'
        # must also be escaped; the conservative alphabet is intentional.
        safe = "0123456789.adefilnrsuN"
        split_payload = "".join(
            ch if ch in safe else _escape(ch).replace("\\", "t")
            for ch in text
        )
        split = (
            "(" + _tokens(split_payload, optimize) + ")["
            + _tokens("split", optimize) + "]("
            + _tokens("t", optimize) + ")["
            + _tokens("join", optimize) + "]("
            + _tokens("\\", optimize) + ")"
        )
        reconstructed = prefix + split + suffix
        output = min((direct, reconstructed), key=len)

    if wrap:
        function = "[][" + _tokens("at", optimize) + "][" + _tokens("constructor", optimize) + "]"
        if parent_scope:
            output = (function + "(" + _tokens("return eval", optimize)
                      + ")()(" + output + ")")
        else:
            output = function + "(" + output + ")()"
    if not set(output) <= _ALLOWED:
        raise AssertionError("Output contains a non-JSFuck symbol")
    return output
