# Dynamic Function-compiled UTF-16 batches (dev11)

## Motivation

The existing numeric batch reconstruction builds an array of decimal
character-code strings and invokes String.fromCharCode through a
`reduce` callback based on `apply.bind`. This avoids literal commas in
JSFuck output, but it incurs large fixed costs for property access and
array/callback construction.

An initial separator search tried 14 one- and multi-character delimiters,
including `false` and `NaN`. This made the existing numeric batch
generator shorter on selected examples, but **did not improve the final
encoder output** because other reconstruction methods were still cheaper.

## New generator

Instead of constructing a JSFuck-level `apply.bind` callback, build a
JavaScript source string that represents a single call to
`String.fromCharCode` and execute that source through `Function`.

Ordinary JavaScript illustration (not literal JSFuck output):

```js
const parts = "28450false23383".split("false");
const source = "return ([]+[]).constructor.fromCharCode(" +
               parts.join() + ")";
const text = ([]["at"]["constructor"])(source)();
// text === "漢字"
```

Key properties:

- `join()` inserts commas by default, so the emitted JSFuck expression
  still contains only `[]()!+`.
- The source body returns an original JavaScript **string**, not the
  execution result of user-provided JavaScript. Therefore
  `wrap=False` and `wrap=True` preserve their separate semantics.
- Code units come from UTF-16 encoding with surrogate preservation.
  `String.fromCharCode` reconstructs both BMP and supplementary-plane
  Unicode (the latter via high/low surrogate pairs).
- The String constructor is reached from an empty-string primitive,
  avoiding reliance on the global `String` binding.
- Only the **complete** emitted expression length determines selection.
  There is no direct replacement of arbitrary JSFuck substrings.
- The search is bounded to input length 64–1024 and at least 32
  unmapped characters, and tries the `false` and `NaN` delimiters.
  Other delimiters remain available for separate research.

## Measured results

The controlled ablation uses the same encoder with only the new dynamic
candidate disabled. Node.js tests verify that the emitted `[]()!+`
expressions reconstruct the original strings, including emoji, NUL and
JavaScript source executed through `wrap=True`.

| Targeted source | Previous | With dynamic batch | Saved |
|---|---:|---:|---:|
| 64 unique CJK characters | 13,238 | 13,238 | 0 |
| 96 unique CJK characters | 17,453 | 17,453 | 0 |
| 128 unique CJK characters | 21,829 | 20,218 | 1,611 |
| 192 unique CJK characters | 31,766 | 27,028 | 4,738 |
| 48 distinct emoji | 16,566 | 16,566 | 0 |

Eight intentionally selected Unicode-rich cases:
**144,139 → 137,790**, saving **6,349 (4.40%)**.

Twenty ordinary JavaScript snippets: **57,633 → 57,633**, saving 0.

The corpus is small and deliberately targeted. It does not establish
the typical real-world savings for JavaScript source files.

### Performance caveat

This generator adds a complete JSFuck source-construction candidate for
eligible inputs. It consumes more Python encoding work even when the old
candidate wins. A controlled diagnostic on GitHub Actions for the eight targeted cases
reported **0.728s -> 0.810s** with the `_tokens` cache cleared before
each run and **0.004s -> 0.004s** with a populated token cache.
These are one-off wall-clock timings from a non-isolated CI runner,
not statistically rigorous throughput measurements. Input-dependent
encoding-time overhead remains a tradeoff to track on larger corpora.

## Code and reproduction

- `jsfuck_py/dynamic_charcode.py`: builder and bounded separators.
- `jsfuck_py/encoder.py`: cost-based candidate selection.
- `tests/test_dynamic_charcode_study.py`: source and wrap semantics.
- `benchmarks/dynamic_charcode_ablation.py`: isolated marginal savings.
- `benchmarks/numeric_separator_study.py`: research of 14 delimiter
  spellings. Its generator-only improvements cannot be credited as
  final encoder improvements.

```sh
python -m benchmarks.dynamic_charcode_ablation
python -m benchmarks.dynamic_charcode_study
python -m benchmarks.numeric_separator_study
python -m unittest discover -s tests -v
```

Further work should test additional source distributions and optimize
the fixed-cost header/argument-string construction as a typed DAG rather
than expanding already generated JSFuck output.
