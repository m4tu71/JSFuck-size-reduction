# Generated JSFuck expression CSE — feasibility study

## Scope

This is **not** source-code substring reuse. It measures repeated
subexpressions inside the *already compiled* `[]()!+` output. The known
`[]["at"]["constructor"]` expression is a particularly relevant target:
the encoder uses it for Unicode escape restoration and, sometimes, the
outer execution wrapper.

An exact Function-constructor subexpression is 382 emitted characters at
the current version (0.1.0.dev6). It occurs:
- once for `false` with `wrap=True`;
- twice for `?` with `wrap=True`;
- three times for `あ` with `wrap=True`.

## First experiment: private helper parameter

Treat the constructor as one reusable argument, and dynamically compile
a helper whose expression body refers to that argument:

```js
// Ordinary JavaScript illustration only — never a literal JSFuck output.
Function("return function(a){return " + rewrittenExpression + "}")()(F)
```

Here `rewrittenExpression` is the original generated JSFuck expression
with complete known constructor nodes replaced by `(a)`. The whole
helper body must be encoded as a JSFuck string. The tool only offers the
candidate when the **complete** final result is shorter. No blind textual
substring replacement is applied to arbitrary expression fragments.

### Verified results

Node.js 22, pinned current Python encoder, experimental output-string CSE:

| Source | wrap | Original output | Function appearances | Forced private-helper output | Net saving |
|---|---|---:|---:|---:|---:|
| `false` | false | 6 | 0 | not applicable | 0 |
| `false` | true | 392 | 1 | not applicable | 0 |
| `?` | false | 1,298 | 1 | not applicable | 0 |
| `?` | true | 1,684 | 2 | 59,230 | −57,546 |
| `あ` | true | 3,138 | 3 | 121,384 | −118,246 |
| `console.log(1)` | true | 1,296 | 1 | not applicable | 0 |
| `const a=1;` | true | 1,647 | 1 | not applicable | 0 |

The forced helper's semantics were verified in a separate Node.js
roundtrip test. It is nevertheless much larger, and therefore **does not
change the encoder output**.

## Interpretation

Repeated 382-character subexpressions are appealing, but substituting an
identifier within JSFuck-only output means paying for an additional function
definition encoded as a *string*. That double encoding overwhelms the
potential savings from two or three references. Source length alone does
not imply that this approach will become profitable.

The theoretical variable-binding savings, before fixed costs, are roughly

```
(k - 1) * size(sharedExpression) - k * size(reference)
```

for `k` appearances, but this estimate ignores function construction and
the encoding of the rewritten body; that missing term dominates here.

## Next research

1. **Optimize before final code generation.** Represent repeated generated
   subexpressions as typed DAG nodes. Share only semantic nodes; never
   arbitrary matching strings. Track receiver binding for native methods,
   and independently validate side effects and evaluation order.
2. **Try structure-specific expression rewrites.** Avoid producing repeated
   `Function` constructors in the first place by combining escape
   restoration and execution steps, rather than adding a general-purpose
   variable helper around an already expanded JSFuck expression.
3. **Compare the earlier source-level helper strategy.** The source-level
   helper encodes ordinary short JavaScript with a reused argument, not a
   long nested JSFuck expression. It has a much more favorable cost model,
   as measured in PR #8.
4. **Search for genuinely cheap reusable scopes.** Array callbacks and
   Reduce/Bind constructs may expose an already computed value without
   encoding the entire expanded expression body, but must be proven by a
   complete output-length and semantics test.

This PR intentionally keeps generated-output CSE research-only.
Use `python -m benchmarks.generated_expression_cse` to reproduce.
