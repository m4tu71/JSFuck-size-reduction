"""Measure bounded interval generator search against the merged encoder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsfuck_py.encoder import _mapping, _tokens, encode
from jsfuck_py.interval_search import best_interval_candidate, batch_windows
from jsfuck_py.numeric_batch import numeric_batch_candidates


DEFAULT_CASES = Path(__file__).with_name("interval_batch_cases.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    options = parser.parse_args()
    values = json.loads(options.cases.read_text(encoding="utf-8"))
    before = after = 0
    print(f"{'source':30} {'original':>9} {'searched':>9} {'delta':>9} {'window':>15}")
    for value in values:
        normal = encode(value)
        searched, interval = best_interval_candidate(
            value,
            _mapping(),
            encode,
            lambda segment: numeric_batch_candidates(segment, lambda s: _tokens(s, True)),
        )
        before += len(normal)
        after += len(searched)
        print(f"{value[:28]!r:30} {len(normal):9} {len(searched):9} "
              f"{len(normal)-len(searched):9} {str(interval):>15}")
        assert len(searched) <= len(normal)
    print(f"Total {before} -> {after}; saved {before-after} "
          f"({100*(before-after)/before if before else 0:.2f}%)")


if __name__ == "__main__":
    main()
