# Whole-source Unicode escape spelling search (negative result)

## Research question

The experimental Unicode Function wrapper (dev10) chooses the cheapest
of `\\uXXXX`, `\\xHH`, `\\u{HEX}` for **each individual Unicode
character** by counting the encoded JSFuck tokens. Can an apparently more
expensive spelling of one character make the **whole source** cheaper,
because DP recognizes a multi-character token across escape boundaries?

This branch tests that hypothesis without modifying the production encoder.

## Method

- Respect the conservatively validated lexical subset used by
  `fused_wrapper_study.py`: do not re-interpret JavaScript syntax.
- Start from the current per-character best expression.
- For eligible characters, enumerate equivalent UTF-16, code-point,
  and (when applicable) two-digit hex spellings with uppercase/lowercase
  hexadecimal digits.
- Evaluate each substitution using the **complete encoded source body**
  `_tokens(source, True)`, rather than only the escape in isolation.
- Accept strict wins only. Bound the probe to at most 24 substitutions,
  24 eligible Unicode characters and 4,096 input characters.
- Validate the alternative source by running the generated JSFuck call
  in Node.js and comparing stdout to the original source.

This is a deterministic coordinate-descent experiment, **not** proof
of global optimality over all escape spellings.

## Results

Twelve targeted Unicode source examples including Japanese, emoji,
Latin accents, Cyrillic/Greek, repeated Japanese and multiple literals:

| Input | Local escape choice | Whole-source search | Additional saving |
|---|---:|---:|---:|
| `console.log("あ")` | 3,544 | 3,544 | 0 |
| `console.log("漢字")` | 5,353 | 5,353 | 0 |
| `console.log("😀😃")` | 5,409 | 5,409 | 0 |
| `console.log("あい")` | 5,138 | 5,138 | 0 |
| `console.log("漢字仮名交じり文")` | 15,090 | 15,090 | 0 |

Across the 12 cases after choosing between the existing wrapper and
locally optimized direct wrapper, **67,201 → 67,201** output characters;
no additional saving. This is a small selected set, not an exhaustive
negative proof.

The result suggests that, for the tested inputs and candidate spellings,
the token DP already handles escape sequences well enough that changing
their per-character spelling does not produce an additional win.

## Conclusion and next investigation

Do **not** expose the global spelling search as an encoder API setting:
it adds full-input DP calls without demonstrated output savings. Keep it
as a standalone research-only module, its tests and a reproducible
benchmark. No version bump; default encoder output remains unchanged.

Higher-value avenues:
1. Modify **where escaping occurs** (Unicode string literal vs source
   reconstruction) rather than just how the same escape is spelled.
2. Evaluate caching or combining the setup for repeated calls to
   Function, split/reduce/apply/bind with a typed pre-emission DAG.
3. Compare on a representative set of longer codebases, measuring
   encoding latency and actual output size.
4. Use a real ECMAScript lexer/parser before attempting to transform
   complex string templates, regex or comments.

Run:

```sh
python -m benchmarks.escape_spelling_ablation
python -m unittest discover -s tests -v
```
