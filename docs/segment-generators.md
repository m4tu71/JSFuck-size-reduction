# Segment-level generator fusion research

## Scope

Four candidate families were examined for adjacent character generation:

1. A single `Function` escape decoder for contiguous unsupported
   characters, compared against multiple independently decoded substrings.
2. Batched `String.fromCharCode` and `String.fromCodePoint` for one or more
   UTF-16 or Unicode code points.
3. Multi-character `String.prototype.repeat` and existing native-function
   suffix extraction, integrated into a token dynamic program.
4. Cross-generator sharing of expensive helper expressions.

The pinned JavaScript reference is JSFuck 0.5.0. All new expression output
continues to use only `[]()!+`.

## 1. Function escape restoration

The existing `encode` already takes a *whole input* with unsupported
characters and evaluates direct escapes versus a split/join reconstruction.
It is not generating a new Function for every Unicode character.

Controlled diagnostic (`python -m benchmarks.generator_segmentation_study`):
combine separately encoded substrings with fully parenthesized `+`.
These comparisons measure **complete** output lengths.

| Input | Whole encoding | Explicitly segmented | Extra characters |
|---|---:|---:|---:|
| `abcあいうdef` | 4,492 | 4,613 | 121 |
| `let s='漢字';` | 4,887 | 11,036 | 6,149 |
| `prefix😀😃suffix` | 4,844 | 7,448 | 2,604 |
| `abc漢字def漢字xyz` | 5,207 | 11,100 | 5,893 |
| `abcabcabcabc` | 999 | 1,007 | 8 |

Thus splitting the input by hand **did not save** characters on these
examples. A genuine segment optimizer must account for `Function` setup
cost and should not independently create a decoder for every segment.
This does not rule out a less expensive fused decoder/runner.

## 2. Character-code batching

The current encoder already evaluates whole-input `fromCharCode` and
`fromCodePoint` variants, including JSFuck-compatible multi-argument
invocation, and tries up to two large contiguous runs of unmapped characters
embedded in longer input. This was measured in the previous dev5 study.

The hard problem is not just selecting a substring. If one chooses
multiple independent batch calls, the cost of `split`, `apply`, `bind`,
`reduce` and the method key is paid again. A generalized segment DP
should share a generator setup *only if* a complete candidate is proven
smaller and the generated program preserves receiver binding and order.

## 3. Multi-character repetition

This PR adds cost-filtered candidates for repeated units of 2–16 characters
into the existing `_tokens` dynamic program, using a bounded count set.
Every candidate includes the encoded repeat key, a string-returning unit and
a count argument. Only paths cheaper than the alternative DP path survive.
The 16-character cap is intentional for search cost; it is not a semantic
limit on JavaScript's repeat method.

The previous implementation handled only one-character runs. The additional
candidate family is checked with Node.js roundtrip tests, including
`wrap=True` execution semantics and ordinary JavaScript fragments.
The ablation benchmark removes only the new candidates, retaining other
optimizations.


### General JavaScript corpus

Controlled ablation on the existing 20 hand-selected ordinary JavaScript
snippets gives **57,633 → 57,633 characters**: zero incremental savings
from the new 2–16-character repeat candidates. This is consistent with
repeat being most helpful for long contiguous repeated patterns, not
ordinary short expressions.

## 4. Generator reuse

Sharing the Function constructor after already generating JSFuck was
examined in PR #9. Its helper had to encode an already expanded JSFuck
expression *again*, which was prohibitively expensive.

For example, a two-occurrence source with 1,684 output characters expanded
to 59,230 when a private helper was forced. This is a negative result for
that specific emission strategy; it does not prove generator sharing is
inherently bad.

A more plausible architecture is a typed generator DAG *before* emission,
with:
- nodes tagged by output type and whether they preserve `this` binding;
- fixed setup cost and per-use cost;
- repeat/escape/numeric-code candidates over input intervals;
- a comparison between no sharing, shared expression references and a
  fused generator (ideally one function call);
- semantic tests for evaluation order, UTF-16 units and escaped punctuation.

## Recommended next experiment

Build a common `Candidate(start, end, method, expression, type, cost)`
interface and compare one whole-input candidate against disjoint interval
candidates. Keep explicit generator setup costs separate from per-use costs,
and do not assume adjacent segments have cost-additive behavior when
JavaScript coercion or parser precedence changes.

Only after the interval DP finds a net win should actual generator sharing
be introduced. Character counts, runtime cost and compatibility should
each be reported separately.
