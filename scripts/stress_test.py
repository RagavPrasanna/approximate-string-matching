"""Optional stress and soak checks for the approximate-search implementations.

Run from the project root:

    python scripts/stress_test.py

The script uses larger inputs than the unit tests but keeps the reference
comparison within a single process.  It is intended for occasional execution,
not as part of the fast test suite.
"""

from __future__ import annotations

import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from asm.algorithms import (
    kmp_exact,
    landau_vishkin_search,
    sellers_full,
    sellers_pruned,
    sellers_rolling,
)
from asm.generator import (
    Dataset,
    planted_dataset,
    random_dataset,
    repetitive_dataset,
)
from asm.models import as_dict
from asm.reference import validate_structure


def peak_kib(fn) -> float:
    tracemalloc.start()
    result = fn()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024.0


def run_case(ds: Dataset, algorithms) -> list[str]:
    n, m, k = len(ds.text), len(ds.pattern), ds.k
    lines = [f"case={ds.name} n={n} m={m} k={k}"]
    reference = None

    for name, fn in algorithms:
        started = time.perf_counter()
        matches = fn(ds.text, ds.pattern, k)
        elapsed = time.perf_counter() - started
        validate_structure(matches, n, k)
        result = as_dict(matches)
        if reference is None:
            reference = result
        else:
            assert result == reference, f"{name} disagrees with reference on {ds.name}"
        lines.append(
            f"  {name:16s} time={elapsed:9.3f} s matches={len(matches):7d}"
        )

    if k == 0:
        exact = as_dict(kmp_exact(ds.text, ds.pattern))
        assert exact == reference, "KMP disagrees at k=0"
        lines.append("  KMP agrees with Sellers at k=0")

    return lines


def main() -> None:
    cases = [
        (planted_dataset(10_000, 10, 0, "dna", seed=901), "small-pattern exact"),
        (planted_dataset(50_000, 100, 3, "dna", seed=902), "medium"),
        (random_dataset(100_000, 10, 2, "dna", seed=903), "large-text short-pattern"),
        (planted_dataset(20_000, 1_000, 2, "dna", seed=904), "long-pattern"),
        (repetitive_dataset(50_000, 100, 3), "repetitive"),
    ]

    lines = ["Approximate string matching - stress/soak results", ""]
    for ds, label in cases:
        algos = [
            ("sellers_full", sellers_full),
            ("sellers_rolling", sellers_rolling),
            ("sellers_pruned", sellers_pruned),
            ("landau_vishkin", landau_vishkin_search),
        ]
        if label == "long-pattern":
            # A 20,000 x 1,000 full matrix is intentionally skipped; rolling
            # rows exercises the same DP in practical memory.
            algos = [item for item in algos if item[0] != "sellers_full"]
        lines.append(f"### {label}")
        lines.extend(run_case(ds, algos))
        lines.append("")

    # One explicit memory observation for the two extreme storage strategies.
    ds = planted_dataset(50_000, 100, 3, "dna", seed=902)
    full_peak = peak_kib(lambda: sellers_full(ds.text, ds.pattern, ds.k))
    rolling_peak = peak_kib(lambda: sellers_rolling(ds.text, ds.pattern, ds.k))
    lines.extend(
        [
            "### Peak memory on n=50,000, m=100, k=3",
            f"  sellers_full    peak={full_peak:10.1f} KiB",
            f"  sellers_rolling peak={rolling_peak:10.1f} KiB",
        ]
    )
    assert rolling_peak < full_peak

    text = "\n".join(lines)
    Path("results").mkdir(exist_ok=True)
    Path("results/test_plan_stress.txt").write_text(text, encoding="utf-8")
    print(text)
    print("\nWrote results/test_plan_stress.txt")


if __name__ == "__main__":
    main()
