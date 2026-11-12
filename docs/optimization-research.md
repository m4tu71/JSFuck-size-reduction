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

## 0.1.0.dev4: precedence-aware expression composition and repeats

Typed concatenation now builds `Expression` nodes and inspects operator depth
when appending a right operand. A top-level addition and a leading unary plus
require grouping, but nested additions inside balanced `[]` or `()` do not.
The result avoids blanket parentheses and retains the primitive-substring
length reductions measured in 0.1.0.dev3. The known literal `!+` input still
uses the conservative encoder fallback.

### Repeated-character search

The `String.prototype.repeat` method can be more economical than encoding a
costly character many times. The Python encoder generates bounded counts
(8–256), uses either numeric or digit-string count expressions, and only
offers candidate tokens when their *full* JSFuck expression is shorter.
Numeric method arguments are coerced according to JavaScript semantics.
This is an input-dependent optimization, not a universal replacement.

Controlled comparison with the same Python encoder but repeat candidates
disabled (8 deliberately repetition-heavy examples):

| Input | Previous Python | With repeat | Saving |
|---|---:|---:|---:|
| `a` repeated 64 | 1,023 | 1,023 | 0 |
| `x` repeated 32 | 29,855 | 1,988 | 27,867 |
| `0` repeated 64 | 381 | 381 | 0 |
| `ab` + 40 `z` + `cd` | 38,592 | 2,285 | 36,307 |
| `false` repeated 15 | 62 | 62 | 0 |
| JS source containing 64 `x` characters | 9,055 | 7,223 | 1,832 |
| JS source containing 128 `a` characters | 6,906 | 5,963 | 943 |
| JS source containing 64 `0` characters | 5,253 | 5,253 | 0 |

Total: **91,127 → 24,178**, saving **66,949 (73.47%)**. The selected
20 ordinary JavaScript snippets yielded **zero incremental saving** from
repeat tokens. A high percentage on the repeated-character corpus must not
be reported as a typical improvement on JavaScript source code.

Official JSFuck 0.5.0 gives the same 29,855-character baseline for 32 `x`
and 38,592 characters for the 40-`z` case; the new Python encoder returns
1,988 and 2,285 characters respectively.

### Future research

- Extend bounded repeat exploration to repeated **substrings** (e.g.
  `"abc"` repeated) and compare the actual cost of encoding the base string.
- Replace opaque mapping strings with syntax-tree nodes, with typed values
  and a formatter that can safely absorb the special `!+` fallback.
- Evaluate JSFuck's documented multi-argument invocation techniques using
  `reduce`/`bind`, comparing the heavy setup cost against two-argument
  `slice(start,end)` and other calls.
- Expand the source benchmark across projects and JavaScript engines.
  Node.js passing alone does not guarantee native-function formatting
  parity in other runtimes.

Reference: https://github.com/aemkei/jsfuck/blob/main/README.md

## 0.1.0.dev5 — batched ASCII and Unicode numbers

The pure-JSFuck output cannot contain a comma, so a literal call like
`String.fromCharCode(65,66)` is not directly expressible. The Python
optimizer constructs the equivalent call using a packed decimal string
(e.g. `"65f66"`), `.split("f")` to produce argument strings, and the
multi-argument invocation technique `[[], arguments].reduce(
String.fromCharCode.apply.bind(String.fromCharCode))`.
All property names and data are expanded to the JSFuck alphabet.

Two candidates are compared:
- `fromCharCode` uses UTF-16 code units (supplementary code points need
  high and low surrogate values), including lone surrogate preservation.
- `fromCodePoint` accepts Unicode scalar or surrogate code points directly.
  The currently unmapped uppercase `P` in the property name is synthesized
  via `String.fromCharCode(80)`, adding a one-time cost.

The encoder compares **complete emitted lengths** with its normal
escape-loader output. It can batch a whole input or a long contiguous
unmapped span; the surrounding text is encoded separately. Both methods
are validated by Node.js roundtrip tests, but other JS engines are not
yet covered.

### Marginal measurement (pinned JSFuck 0.5.0 / Node.js 22)

| Selected sample | Without batch | With batch | Saved |
|---|---:|---:|---:|
| Japanese phrase repeated 40 times (320 chars) | 50,797 | 49,689 | 1,108 (2.18%) |
| 8-emoji sequence repeated 30 times (240 code points) | 62,167 | 53,555 | 8,612 (13.85%) |
| `ΩλЖ中` repeated 40 times (160 chars) | 33,757 | 29,729 | 4,028 (11.93%) |
| `ABC` repeated 60 times (180 chars) | 143,999 | 28,769 | 115,230 (80.02%) |
| 30 snowman characters | 6,967 | 6,967 | 0 |

These are selected examples, **not a typical performance estimate**.
The 8 Unicode-oriented long samples collectively drop from 273,732 to
259,984 characters (5.02%); the improvement is concentrated in 3 inputs.
Short Unicode strings and Unicode strings embedded in the current tested
JavaScript examples remained unchanged, as the batch-call setup is costly.

### Next experiments

- Faster construction of numeric argument arrays. `reduce`, `apply`,
  `bind`, `split` and `concat` have a substantial fixed cost.
- Variable-length character-code packing, dynamic separators, radix or
  code-point delta coding, with decoding cost included.
- General DP segmentation over long mapped/unmapped stretches rather than
  only one or two contiguous expensive runs.
- Corpus-wide runtime cost in addition to output length.
- More engines: native-function text and property availability differ.

Upstream multi-argument technique:
https://github.com/aemkei/jsfuck/blob/main/README.md

## 0.1.0.dev6 — sharing repeated substrings through helper parameters

A standalone JSFuck expression cannot directly contain user-defined
identifiers, so inserting ordinary declarations into the original source
is not a sound optimization. Instead, construct an isolated helper:

```js
Function('return function(a){return "prefix"+a+"middle"+a+"suffix"}')()(shared)
```

This ordinary JavaScript is illustrative only. Both the function body and
the common `shared` value are themselves encoded to the JSFuck alphabet.

The helper returns the **original source string**, not the result of
executing it. For `wrap=True`, the existing execution wrapper runs the
reconstructed source afterward. Therefore the original program is never
rewritten to insert variables, and helper identifiers have their own scope.

The optimizer probes bounded repeated nonoverlapping substrings of lengths
16, 32, 64, 128, 256, 512, and 1024, ranks candidates heuristically,
tests short helper identifiers, and chooses based on **total emitted JSFuck
length** (including compiled helper body, function constructor and shared
argument). The default is `share_substrings=False` to retain existing
output and execution profile. `avoid_source_identifiers=True` is a
conservative choice; names inside the private helper cannot capture the
original program's variables, so collisions are not actually possible
in this architecture.

This is a bounded search, **not a globally optimal common-subexpression
elimination algorithm**. Dynamic function construction has runtime,
CSP, compatibility and security implications distinct from ordinary
string concatenation. The feature should remain experimental until
measured and tested across a larger corpus.

To measure against the existing Python encoder:

```sh
python -m benchmarks.shared_substring_ablation
```

Next experiments: multiple shared fragments, overlapping candidates,
liveness/cost model and function creation cost, alternative identifier
alphabets, and long-code timing.
