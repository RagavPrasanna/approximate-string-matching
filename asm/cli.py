"""Command-line entry point: ``python -m asm.cli ...``."""

from __future__ import annotations

import argparse
import random
import time
from pathlib import Path

from .algorithms import (
    kmp_exact,
    landau_vishkin_search,
    levenshtein_banded,
    levenshtein_full,
    levenshtein_rolling,
    sellers_full,
    sellers_pruned,
    sellers_rolling,
)
from .generator import planted_dataset
from .models import Match, as_dict
from .reference import brute_force_search, compare_to_reference

ALGORITHMS = {
    "full": sellers_full,
    "rolling": sellers_rolling,
    "pruned": sellers_pruned,
    "lv": landau_vishkin_search,
    "kmp": lambda text, pattern, k: kmp_exact(text, pattern),
}


def _non_negative_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return number


def _positive_int(value: str) -> int:
    number = _non_negative_int(value)
    if number == 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def _format_matches(text: str, matches: list[Match], limit: int = 20) -> str:
    if not matches:
        return "  (no matches)"
    lines = []
    for match in matches[:limit]:
        end = match.end
        start = max(0, end - 12)
        context = text[start:end]
        if start:
            context = "..." + context
        lines.append(
            f"  end={end:5d} (1-based {end:5d})  d={match.distance}  before: {context!r}"
        )
    if len(matches) > limit:
        lines.append(f"  ... {len(matches) - limit} more")
    return "\n".join(lines)


def command_search(args: argparse.Namespace) -> None:
    if args.text_file:
        try:
            text = Path(args.text_file).read_text(encoding=args.encoding)
        except OSError as exc:
            raise SystemExit(f"error: cannot read text file: {exc}") from exc
    else:
        text = args.text
    pattern = args.pattern
    fn = ALGORITHMS[args.algorithm]
    start = time.perf_counter()
    matches = fn(text, pattern, args.k)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"text length={len(text)} pattern length={len(pattern)} k={args.k}")
    print(f"algorithm={args.algorithm} time={elapsed:.3f} ms matches={len(matches)}")
    print(_format_matches(text, matches, args.limit))


def command_distance(args: argparse.Namespace) -> None:
    print(f"full matrix      : {levenshtein_full(args.a, args.b)}")
    print(f"rolling rows     : {levenshtein_rolling(args.a, args.b)}")
    print(f"banded (k={args.k})  : {levenshtein_banded(args.a, args.b, args.k)} (k+1 means > k)")


def command_demo(args: argparse.Namespace) -> None:
    text = args.text or "ABCXDEFGABXDEFGABCDEF"
    pattern = args.pattern or "ABCDEF"
    print("Approximate string matching demonstration")
    print(f"Text    : {text}")
    print(f"Pattern : {pattern}")
    print("Matches are reported by 0-based exclusive end position.\n")

    for k in range(0, args.max_k + 1):
        print(f"k = {k}")
        for name in ("rolling", "pruned", "lv"):
            start = time.perf_counter()
            matches = ALGORITHMS[name](text, pattern, k)
            elapsed = (time.perf_counter() - start) * 1000
            ends = ", ".join(f"{m.end}(d={m.distance})" for m in matches)
            print(f"  {name:8s} {elapsed:7.3f} ms  {ends or '-'}")
        if k == 0:
            print(f"  kmp      {', '.join(str(m.end) for m in kmp_exact(text, pattern)) or '-'}")
        print()

    print("Planted-mutation experiment:")
    for k in (0, 1, 2, 4):
        ds = planted_dataset(800, 40, k, "dna", seed=42)
        start = time.perf_counter()
        matches = sellers_rolling(ds.text, ds.pattern, k)
        elapsed = (time.perf_counter() - start) * 1000
        print(
            f"  k={k}  n={len(ds.text)} m={len(ds.pattern)}  "
            f"matches={len(matches):3d}  time={elapsed:.3f} ms"
        )


def command_validate(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    algorithms = {
        "sellers_full": sellers_full,
        "sellers_rolling": sellers_rolling,
        "sellers_pruned": sellers_pruned,
        "landau_vishkin": landau_vishkin_search,
    }
    checks = 0
    for _ in range(args.cases):
        n = rng.randint(0, 14)
        m = rng.randint(0, 10)
        k = rng.randint(0, 5)
        alphabet = rng.choice(["ab", "abc", "ACGT"])
        text = "".join(rng.choice(alphabet) for _ in range(n))
        pattern = "".join(rng.choice(alphabet) for _ in range(m))
        expected = as_dict(brute_force_search(text, pattern, k))
        for name, fn in algorithms.items():
            actual = as_dict(fn(text, pattern, k))
            if actual != expected:
                raise SystemExit(
                    f"FAIL {name}: text={text!r} pattern={pattern!r} k={k}\n"
                    f"expected={expected}\nactual={actual}"
                )
            checks += 1
    print(f"OK: {checks} algorithm/case comparisons against brute force")


def command_bench(args: argparse.Namespace) -> None:
    from .benchmark import benchmark_all

    benchmark_all(args.repeats, Path(args.output))


def command_analyze(args: argparse.Namespace) -> None:
    from .analysis import main as analysis_main

    analysis_main(["--input", args.input, "--outdir", args.outdir])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asm",
        description="Approximate string matching project: algorithms, demos, benchmarks",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search", help="run one approximate search")
    search.add_argument("--text", default="ABCXDEFG")
    search.add_argument("--text-file")
    search.add_argument("--encoding", default="utf-8")
    search.add_argument("--pattern", default="ABCDEF")
    search.add_argument("--k", type=_non_negative_int, default=1)
    search.add_argument("--algorithm", choices=sorted(ALGORITHMS), default="rolling")
    search.add_argument("--limit", type=_positive_int, default=20)
    search.set_defaults(func=command_search)

    distance = sub.add_parser("distance", help="compare distance implementations")
    distance.add_argument("a")
    distance.add_argument("b")
    distance.add_argument("--k", type=_non_negative_int, default=3)
    distance.set_defaults(func=command_distance)

    demo = sub.add_parser("demo", help="show the effect of increasing k")
    demo.add_argument("--text")
    demo.add_argument("--pattern")
    demo.add_argument("--max-k", type=_non_negative_int, default=3)
    demo.set_defaults(func=command_demo)

    validate = sub.add_parser("validate", help="random correctness check vs brute force")
    validate.add_argument("--cases", type=_positive_int, default=200)
    validate.add_argument("--seed", type=int, default=0)
    validate.set_defaults(func=command_validate)

    bench = sub.add_parser("bench", help="run the benchmark suite")
    bench.add_argument("--repeats", type=_positive_int, default=5)
    bench.add_argument("--output", default="results/benchmark_raw.csv")
    bench.set_defaults(func=command_bench)

    analyze = sub.add_parser("analyze", help="generate figures and tables")
    analyze.add_argument("--input", default="results/benchmark_raw.csv")
    analyze.add_argument("--outdir", default="results")
    analyze.set_defaults(func=command_analyze)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
