"""Compare current encoder with the native-suffix optimization disabled.

This isolates the marginal benefit of this one candidate family rather than
incorrectly attributing all official-reference savings to the latest change.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

from jsfuck_py import __version__
from jsfuck_py import encoder
from jsfuck_py.at_optimization import native_string_tokens

DEFAULT_CORPUS = Path(__file__).with_name("javascript_samples.json")


def compare(cases: list[str], *, wrap: bool = False) -> list[dict[str, object]]:
    """Return before/after counts with the same mapping and wrapping mode."""
    encoder._tokens.cache_clear()
    optimized = [len(encoder.encode(case, wrap=wrap)) for case in cases]

    encoder._tokens.cache_clear()
    try:
        with patch.object(
            encoder,
            "_native_tokens",
            return_value=native_string_tokens(encoder._mapping()),
        ):
            original = [len(encoder.encode(case, wrap=wrap)) for case in cases]
    finally:
        encoder._tokens.cache_clear()

    return [
        {
            "input": case,
            "without_suffix": old,
            "with_suffix": new,
            "characters_saved": old - new,
        }
        for case, old, new in zip(cases, original, optimized, strict=True)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--wrap", action="store_true")
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or any(not isinstance(s, str) for s in cases):
        parser.error("Expected a JSON array of strings")

    rows = compare(cases, wrap=args.wrap)
    saved = sum(int(row["characters_saved"]) for row in rows)
    before = sum(int(row["without_suffix"]) for row in rows)
    print(f"Encoder: {__version__}; wrap={args.wrap}")
    for row in rows:
        print(f"{row['input'][:35]!r:38} {row['without_suffix']:>8} "
              f"{row['with_suffix']:>8} {row['characters_saved']:>8}")
    percent = 100 * saved / before if before else 0
    print(f"Total: {before} -> {before - saved}; saved={saved} ({percent:.2f}%)")


if __name__ == "__main__":
    main()
