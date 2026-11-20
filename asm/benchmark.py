"""Benchmark runner.

Run ``python -m asm.benchmark`` (or ``python -m asm.cli bench``) to recreate
``results/benchmark_raw.csv``.  File reading is outside the timed region; each
case is generated in memory before measurement.
"""

from __future__ import annotations

import argparse
import csv
import gc
import json
import platform
import statistics
import sys
import time
import tracemalloc
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .algorithms import (
    kmp_exact,
    landau_vishkin_search,
    levenshtein_banded,
    levenshtein_rolling,
    sellers_full,
    sellers_pruned,
    sellers_rolling,
)
from .generator import (
    Dataset,
    english_dataset,
    mutate,
    planted_dataset,
    prefix_trap_dataset,
    random_dataset,
    repetitive_dataset,
)
from .models import Match

SearchFn = Callable[[str, str, int], Iterable[Match]]


@dataclass(frozen=True)
class Algorithm:
    key: str
    label: str
    fn: SearchFn


SEARCH_ALGORITHMS = (
    Algorithm("sellers_full", "Sellers full matrix", sellers_full),
    Algorithm("sellers_rolling", "Sellers rolling rows", sellers_rolling),
    Algorithm("sellers_pruned", "Sellers threshold-pruned", sellers_pruned),
    Algorithm("landau_vishkin", "Landau-Vishkin + LCE", landau_vishkin_search),
)


def _kmp_adapter(text: str, pattern: str, k: int) -> list[Match]:
    return kmp_exact(text, pattern)


def median_runtime(
    fn: Callable[[], object], repeats: int, target_ms: float = 40.0
) -> float:
    """Median wall-clock time per call, using batched calls for small cases.

    A single sub-millisecond call is dominated by timer resolution and OS
    scheduling noise.  Calls are therefore repeated inside each sample until
    roughly ``target_ms`` of work has been performed, then divided by the
    number of calls.
    """

    fn()  # warm up
    start = time.perf_counter()
    fn()
    estimate = max(time.perf_counter() - start, 1e-6)
    number = max(1, min(2000, int((target_ms / 1000.0) / estimate)))

    samples: list[int] = []
    for _ in range(repeats):
        gc.collect()
        start = time.perf_counter_ns()
        for _ in range(number):
            fn()
        samples.append((time.perf_counter_ns() - start) // number)
    return statistics.median(samples) / 1_000_000.0


def peak_memory(fn: Callable[[], object]) -> tuple[float, object]:
    gc.collect()
    tracemalloc.start()
    result = fn()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024.0, result


class Writer:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.rows: list[dict[str, object]] = []

    def add(self, **row: object) -> None:
        self.rows.append(row)

    def flush(self) -> None:
        fieldnames = [
            "experiment",
            "case",
            "dataset",
            "alphabet",
            "n",
            "m",
            "k",
            "algorithm",
            "label",
            "median_ms",
            "peak_kib",
            "matches",
            "status",
        ]
        with self.path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.rows:
                writer.writerow({key: row.get(key, "") for key in fieldnames})


def _prepare_plan(
    fn: Callable[[], object], target_ms: float = 30.0
) -> tuple[int, list[float]]:
    fn()  # warm up
    start = time.perf_counter()
    fn()
    estimate = max(time.perf_counter() - start, 1e-6)
    number = max(1, min(2000, int((target_ms / 1000.0) / estimate)))
    return number, []


def _run_batch(fn: Callable[[], object], number: int) -> float:
    gc.collect()
    start = time.perf_counter_ns()
    for _ in range(number):
        fn()
    return (time.perf_counter_ns() - start) / number / 1_000_000.0


def run_search_case(
    writer: Writer,
    experiment: str,
    dataset: Dataset,
    algorithms: Iterable[Algorithm],
    repeats: int,
) -> None:
    n, m, k = len(dataset.text), len(dataset.pattern), dataset.k
    plans: list[tuple[Algorithm, Callable[[], object], int, list[float]]] = []
    for algorithm in algorithms:
        fn = lambda algorithm=algorithm: algorithm.fn(dataset.text, dataset.pattern, k)
        number, samples = _prepare_plan(fn)
        plans.append((algorithm, fn, number, samples))

    # Interleave rounds so slow thermal drift affects every algorithm in a
    # comparable way.  The order is reversed on alternate rounds.
    for round_index in range(repeats):
        order = plans if round_index % 2 == 0 else list(reversed(plans))
        for _, fn, number, samples in order:
            samples.append(_run_batch(fn, number))

    for algorithm, fn, _, samples in plans:
        elapsed = statistics.median(samples)
        try:
            peak_kib, result = peak_memory(fn)
            writer.add(
                experiment=experiment,
                case=dataset.name,
                dataset=dataset.name,
                alphabet=dataset.alphabet,
                n=n,
                m=m,
                k=k,
                algorithm=algorithm.key,
                label=algorithm.label,
                median_ms=round(elapsed, 6),
                peak_kib=round(peak_kib, 3),
                matches=len(list(result)),
                status="ok",
            )
            print(
                f"{experiment:24s} {dataset.name:34s} {algorithm.key:18s}"
                f" {elapsed:9.3f} ms {peak_kib:10.1f} KiB"
            )
        except Exception as exc:  # pragma: no cover - benchmark diagnostics
            writer.add(
                experiment=experiment,
                case=dataset.name,
                dataset=dataset.name,
                alphabet=dataset.alphabet,
                n=n,
                m=m,
                k=k,
                algorithm=algorithm.key,
                label=algorithm.label,
                status=f"error: {type(exc).__name__}: {exc}",
            )
            print(f"ERROR {dataset.name} {algorithm.key}: {exc}", file=sys.stderr)


def run_distance_case(
    writer: Writer,
    experiment: str,
    name: str,
    a: str,
    b: str,
    k: int,
    repeats: int,
) -> None:
    n, m = len(a), len(b)
    specs = (
        ("distance_rolling", "Rolling-row Levenshtein", lambda: levenshtein_rolling(a, b)),
        ("distance_banded", "Banded Levenshtein", lambda: levenshtein_banded(a, b, k)),
    )
    plans = []
    for key, label, fn in specs:
        number, samples = _prepare_plan(fn)
        plans.append((key, label, fn, number, samples))

    for round_index in range(repeats):
        order = plans if round_index % 2 == 0 else list(reversed(plans))
        for _, _, fn, number, samples in order:
            samples.append(_run_batch(fn, number))

    for key, label, fn, _, samples in plans:
        elapsed = statistics.median(samples)
        try:
            peak_kib, _ = peak_memory(fn)
            writer.add(
                experiment=experiment,
                case=name,
                dataset=name,
                alphabet="dna",
                n=n,
                m=m,
                k=k,
                algorithm=key,
                label=label,
                median_ms=round(elapsed, 6),
                peak_kib=round(peak_kib, 3),
                matches="",
                status="ok",
            )
            print(f"{experiment:24s} {name:34s} {key:18s} {elapsed:9.3f} ms")
        except Exception as exc:  # pragma: no cover
            writer.add(
                experiment=experiment,
                case=name,
                dataset=name,
                alphabet="dna",
                n=n,
                m=m,
                k=k,
                algorithm=key,
                label=label,
                status=f"error: {exc}",
            )


def benchmark_all(repeats: int = 5, output: Path = Path("results/benchmark_raw.csv")) -> None:
    writer = Writer(output)
    started = time.perf_counter()

    def search(experiment: str, ds: Dataset, algorithms=SEARCH_ALGORITHMS) -> None:
        run_search_case(writer, experiment, ds, algorithms, repeats)

    # 1. Text length, with everything else fixed.
    for n in (500, 1000, 2000, 4000, 8000):
        ds = planted_dataset(n, 80, 2, "dna", seed=100 + n)
        search("text_length", ds)

    # 2. Pattern length, with text length fixed.
    for m in (20, 50, 100, 200, 400):
        ds = planted_dataset(4000, m, 3, "dna", seed=200 + m)
        search("pattern_length", ds)

    # 3. Error threshold.  k = 0 also compares KMP with approximate-search
    # algorithms that reduce to exact matching.
    for k in (0, 1, 2, 4, 8, 16, 32):
        ds = planted_dataset(4000, 100, k, "dna", seed=300 + k)
        algs = SEARCH_ALGORITHMS
        search("threshold", ds, algs)
        if k == 0:
            run_search_case(
                writer,
                "threshold",
                ds,
                (Algorithm("kmp", "KMP (k=0)", _kmp_adapter),),
                repeats,
            )

    # 4. Alphabet size / natural language.
    for alphabet in ("binary", "dna", "english"):
        if alphabet == "english":
            ds = english_dataset(3000, 80, 3, seed=401)
        else:
            ds = planted_dataset(3000, 80, 3, alphabet, seed=400)
        search("alphabet", ds)

    # 5. Adversarial / highly repetitive input.
    search("adversarial", repetitive_dataset(3000, 100, 3, char="A"))
    search(
        "adversarial",
        Dataset(
            name="repeat-AC-n3000-m100-k3",
            text="AC" * 1500,
            pattern="AC" * 50,
            k=3,
            alphabet="binary",
        ),
    )
    search("adversarial", prefix_trap_dataset(3000, 100, 3, seed=500))

    # 6. Same-machine memory scaling.
    for n in (500, 1000, 2000, 4000):
        ds = planted_dataset(n, 80, 2, "dna", seed=600 + n)
        search("memory_scaling", ds)

    # 7. Banded edit distance versus rolling-row edit distance.  The pair is
    # a pattern and a mutated copy, so the true distance is small.
    for target_k in (1, 2, 4, 8, 16, 32):
        from random import Random

        rng = Random(700 + target_k)
        base = "".join(rng.choice("ACGT") for _ in range(1000))
        other = mutate(base, target_k, "ACGT", rng)
        run_distance_case(
            writer,
            "banded_distance",
            f"distance-n1000-k{target_k}",
            base,
            other,
            target_k,
            repeats,
        )

    writer.flush()

    meta = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "repeats": repeats,
        "timing": "median per-call wall time; algorithms interleaved, batched",
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    output.with_suffix(".meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {output} in {meta['elapsed_seconds']} s")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path("results/benchmark_raw.csv"))
    args = parser.parse_args(argv)
    benchmark_all(args.repeats, args.output)


if __name__ == "__main__":
    main()
