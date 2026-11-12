# Fusing Unicode restoration with wrap=True execution

## Existing architecture

For a JavaScript input with characters outside the direct JSFuck mapping,
the Python encoder builds the string source via a `Function`-based escape
decoder, then, when `wrap=True`, creates another `Function` from that
string and invokes it.

Conceptually:

```js
const F = []["at"]["constructor"];
F(F('return "console.log(\\"\\u3042\\")"')())();
```

A general replacement must preserve JavaScript parser contexts and
execution mode; blindly replacing raw Unicode source characters with
`\\uXXXX` changes semantics in comments, regexp literals, template
literals and certain identifiers. It cannot be applied to arbitrary
JavaScript without a grammar-aware rewrite.

## Constrained direct-compile candidate

In this study, only the grammar of a **single console.log call containing
one plain double-quoted string literal** is accepted:

```js
console.log("あ")
```

Inside the quoted string, Unicode characters may be represented using
`\\uXXXX`, `\\xHH` or `\\u{HEX}` escapes, including surrogate pairs.
Every escape candidate is costed using the existing Python JSFuck token
encoder. The transformed *source* is encoded directly and passed to a single
`Function` constructor; it is not first reconstructed by a separate
`Function`.

The alternative is **opt-in** as `fuse_wrapped_unicode=True`. It is
considered only with `wrap=True`, `parent_scope=False` and
`optimize=True`. The encoder compares complete emitted lengths and keeps
its original result whenever the fused candidate is larger. String mode
and parent-scope execution remain unchanged.

This is deliberately conservative: the current prototype does not attempt
to parse arbitrary ECMAScript, rewrite identifier escapes, normalize
quotes or change source lexical bindings.

## Pinned results

Node.js 22, same Python encoder with or without the direct-compile
candidate, output characters:

| Source | Existing wrapped output | Direct compilation | Difference |
|---|---:|---:|---:|
| `console.log("あ")` | 5,256 | 3,544 | 1,712 shorter |
| `console.log("漢字")` | 5,570 | 5,353 | 217 shorter |
| `console.log("漢字仮名交じり文")` | 6,337 | 15,090 | 8,753 longer |
| `console.log("漢字" × 12)` | 6,617 | 6,400 | 217 shorter |
| `console.log("漢字" × 36)` | 8,081 | 10,854 | 2,773 longer |
| `console.log("😀😃" × 12)` | 10,819 | 43,348 | 32,529 longer |
| `console.log("😀😃" × 36)` | 22,123 | 126,124 | 104,001 longer |
| `console.log("ΩλЖ中" × 24)` | 23,023 | 163,336 | 140,313 longer |

All eight eligible cases: **87,826 -> 85,680** when the cheaper
candidate wins. **2,146 characters / 2.44%** are saved on this small,
intentionally selected corpus. Node.js stdout matches the original
wrapper for eligible tests. It does **not** support a general claim about
long JavaScript files or typical input.

The `\\u{HEX}` escape option improved cost for supplementary-plane
characters over UTF-16 surrogate escapes in isolation, but did not beat
the existing full decoder/repeat strategy in tested emoji cases.

## Recommendations

- **Long-run next step:** tokenize ECMAScript source so rewrites are
  restricted to actual quoted literal content. Do not assume text
  substitution is semantics-preserving.
- **Fixed costs:** `Function` construction can sometimes be saved by
  moving Unicode decoding into JavaScript's parser, but long escaped
  literals may cost much more than repeat and numeric-code generators.
- **Call-site optimization:** give every wrapping strategy an exact
  grammar/semantics contract, and compare *whole output length* rather
  than counting constructor occurrences.
- **Execution semantics:** `eval` is not a drop-in alternative to
  `Function`; top-level return, lexical scope, strict mode and
  completion values can differ.

Reproduce using:

```sh
python -m benchmarks.fused_wrapper_study
python -m unittest discover -s tests -v
```
