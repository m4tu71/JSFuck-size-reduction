# Changelog

This project uses [Semantic Versioning](https://semver.org/) for released
Python encoder versions and PEP 440 for development version identifiers.

## Unreleased

- Add a Python encoder based on upstream JSFuck 0.5.0.
- Compare against a pinned official JSFuck encoder with semantic tests.
- Add cost-based character recipes and native-function string tokens.
- Add machine-readable benchmark reports with version metadata.


## 0.1.0.dev7 (development)

- Evaluate adjacent character generation through Function escape restoration,
  UTF-16/code-point batching, repeated multi-character units and shared
  generated expressions.
- Add bounded 2–16-character repeat candidates to the string token DP,
  comparing full emitted JSFuck expression costs.
- Add Node.js roundtrip and execution-wrapper regression tests.
- Add targeted ablation/segmentation studies and document cases where
  whole-string restoration beats independent substring encoding.

## 0.1.0.dev6 (development)

- Add opt-in shared-substring reconstruction through an isolated generated
  function parameter, encoding each repeated fragment once.
- Bound substring and helper-name candidate search; compare full emitted
  JSFuck expression lengths and keep the legacy result if no improvement.
- Provide an optional identifier-exclusion safeguard for names already
  present in the original JavaScript source without modifying that source.
- Add Node.js roundtrip, identifier avoidance, and dedicated ablation tests.

## 0.1.0.dev5 (development)

- Explore batched decimal code reconstruction using String.fromCharCode and
  String.fromCodePoint. Use split plus reduce/apply/bind to pass arrays of
  numeric strings without literal commas in JSFuck output.
- Handle UTF-16 surrogate pairs and bootstrap uppercase P via char code 80
  when spelling fromCodePoint.
- Compare fully compiled JSFuck output costs with the existing escape-loader
  strategy, retaining the shortest candidate.
- Explore long unmapped spans inside a JavaScript source string.
- Add Unicode/ASCII semantic tests, targeted benchmarks and controlled
  ablation of the numeric-code strategy.

## 0.1.0.dev4 (development)

- Replace heuristic typed-expression concatenation with structured expression
  nodes and a precedence-aware JSFuck printer that groups only when needed.
- Explore cost-based String.prototype.repeat candidates for long runs of
  individual characters, retaining existing encodings when shorter.
- Add targeted Node.js semantic tests for precedence, repeat counts, escaped
  punctuation and deterministic typed-string cases.
- Add controlled repeat ablation and pinned official reference benchmarks.

## 0.1.0.dev3 (development)

- Add a typed dynamic-programming string builder that distinguishes
  non-string primitives from string-valued prefixes.
- Avoid redundant string coercions for primitive literals anywhere in a
  source string, and remove unneeded outer parentheses for standalone
  `false`, `true`, `undefined`, `NaN` and `Infinity`.
- Track JavaScript precedence carefully for multi-addition number recipes.
- Retain a conservative fallback for literal `!+` to avoid ambiguous
  escape-loader expressions until grammar-aware printing is implemented.
- Add 120 deterministic mixed-token Node.js roundtrip cases and controlled
  ablation on both ordinary JavaScript and primitive-heavy inputs.

## 0.1.0.dev2 (development)

- Search native Array-method source-string suffixes using a one-argument
  `slice(start)` expression, selecting candidates by emitted JSFuck cost.
- Add semantic tests, a 20-snippet JavaScript source corpus, and controlled
  ablation benchmarks separating old and newly introduced gains.

## 0.1.0.dev1 (development)

- Choose the shorter of direct escape decoding and placeholder split/join
  based on total generated JSFuck length, not the count of unknown characters.
- Omit redundant string coercion for trailing `false`, `true`, `undefined`,
  `NaN` and `Infinity`, preserving JavaScript's unary-plus parsing rules.
- Restore validated official fallback mappings for `E`, `R`, `:` and `?`.
  Pinned recipes can be regenerated using `tools/generate_reference_fallback.py`.

## Versioning policy

- First release target: **0.1.0** (not yet released).
- Current development version: **0.1.0.dev7**.
- Increase **PATCH** for backwards-compatible bug fixes.
- Increase **MINOR** for backwards-compatible features and optimization strategies.
- Increase **MAJOR** for incompatible changes in the public Python API or its output contract.
- Use `vX.Y.Z` Git tags and matching GitHub releases for stable versions.
- Do not tag or release a development PR before it has been merged.

The official JSFuck version is a **reference dependency**, not this project's version.
