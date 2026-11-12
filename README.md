# JSFuck size reduction

Experimental Python JSFuck encoder that measures output character count against the
reference encoder at [jsfuck.com](https://jsfuck.com/).

## Setup

Python 3.10+ (no runtime dependencies). Node.js is used to execute semantic tests.
To run the benchmark, install the official JSFuck npm package in this directory:

```sh
npm install --no-save jsfuck
python -m unittest discover -s tests -v
python -m jsfuck_py.benchmark
```

For your own input set, pass a JSON array of strings using `--cases cases.json`.
Use `--output results.json` to persist length comparisons.

## API

```python
from jsfuck_py.encoder import encode

expression = encode('console.log(1)', optimize=True, wrap=False)
code = encode('console.log(1)', wrap=True)
```

`wrap=False` produces a JS expression that evaluates to the source string;
`wrap=True` executes it. Use identical settings for both encoder comparisons.

The Python implementation uses mappings derived from the upstream
[aemkei/jsfuck](https://github.com/aemkei/jsfuck) JSFuck 0.5.0 encoder.
It expands the official symbol recipes and uses dynamic programming to choose
between individual-character encodings and built-in multi-character literals.

**Limitations:** This is not a globally optimal JSFuck encoder. The initial
search does not yet share common subexpressions or optimize the string escape
loader. Unicode and execution semantics are tested using Node.js. Benchmark
numbers are computed locally; no performance claims are assumed in advance.
