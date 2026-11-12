"""Controlled comparison of whole-string and segmented generator strategies.

The complete output, including parentheses between parts, is measured.
This is a research diagnostic, not a production encoder rewrite.
"""
from __future__ import annotations

from jsfuck_py.encoder import encode

CASES = (
    ("abcあいうdef", ("abc", "あいう", "def")),
    ("let s='漢字';", ("let s='", "漢字", "';")),
    ("prefix😀😃suffix", ("prefix", "😀😃", "suffix")),
    ("abc漢字def漢字xyz", ("abc", "漢字", "def", "漢字", "xyz")),
    ("abcabcabcabc", ("abc", "abc", "abc", "abc")),
)


def main() -> None:
    print(f"{'input':28} {'whole':>7} {'segmented':>10} {'delta':>8}")
    for source, parts in CASES:
        assert "".join(parts) == source
        # Each fully parenthesized part must evaluate to a string.
        segmented = "+".join("(" + encode(part) + ")" for part in parts)
        whole = encode(source)
        print(f"{source[:26]!r:28} {len(whole):7} "
              f"{len(segmented):10} {len(segmented)-len(whole):8}")
    print("Positive delta means the segmented candidate is longer.")


if __name__ == "__main__":
    main()
