"""Reproduce the complete experimental pipeline.

Typical use from the repository root:

    python scripts/run_experiments.py

This runs the tests, three independent benchmark suites, combines the runs,
and regenerates all figures and tables.  It takes several minutes on a laptop.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Directory for CSVs, tables, and figures.",
    )
    args = parser.parse_args()

    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_tests:
        subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=ROOT,
            check=True,
        )

    inputs: list[str] = []
    for run in range(1, args.runs + 1):
        output = output_dir / f"benchmark_run{run}.csv"
        print(f"\n=== Benchmark run {run}/{args.runs} -> {output} ===")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "asm.benchmark",
                "--repeats",
                str(args.repeats),
                "--output",
                str(output),
            ],
            cwd=ROOT,
            check=True,
        )
        inputs.append(str(output))

    subprocess.run(
        [
            sys.executable,
            "scripts/combine_benchmarks.py",
            *inputs,
            "--output",
            str(output_dir / "benchmark_raw.csv"),
            "--stat",
            "min",
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "asm.analysis",
            "--input",
            str(output_dir / "benchmark_raw.csv"),
            "--outdir",
            str(output_dir),
        ],
        cwd=ROOT,
        check=True,
    )
    print(
        f"\nDone. See {output_dir / 'benchmark_raw.csv'}, "
        f"{output_dir / 'analysis.md'} and {output_dir / 'figures'}."
    )


if __name__ == "__main__":
    main()
