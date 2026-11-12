"""Ablation: opt-in shared-substring helper versus the existing encoder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsfuck_py import __version__
from jsfuck_py.encoder import encode

DEFAULT_CASES = Path(__file__).with_name("shared_substring_cases.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args()
    values = json.loads(args.cases.read_text(encoding="utf-8"))
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        parser.error("Expected a JSON array of strings")
    total_old = total_new = 0
    print(f"Encoder: {__version__}, shared mode comparison")
    for source in values:
        old = len(encode(source))
        new = len(encode(source, share_substrings=True))
        total_old += old
        total_new += new
        print(f"{source[:36]!r:40} {old:>8} {new:>8} {old-new:>8}")
        assert new <= old
    saved = total_old - total_new
    print(f"Total {total_old} -> {total_new}; saved {saved} "
          f"({100*saved/total_old if total_old else 0:.2f}%)")


if __name__ == "__main__":
    main()
