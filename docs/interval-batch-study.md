# Interval and generator-cost follow-up (dev8 research)

## Motivation

The former PR #10 reported multi-character `String.prototype.repeat`
candidates with units of length 2 through 16. Inspection found a mismatch:
`has_multi_repeat()` scanned through 16, but `multi_repeat_candidates()`
only created candidates for units of length **2 through 8**.

This branch fixes the candidate-generation limit to 16 and verifies
semantics against Node.js.

### Verified incremental repeat-range results (Node.js 22)

| Input | Prior 2–8 units | Current 2–16 units | Saved |
|---|---:|---:|---:|
| `function(x)` repeated 24 | 28,361 | 2,330 | 26,031 |
| `console.log(` repeated 24 | 20,255 | 3,582 | 16,673 |
| `let value=42;` repeated 20 | 26,019 | 2,345 | 23,674 |
| `getElementById` repeated 24 | 33,281 | 7,619 | 25,662 |
| `漢字` repeated 24 (after escape expansion) | 13,669 | 6,255 | 7,414 |

Across the 11 repetition-focused samples, 172,469 → 73,015
(**99,454 fewer, 57.66%**). The 20 ordinary JavaScript snippets were
unchanged (57,633 → 57,633). These are targeted small corpora and are
not representative real-world average savings.
 A targeted ablation compares the same Python
encoder with 2–8 and 2–16 unit lengths; it does not conflate the original
one-character or previously implemented 2–8 optimizations with the
incremental improvement.

## Multiple Unicode runs

The current encoder already chooses a whole-input escape reconstruction
and examines the two longest isolated unmapped runs for numeric code
batching. This research adds a bounded **probe**, not a default encoder
feature, that considers spans covering up to five adjacent unmapped runs,
including short mapped segments between them.

The probe:
1. Detects contiguous expensive runs of at least six unmapped characters.
2. Forms 1–5-run windows up to 256 characters; evaluates at most 15.
3. Builds `fromCharCode` and `fromCodePoint` candidates for each window.
4. Fully encodes surrounding prefix and suffix, parenthesizes all parts,
   and compares the complete emitted JSFuck expression against the
   unmodified encoder.

### Controlled measurements

The nine deliberately mixed-source/Unicode cases in
`benchmarks/interval_batch_cases.json` did **not** improve:
**73,276 → 73,276 characters**. The existing whole-input or previous
isolated-run candidates won on every case.

The 20 ordinary JavaScript source snippets also showed zero improvement
from the Unicode interval probe.

**Interpretation:** Simply finding more intervals does not eliminate
the expensive method invocation/argument-array construction cost. These
negative findings apply to this bounded candidate family and corpus,
not to all possible fused-Function or shared-code-point designs.

## Future work

- Represent generator identity, setup cost and per-call cost explicitly,
  then consider *fused* generation with one invocation over multiple
  intervals instead of calling the constructor for every interval.
- Use a typed AST/grammar for safe JavaScript expression composition,
  preserving receiver binding and precedence.
- Investigate packing several numeric character codes into a denser
  representation *before* paying `split`/`reduce`/`apply`/`bind`
  costs; run cost comparisons rather than using fixed thresholds.
- Validate on longer and more representative JavaScript source files,
  and measure Python encoding time in addition to output size.

Commands:

```sh
python -m benchmarks.repeat_range_ablation
python -m benchmarks.repeat_range_ablation --cases benchmarks/javascript_samples.json
python -m benchmarks.interval_batch_ablation
python -m benchmarks.interval_batch_ablation --cases benchmarks/javascript_samples.json
```
