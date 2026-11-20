"""Combine repeated benchmark runs into one table.

By default the per-case lower envelope (minimum) is used; this is the
least-noisy of the independent medians.  Use ``--stat median`` for the median
across runs instead.

Usage:
    python scripts/combine_benchmarks.py results/benchmark_run1.csv ...
        --output results/benchmark_raw.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

KEY_FIELDS = (
    "experiment",
    "case",
    "dataset",
    "alphabet",
    "n",
    "m",
    "k",
    "algorithm",
    "label",
    "matches",
)
FIELDS = KEY_FIELDS + ("median_ms", "peak_kib", "status")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/benchmark_raw.csv"))
    parser.add_argument(
        "--stat",
        choices=("min", "median"),
        default="min",
        help="Across-run statistic (min is the lower envelope / least-noisy run)",
    )
    args = parser.parse_args()

    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for path in args.inputs:
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row["status"] != "ok":
                    continue
                key = tuple(row[field] for field in KEY_FIELDS)
                groups[key].append(row)

    combined: list[dict[str, object]] = []
    for key, rows in groups.items():
        row = dict(zip(KEY_FIELDS, key))
        for field in ("median_ms", "peak_kib"):
            values = [float(item[field]) for item in rows if item[field] not in ("", None)]
            if values:
                row[field] = round(
                    min(values) if args.stat == "min" else statistics.median(values),
                    6,
                )
            else:
                row[field] = ""
        row["status"] = "ok"
        combined.append(row)

    combined.sort(
        key=lambda row: (
            row["experiment"],
            int(row["n"]),
            int(row["m"]),
            int(row["k"]),
            row["algorithm"],
        )
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(combined)
    meta = {
        "inputs": [str(path) for path in args.inputs],
        "across_run_statistic": args.stat,
        "rows": len(combined),
        "note": "Each input value is already a per-case median; the combined value is the lower envelope across independent suite runs.",
    }
    args.output.with_suffix(".meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print(f"Combined {len(groups)} case/algorithm rows into {args.output}")


if __name__ == "__main__":
    main()
