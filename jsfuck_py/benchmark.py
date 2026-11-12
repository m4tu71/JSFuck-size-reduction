"""Length benchmark against a pinned jsfuck.com upstream encoder (0.5.0)."""
import argparse
import json
import subprocess
from pathlib import Path
from urllib.request import urlopen

from jsfuck_py.encoder import encode

DEFAULT_CASES = [
    "0", "1", "2", "01", "10", "1234567890", "false", "true", "undefined", "NaN", "Infinity",
    "hello", "Hello world!", "function", "function function", "function at() { [native code] }", "function map() { [native code] }", "native", "at", "console.log('hello')",
    "function add(a,b){return a+b}", "あいうえお", "~!~",
]
REFERENCE_COMMIT = "6f8fdf31f18a4f2df3bf2576f313b3abeca4c89d"
REFERENCE_URL = ("https://raw.githubusercontent.com/aemkei/jsfuck/"
                 + REFERENCE_COMMIT + "/jsfuck.js")
NODE_SCRIPT = """
const fs = require('fs');
const { source, cases, wrap } = JSON.parse(fs.readFileSync(0, 'utf8'));
const exports = {};
new Function('exports', source)(exports);
if (!exports.JSFuck?.encode) throw new Error('Invalid JSFuck reference encoder');
process.stdout.write(JSON.stringify(cases.map(x => exports.JSFuck.encode(x, wrap, false).length)));
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, help="JSON array of inputs")
    parser.add_argument("--reference", type=Path, help="Use local official jsfuck.js instead of fetching pinned source")
    parser.add_argument("--output", type=Path, help="Write machine-readable JSON results")
    parser.add_argument("--wrap", action="store_true", help="Compare eval-wrapped JavaScript execution")
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8")) if args.cases else DEFAULT_CASES
    if not isinstance(cases, list) or not all(isinstance(x, str) for x in cases):
        parser.error("cases must be a JSON array of strings")
    source = (args.reference.read_text(encoding="utf-8") if args.reference else
              urlopen(REFERENCE_URL, timeout=20).read().decode("utf-8"))
    reference = subprocess.run(
        ["node", "-e", NODE_SCRIPT], input=json.dumps({"source": source, "cases": cases, "wrap": args.wrap}),
        text=True, capture_output=True, check=True)
    lengths = json.loads(reference.stdout)
    results = []
    for value, baseline in zip(cases, lengths, strict=True):
        optimized = len(encode(value, wrap=args.wrap))
        results.append({"input": value, "baseline": baseline,
                        "python": optimized, "delta": optimized - baseline,
                        "reduction_pct": round(100 * (baseline - optimized) / baseline, 2)
                        if baseline else None})
    print(f"Reference: aemkei/jsfuck@{REFERENCE_COMMIT} (JSFuck 0.5.0), wrap={args.wrap}")
    print(f"{'input':24} {'jsfuck.com':>12} {'python':>12} {'delta':>10} {'saving %':>10}")
    for item in results:
        print(f"{item['input'][:24]!r:24} {item['baseline']:12} "
              f"{item['python']:12} {item['delta']:10} "
              f"{str(item['reduction_pct']):>10}")
    if args.output:
        args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")


if __name__ == "__main__":
    main()
