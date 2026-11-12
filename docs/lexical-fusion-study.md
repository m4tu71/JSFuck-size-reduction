# Conservative Unicode-literal wrapper fusion: expanded lexical subset

## Goal

The Python encoder can sometimes reduce output size by avoiding two
`Function` constructors for `wrap=True`: instead of restoring Unicode
source text and executing that restored source, it directly compiles a
JavaScript program containing Unicode escape sequences inside string
literals.

PR #12 initially permitted only one plain `console.log("...")` call.
This research expands the **opt-in** feature to several string literals
and statements, including uncomplicated single-quoted literals.

## Lexical safety contract

This is **not an ECMAScript parser**. Before rewriting, the scanner must
accept the entire source:

- All Unicode characters must appear inside unescaped single- or
  double-quoted string literals.
- No backslashes or line terminators inside a literal; no lone surrogate
  code units.
- No backticks, slashes (comments, regex, division), backslashes or
  non-ASCII characters outside string literals.
- A single-quoted literal cannot contain a double quote, because the
  normalizer changes its delimiters to double quotes.
- Total source length at most 4,096 characters.

If the whole source violates a rule, return no fusion candidate and
leave the existing encoder behavior unchanged.

The scanner selects the cheapest tested literal escape per character
(`\\uXXXX`, `\\xHH`, or `\\u{HEX}`) using the existing JSFuck
token cost. It then compiles the transformed JS source directly using
`Function`. The encoder only selects the candidate if **the complete
output is shorter**. The option remains
`fuse_wrapped_unicode=False` by default, and only affects
`optimize=True, wrap=True, parent_scope=False`.

The resulting single-function compilation executes the same statements
but does not necessarily preserve the raw source string. Accordingly,
the ordinary string-returning `wrap=False` mode does not use it.

## Results

Node.js 22, 17 selected inputs with and without
`fuse_wrapped_unicode=True`:

| Source | Standard | Fusion enabled | Saved |
|---|---:|---:|---:|
| `console.log("あ")` | 5,256 | 3,544 | 1,712 |
| `console.log('あ')` | 5,306 | 3,544 | 1,762 |
| `console.log("漢字")` | 5,570 | 5,353 | 217 |
| `console.log('漢字')` | 5,620 | 5,353 | 267 |
| `let name="あ";console.log(name)` | 5,846 | 5,543 | 303 |
| `let name='あ';console.log(name)` | 5,896 | 5,543 | 353 |
| `console.log("あ");console.log("い")` | 6,208 | 6,208 | 0 |
| `const x="漢字";console.log(x)` | 6,163 | 6,163 | 0 |

Aggregate of the 17 deliberately selected samples: **105,405 → 100,791**
JSFuck characters, **4,614 saved (4.38%)**. These numbers include
cases already optimized in PR #12. In the same corpus the new source
forms contributed 2,685 characters of the total saving; not all is
incremental on the previous version. They do not estimate general
JavaScript average savings.

Multiple literals can be accepted and retain exact output in Node.js
without being chosen on cost: for instance
`console.log("漢字", "あ")` produces a direct-compile candidate of
7,899 characters, which is longer than the 5,864-character baseline.

## Validation

Node.js tests check:

- Exact stdout matching between original JS, existing JSFuck wrapper,
  direct fused candidate and cost-selected opt-in output for several
  double- and single-quoted literals and multiple statements.
- Unescaped quote handling, surrogate escape handling, and the
  `[]()!+` alphabet.
- Safe fallback for strings containing backslash escapes, comments,
  regex syntax, backticks, Unicode in source code rather than literals,
  and ambiguous single-quoted content.
- No behavior change for `wrap=False` or `parent_scope=True`.

## Follow-up

1. Integrate a real ECMAScript lexer/parser for broader source coverage.
   A regex/scanner heuristic cannot safely support arbitrary expressions.
2. Generate escape alternatives *globally* rather than per character:
   DP may find cheaper combinations when `false`, `true`, and native
   function tokens cross escape boundaries.
3. Compare JSFuck expression construction time and runtime; source
   length is not the only relevant engineering cost.
4. Investigate fused execution for Unicode-literal JavaScript inside
   full projects while preserving directives, lexical scope and source
   semantics.

Reproduce:

```sh
python -m benchmarks.lexical_fusion_ablation
python -m unittest discover -s tests -v
```
