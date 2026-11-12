"""Experimental shared-substring encoding using an isolated JS function.

The emitted JSFuck expression constructs a function that accepts one string
argument. All repeated occurrences of the selected substring refer to that
parameter, so the expensive substring expression is emitted once.

The user's JavaScript source is treated solely as data. Its bindings, scopes,
and syntax are never rewritten. Names used inside the generated helper are
local to that helper.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
import json
import re

# Bounded deterministic search: avoids quadratic enumeration on large inputs.
LENGTHS = (16, 32, 64, 128, 256, 512, 1024)
MAX_SAMPLES = 600
MAX_CANDIDATES = 6
VARIABLES = ("a", "t", "f", "l", "n", "r", "e", "i", "o",
             "s", "u", "c", "b", "d", "x", "y", "z")


def repeated_candidates(source: str) -> list[str]:
    """Rank repeated nonoverlapping substrings by rough potential savings."""
    ranked: dict[str, int] = {}
    for length in LENGTHS:
        if length * 2 > len(source):
            continue
        step = max(1, (len(source) - length) // MAX_SAMPLES)
        sampled = Counter(
            source[start:start + length]
            for start in range(0, len(source) - length + 1, step)
        )
        for word, samples in sampled.items():
            if samples < 2 or len(set(word)) <= 1:
                continue
            occurrences = source.count(word)
            if occurrences >= 2:
                ranked[word] = (occurrences - 1) * len(word)
    return sorted(ranked, key=lambda word: (-ranked[word], -len(word), word))[:MAX_CANDIDATES]


def helper_names(source: str, *, avoid_source_identifiers: bool) -> tuple[str, ...]:
    """Try short JS identifiers, optionally excluding source identifiers."""
    if not avoid_source_identifiers:
        return VARIABLES
    identifiers = set(re.findall(r"[$A-Za-z_][$A-Za-z_0-9]*", source))
    return tuple(name for name in VARIABLES if name not in identifiers)


def shared_string_candidates(
    source: str,
    encode_plain: Callable[[str], str],
    function_constructor: str,
    *,
    avoid_source_identifiers: bool = True,
) -> list[tuple[str, str, str]]:
    """Return (JSFuck expression, shared substring, helper variable) options.

    Compare total size of compiled helper body, function constructor and the
    one-time argument encoding; no optimistic size estimate is used for final
    selection. Embedded source fragments are JSON-quoted JS string literals.
    """
    names = helper_names(source, avoid_source_identifiers=avoid_source_identifiers)
    if not names:
        return []

    options: list[tuple[str, str, str]] = []
    for word in repeated_candidates(source):
        fragments = source.split(word)
        if len(fragments) < 3:
            continue

        # Encoding the repeated value only once is the potential win.
        encoded_value = encode_plain(word)
        for name in names:
            pieces: list[str] = []
            for i, fragment in enumerate(fragments):
                if fragment:
                    pieces.append(json.dumps(fragment, ensure_ascii=True))
                if i < len(fragments) - 1:
                    pieces.append(name)
            body = f"return function({name}){{return " + "+".join(pieces) + "}"
            encoded_body = encode_plain(body)
            output = (function_constructor + "(" + encoded_body
                      + ")()(" + encoded_value + ")")
            options.append((output, word, name))

    options.sort(key=lambda candidate: (len(candidate[0]), candidate[2]))
    return options[:1]
