# JSFuck size-reduction research (2026-11-12)

## Baseline and controls

The reference is official `aemkei/jsfuck` 0.5.0 at commit
`6f8fdf31f18a4f2df3bf2576f313b3abeca4c89d`.
Compare both `wrap=False` (string) and `wrap=True` (execution);
test semantic equivalence with Node.js, not only output length.
Never claim the global optimum from a finite benchmark.

## Validated techniques

1. **Shorter native text character extraction.** Examine the native text of
   `[]["at"]` and other Array methods with several cheap string prefixes.
   Changing the offset can reduce the emitted index expression.
   Only strictly shorter recipes replace the baseline.
2. **Whole native-string tokens.** In the dynamic-programming text encoder,
   represent the complete string `function at() { [native code] }` with the
   JSFuck equivalent of `([]+[]["at"])` instead of individual characters.
   Other Array methods are considered similarly.
3. **Iterator-character candidates.** Probe the source string
   `[object Array Iterator]` from `[]["entries"]()`. In the tested
   benchmark this did **not** beat the current 185-character `A` recipe
   or the 70-character `I` recipe; retain only candidates that win.

### Pinned reference measurements (Node.js 22; string mode)

| Input | Reference | Experimental | Reduction |
|---|---:|---:|---:|
| `native` | 1022 | 162 | 84.15% |
| `function at() { [native code] }` | 2491 | 39 | 98.43% |
| `function map() { [native code] }` | 3775 | 1323 | 64.95% |
| `function add(a,b){return a+b}` | 1602 | 1442 | 9.99% |
| `A` | 185 | 185 | 0% |
| `I` | 70 | 70 | 0% |
| `hello` | 1034 | 1034 | 0% |

These are **input-specific**, not representative overall reduction rates.
Native function text can change with the JavaScript engine or overridden
built-ins. CI covers the declared Node.js version only.

## Proposed next experiments (not implemented)

### P1: Substring expressions

Instead of matching only an *entire* native-function string, generate
substring candidates with `slice`/`substring` and compare:

```
length(native_expression) + length(method_key) + length(start_index)
+ length(end_index) + invocation_overhead
```

The slice method and indices have substantial JSFuck costs. Enumerate
positions and compare total cost before adding candidates to the DP table.
Extracting a 5-character substring is not necessarily cheaper than 5
single-character mappings.

### P1: Escape-loader selection

The current baseline chooses its recovery pipeline based on the number
of unmapped characters. Model the final emitted costs of:

- individual escaped characters;
- a whole-source escape payload plus split/join restoration;
- alternative String.fromCharCode or string-method strategies;

and select the shortest *semantically equivalent* branch. Correct handling
of quotes, backslashes, UTF-16 surrogate pairs and runtime semantics is
mandatory. Do not add a character to the direct mapping without checking
the effect on the unmapped-character threshold.

### P2: More source expressions

Extend the candidate grammar beyond Array-native text: constructor
names, iterator objects, number formatting, and primitive coercion.
For every candidate track its inferred JS value type and the exact string
coercion context. A cheap numeric expression must not silently replace a
string-expression in a concatenation.

### P2: Grammar-aware search

Represent `number`, `string`, `function`, and `array` as typed nodes,
including operator precedence, parenthesization, and context-specific
coercions. Use bounded cost-first search and memoization. The shortest
standalone character expression is not necessarily the cheapest expression
inside a larger constructor or string pipeline.

## External leads

- https://github.com/aemkei/jsfuck/issues/129 (capital A via iterator;
  older proposal, not an improvement over the pinned current mapping)
- https://github.com/aemkei/jsfuck/issues/146 (capital P via
  Array.fromAsync/Promise; requires runtime compatibility checks)
- https://github.com/aemkei/jsfuck (reference sources and documentation)

## Additional experiments: 0.1.0.dev1

**Cost-based escape path:** Generate the direct-escape and split/join
reconstruction alternatives and compare their complete JSFuck output lengths.
This supersedes the fixed threshold of two unmapped characters. Both branches
are checked with Node.js round-trip tests including Unicode and literal slashes.

**Trailing primitive conversion:** When a string prefix ends in `false`,
`true`, `undefined`, `NaN` or `Infinity`, omit the unnecessary
`+[]` coercion and let JavaScript's string addition do it. Protect unary
plus expressions with parentheses to avoid `++` parse errors.

**Reference mapping gaps:** The Python port previously omitted `E`, `R`,
`:` and `?` because its regex-constructor expansion did not round-trip.
These are now stored as pinned upstream 0.5.0 fallback recipes and validated
by the per-character semantics tests. As a result, the current measured
`??` case matches the official length (2597), rather than regressing to 4175.

Selected measured examples (string mode, official -> experimental):

| Input | Official | Python |
|---|---:|---:|
| `falsefalse` | 17 | 12 |
| `truefalse` | 18 | 13 |
| `xfalse` | 941 | 936 |
| `xNaN` | 944 | 941 |
| `??` | 2597 | 2597 |
| `E:R` | 3908 | 3908 |

**Further work:** Fixing the reference parity removes misleading deficits,
but these examples are not representative corpus-wide savings. A larger,
versioned benchmark corpus is the next priority before claiming typical
performance improvements.

## Native substring suffix experiments (0.1.0.dev2)

The Python optimizer now searches suffixes of the JavaScript engine's native
Array-method source strings. Unlike two-argument `slice(start, end)`, which
requires a comma unavailable in JSFuck, the one-argument
`String(nativeMethod).slice(start)` form can be compiled using only
`[]()!+`. Candidate expressions are evaluated by **total emitted size**,
including encoding `slice`, the method name and the offset. Candidates that
cannot beat individual-character concatenation are discarded before DP.

Pinned JSFuck 0.5.0 baseline, Node.js 22, string-return mode:

| Input | Official | Experimental | Savings |
|---|---:|---:|---:|
| `at() { [native code] }` | 2209 | 224 | 89.86% |
| `() { [native code] }` | 2178 | 210 | 90.36% |
| `native code] }` | 1707 | 239 | 86.00% |
| `map() { [native code] }` | 3493 | 1525 | 56.34% |

### Controlled ablation

`python -m benchmarks.ablation --cases benchmarks/native_suffix_cases.json`
compares the same Python implementation with only suffix candidates disabled.
On the seven targeted inputs: **7596 → 4389 characters**, 3207 fewer
(42.22%). The new optimization alone saved **0 characters** over the
20 JavaScript source snippets in `benchmarks/javascript_samples.json`.

### Non-random JavaScript source sample

The 20 manually selected JavaScript snippets total **62163 characters** in
pinned official JSFuck and **57638 characters** in the Python encoder:
4525 fewer (7.28%). Of 20 inputs, 15 are shorter and 5 are tied. These
gains are **cumulative across previous and current optimizations**, not
attributable to the new suffix search. This small, intentionally selected
sample does not establish a population-wide average.

### Interpretation and next steps

- Arbitrary `slice(start, end)` is unavailable syntactically as written
  because JSFuck cannot contain a literal comma. A two-argument call would
  need a separately constructed invocation mechanism, whose cost must be
  justified.
- Consider adding a typed, cost-first grammar for numeric indices,
  property access and coercion contexts. This has a plausible route to
  **general-code** savings not confined to native-method text.
- Test engine portability beyond Node.js 22 before treating native source
  representations as universal; source formatting can vary by engine.
- Profile encoder time on longer inputs; each extra token family increases
  dynamic-programming candidate checks.

## Typed primitive concatenation (0.1.0.dev3)

A new cost-based dynamic program distinguishes two states: a prefix that
JavaScript guarantees is a string, and a standalone primitive/array prefix.
The latter may transition to a string only when the next operand guarantees
string concatenation. Once a string exists, an embedded boolean, undefined
or number need not be explicitly converted by `+[]`.

The printer encloses arithmetic recipes containing binary `+` when
concatenating with strings. The generated `!+` literal-input family has a
known interaction with the escape pipeline; it is conservatively encoded
through the older checked pathway. This is not proof that the grammar is
complete or globally shortest.

### Marginal measurements

Controlled ablation disables only the typed DP, holding all existing
optimizations and the pinned JSFuck 0.5.0 reference constant:

| Corpus | Previous Python | With typed DP | Characters saved |
|---|---:|---:|---:|
| 20 JavaScript examples | 57,638 | 57,633 | 5 (0.01%) |
| 19 primitive-heavy examples | 15,542 | 15,468 | 74 (0.48%) |

Selected official-reference string-mode results:

| Input | JSFuck 0.5.0 | New Python |
|---|---:|---:|
| `false` | 8 | 6 |
| `true` | 9 | 7 |
| `undefined` | 11 | 9 |
| `NaN` | 11 | 9 |
| `Infinity` | 65 | 63 |
| `falsefalse` | 17 | 10 |
| `if(true){alert(1)}` | 668 | 502 |

These are small, hand-selected corpora; percentages are not population-wide
savings. The next research direction is a proper typed expression AST and
precedence-aware printer, eliminating the need for a special fallback while
allowing cheap numeric and primitive operations in more contexts.

Run:

```sh
python -m benchmarks.typed_ablation
python -m benchmarks.typed_ablation --cases benchmarks/typed_primitive_cases.json
```
