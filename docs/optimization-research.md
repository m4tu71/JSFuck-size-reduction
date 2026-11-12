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
