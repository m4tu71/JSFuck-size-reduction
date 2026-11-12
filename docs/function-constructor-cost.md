# Function constructor access: complete JSFuck setup cost

## Question

Can an equivalent JavaScript expression shorten the repeated
`[]["at"]["constructor"]` used by the current Python JSFuck encoder?

Rather than attempt variable CSE on already-expanded output, compare
**semantically equivalent Function constructor access paths** before
changing generated program structure.

## Candidate families

All candidates are compiled to the exact JSFuck alphabet `[]()!+`:

- `[][method]["constructor"]` where method is a standard Array prototype
  function (`at`, `flat`, `fill`, `find`, `pop`, `keys`, etc.).
- `[]["constructor"]["constructor"]` via the Array constructor.
- `([]+[])["constructor"]["constructor"]` via String.
- `(+[])["constructor"]["constructor"]` via Number.
- `(![])["constructor"]["constructor"]` via Boolean.

For each expression, Node.js verifies `eval(jsfuck) === Function`.
A separate test compiles `return 42` and checks the return value.
The benchmark reports both access cost and full function-body call cost.

## Initial measured comparison (Node.js 22)

| Constructor path | JSFuck characters | Difference vs at |
|---|---:|---:|
| `array.at.constructor` | 382 | 0 |
| `array.flat.constructor` | 416 | +34 |
| `array.fill.constructor` | 433 | +51 |
| `array.find.constructor` | 435 | +53 |
| `array.sort.constructor` | 463 | +81 |
| `array.filter.constructor` | 471 | +89 |
| `array.join.constructor` | 636 | +254 |
| `array.constructor.constructor` | 698 | +316 |
| `number.constructor.constructor` | 701 | +319 |
| `boolean.constructor.constructor` | 701 | +319 |
| `string.constructor.constructor` | 703 | +321 |
| `array.map.constructor` | 1,666 | +1,284 |

The full call has the same relative ordering because the Function body
payload and invocation suffix are the same across these candidates.
Examples: `return 42` 588 chars, `return true` 559 chars,
`console.log(1)` 1,296 chars, `console.log("hello")` 2,995 chars.

A follow-up candidate expansion covers additional built-in Array methods;
these results demonstrate no gain among the initially measured paths.
They do not mathematically prove that `at` is globally shortest among
all possible JavaScript expressions.

## Caution interpreting textual occurrence counts

Searching emitted JSFuck for an exact constructor substring is *not* an
AST-level count of Function evaluations. A substring may appear within
mapping recipes, nested property access or other expressions. For example,
`wrap=True` for `console.log("あ")` includes three textual appearances
of the canonical constructor expression, but this alone does not prove
three redundant semantically identical Function constructions.

Any future common-subexpression elimination must operate on typed
expressions, with evaluation-order and receiver binding guarantees,
rather than replace arbitrary matching output strings.

## Conclusion

Do not change the production Function constructor recipe unless a proven
shorter, type-correct candidate exists. The dominant opportunity in the
tested paths is not a cheaper spelling of `Function`; it is reducing the
number of times generator setup is needed (e.g. Unicode source decoding
merged into execution) or eliminating repeated argument-array setup.

Next:
- Evaluate a **pre-emission typed DAG** for repeated generator expressions.
- Compare fused Function Unicode source execution with direct string
  assembly on a realistic corpus, preserving parsing semantics.
- Separate output size, encoding wall-clock time and JS runtime before
  recommending an architecture change.

Reproduction:

```sh
python -m benchmarks.function_constructor_study
python -m unittest discover -s tests -v
```

This research branch intentionally does not change the default encoder.
