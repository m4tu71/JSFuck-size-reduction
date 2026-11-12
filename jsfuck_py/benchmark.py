"""Length benchmark against the installed official jsfuck npm package.

Install official reference separately: npm install --no-save jsfuck
The encoder under evaluation remains pure Python.
"""
import argparse
import json
import subprocess
from pathlib import Path

from jsfuck_py.encoder import encode

DEFAULT_CASES = [
    "false", "true", "undefined", "NaN", "Infinity",
    "hello", "Hello world!", "1234567890", "console.log('hello')",
    "function add(a,b){return a+b}", "あいうえお", "~!~",
]
NODE_SCRIPT = """
const fs = require('fs');
const { JSFuck } = require('jsfuck');
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(cases.map(x => JSFuck.encode(x, false, false).length)));
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, help="JSON array of inputs")
    parser.add_argument("--output", type=Path, help="Write machine-readable JSON results")
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8")) if args.cases else DEFAULT_CASES
    if not isinstance(cases, list) or not all(isinstance(x, str) for x in cases):
        parser.error("cases must be a JSON array of strings")
    reference = subprocess.run(
        ["node", "-e", NODE_SCRIPT], input=json.dumps(cases),
        text=True, capture_output=True, check=True)
    lengths = json.loads(reference.stdout)
    results = []
    for value, baseline in zip(cases, lengths, strict=True):
        optimized = len(encode(value))
        results.append({"input": value, "baseline": baseline,
                        "python": optimized, "delta": optimized - baseline,
                        "reduction_pct": round(100 * (baseline - optimized) / baseline, 2)
                        if baseline else None})
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
