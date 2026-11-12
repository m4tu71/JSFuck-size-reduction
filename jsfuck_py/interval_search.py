"""Bounded interval search for expensive character-code reconstruction.

This module is intentionally a research probe rather than a default encoder
optimization. It chooses from windows of adjacent unmapped runs and evaluates
the complete prefix + batch + suffix expression cost. No generator setup is
assumed to be shared between independently evaluated batch expressions.
"""
from __future__ import annotations

from collections.abc import Callable

from .numeric_batch import expensive_runs


def batch_windows(
    source: str,
    mapping: dict[str, str],
    *,
    min_run: int = 6,
    max_runs: int = 5,
    max_span_chars: int = 256,
) -> list[tuple[int, int]]:
    """Select unique contiguous spans bounded by expensive character runs."""
    runs = sorted(expensive_runs(source, mapping, minimum=min_run))
    if not runs:
        return []
    if len(runs) > max_runs:
        runs = sorted(
            sorted(runs, key=lambda interval: interval[1] - interval[0], reverse=True)[
                :max_runs
            ]
        )
    result: set[tuple[int, int]] = set()
    for i, (start, _) in enumerate(runs):
        for j in range(i, min(len(runs), i + max_runs)):
            end = runs[j][1]
            if end - start > max_span_chars:
                break
            if start != 0 or end != len(source):
                result.add((start, end))
    return sorted(result)


def best_interval_candidate(
    source: str,
    mapping: dict[str, str],
    encode_plain: Callable[[str], str],
    make_batches: Callable[[str], dict[str, str]],
    *,
    max_windows: int = 15,
) -> tuple[str, tuple[int, int] | None]:
    """Return shortest tested expression and selected interval, if any.

    Each encoded piece is parenthesized so JavaScript addition performs
    string concatenation regardless of subexpression precedence.
    """
    baseline = encode_plain(source)
    best = baseline
    selected: tuple[int, int] | None = None

    windows = batch_windows(source, mapping)
    # Longer expensive regions first; total work is bounded.
    windows.sort(key=lambda span: (-(span[1] - span[0]), span[0]))
    for start, end in windows[:max_windows]:
        parts = (
            encode_plain(source[:start]) if start else "",
            encode_plain(source[end:]) if end < len(source) else "",
        )
        for batch in make_batches(source[start:end]).values():
            components = [parts[0], batch, parts[1]]
            candidate = "+".join("(" + part + ")" for part in components if part)
            if len(candidate) < len(best):
                best = candidate
                selected = (start, end)
    return best, selected
