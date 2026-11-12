"""Explore escape spellings by measuring the complete JSFuck source body.

The per-character winner is not necessarily globally cheapest: DP token
boundaries may cross neighboring JavaScript escape sequences. This bounded
search keeps the existing per-character output as the baseline and probes
single substitutions using complete emitted JSFuck cost.

Research-only: source transformation remains delegated to the conservative
lexical scanner in fused_wrapper_study.py.
"""
from __future__ import annotations

from functools import lru_cache

from .encoder import _tokens
from .fused_wrapper_study import simple_literal_spans, unicode_literal_source

MAX_PROBES = 24


@lru_cache(maxsize=1024)
def escape_spellings(char: str) -> tuple[str, ...]:
    """Equivalent JavaScript string-literal spellings of one Unicode scalar."""
    code = ord(char)
    if code <= 127 or 0xD800 <= code <= 0xDFFF:
        return ()
    units = char.encode("utf-16-be")
    options = {
        "".join("\\u" + units[i:i + 2].hex() for i in range(0, len(units), 2)),
        "".join("\\u" + units[i:i + 2].hex().upper() for i in range(0, len(units), 2)),
        "\\u{" + format(code, "x") + "}",
        "\\u{" + format(code, "X") + "}",
    }
    if code <= 255:
        options.update({"\\x" + format(code, "02x"),
                        "\\x" + format(code, "02X")})
    # Fixed ordering ensures benchmark results do not depend on hash seeds.
    return tuple(sorted(options))


def _render(source: str, selected: dict[int, str]) -> str:
    """Render a safe source, substituting selected individual Unicode chars."""
    spans = simple_literal_spans(source)
    output: list[str] = []
    pos = 0
    for start, end, quote in spans:
        output.append(source[pos:start - 1])
        output.append('"')
        for i in range(start, end):
            char = source[i]
            output.append(selected[i] if i in selected else char)
        output.append('"')
        pos = end + 1
    output.append(source[pos:])
    return "".join(output)


def best_spelled_source(source: str, *, max_probes: int = MAX_PROBES) -> str | None:
    """Try changing one Unicode escape spelling at a time.

    Start from the already validated per-character minimum. At every
    candidate point evaluate *whole* JSFuck body token length, accepting
    only strict improvements. Limits search cost on large inputs.
    """
    baseline = unicode_literal_source(source)
    if baseline is None:
        return None

    # Build a spelling vector using the existing per-character chosen
    # escapes, then allow an alternative at one source position.
    spans = simple_literal_spans(source)
    unicode_indices = [
        i for start, end, _ in spans for i in range(start, end)
        if ord(source[i]) > 127
    ]
    if not unicode_indices:
        return None
    if len(unicode_indices) > 24:
        return baseline

    # Recover each chosen escape from the library's local cost rule,
    # without attempting to parse transformed escape text.
    from .fused_wrapper_study import _unicode_escaped
    selected = {i: _unicode_escaped(source[i]) for i in unicode_indices}
    current = baseline
    current_cost = len(_tokens(current, True))
    attempts = 0

    for i in unicode_indices:
        for spelling in escape_spellings(source[i]):
            if spelling == selected[i]:
                continue
            attempts += 1
            if attempts > max_probes:
                return current
            proposal = dict(selected)
            proposal[i] = spelling
            candidate = _render(source, proposal)
            cost = len(_tokens(candidate, True))
            if cost < current_cost:
                current = candidate
                current_cost = cost
                selected = proposal
    return current
