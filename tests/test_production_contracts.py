"""Production-contract, integration, generator, and CLI tests.

These supplement the core algorithm tests with the checks from the project test
plan: refusal of invalid thresholds, the semi-global banding trap, generator
ground truth, structural output guarantees, benchmark/analysis smoke tests, and
command-line behaviour.
"""

from __future__ import annotations

import csv
import random
import subprocess
import sys
from pathlib import Path

import pytest

from asm.algorithms import (
    kmp_exact,
    landau_vishkin_search,
    levenshtein_banded,
    sellers_full,
    sellers_pruned,
    sellers_rolling,
)
from asm.benchmark import Algorithm, Writer, run_search_case
from asm.analysis import main as analysis_main
from asm.generator import (
    Dataset,
    english_dataset,
    mutate,
    mutate_once,
    planted_dataset,
    random_dataset,
    repetitive_dataset,
)
from asm.models import Match, as_dict, normalise
from asm.reference import brute_force_search, validate_structure

ROOT = Path(__file__).resolve().parents[1]
SEARCHES = [sellers_full, sellers_rolling, sellers_pruned, landau_vishkin_search]


# ---------------------------------------------------------------------------
# Invalid thresholds and structural contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "search",
    SEARCHES,
)
def test_negative_k_is_rejected(search) -> None:
    with pytest.raises(ValueError):
        search("abc", "abc", -1)


def test_banded_distance_rejects_negative_k() -> None:
    with pytest.raises(ValueError):
        levenshtein_banded("abc", "abd", -1)


def test_validate_structure_rejects_unsorted_or_bad_output() -> None:
    with pytest.raises(AssertionError, match="sorted"):
        validate_structure([Match(5, 0), Match(3, 0)], n=5, k=0)
    with pytest.raises(AssertionError, match="outside text"):
        validate_structure([Match(8, 0)], n=5, k=0)
    with pytest.raises(AssertionError, match="outside threshold"):
        validate_structure([Match(3, 2)], n=5, k=1)
    with pytest.raises(AssertionError, match="duplicate"):
        validate_structure([Match(3, 0), Match(3, 0)], n=5, k=0)


def test_normalise_sorts_and_keeps_minimum_distance() -> None:
    matches = [Match(5, 2), Match(3, 1), Match(5, 1), Match(3, 2)]
    assert normalise(matches) == [Match(3, 1), Match(5, 1)]


# ---------------------------------------------------------------------------
# Golden cases from the plan
# ---------------------------------------------------------------------------


def test_golden_example() -> None:
    text, pattern = "ABCXDEFG", "ABCDEF"
    for search in SEARCHES:
        assert as_dict(search(text, pattern, 0)) == {}
        assert as_dict(search(text, pattern, 1)) == {7: 1}


def test_far_from_main_diagonal_golden_case() -> None:
    """A fixed global band would miss this occurrence; every safe matcher must
    report it."""

    for search in SEARCHES:
        assert as_dict(search("XXXXXABC", "ABC", 0)) == {8: 0}


def test_matches_are_sorted_and_distance_minimal() -> None:
    text = "ACGTACGTACGT"
    pattern = "ACGTT"
    expected = as_dict(brute_force_search(text, pattern, 2))
    for search in SEARCHES:
        matches = search(text, pattern, 2)
        validate_structure(matches, len(text), 2)
        assert as_dict(matches) == expected


def test_overlapping_matches_are_retained() -> None:
    for search in SEARCHES:
        assert as_dict(search("abababa", "aba", 0)) == {3: 0, 5: 0, 7: 0}


def test_unicode_text_and_lce() -> None:
    text = "αβγδεζηθ"
    pattern = "αβδ"
    expected = as_dict(brute_force_search(text, pattern, 1))
    for search in SEARCHES:
        assert as_dict(search(text, pattern, 1)) == expected
    assert as_dict(kmp_exact(text, "γδε")) == {5: 0}


def test_edit_operations_individually() -> None:
    pattern = "ACGTAC"
    cases = {
        "ACGAAC": 1,  # substitution
        "ACGTTAC": 1,  # insertion into the text-side match
        "ACGAC": 1,  # deletion from the text-side match
    }
    for text, k in cases.items():
        for search in SEARCHES:
            assert len(text) in as_dict(search(text, pattern, k))


def test_all_thresholds_large_k() -> None:
    for search in SEARCHES:
        actual = as_dict(search("ACGT", "ACGT", 99))
        expected = as_dict(brute_force_search("ACGT", "ACGT", 99))
        assert actual == expected == {1: 3, 2: 2, 3: 1, 4: 0}


# ---------------------------------------------------------------------------
# Additional fuzz coverage
# ---------------------------------------------------------------------------


def test_extended_random_fuzz_against_brute_force() -> None:
    rng = random.Random(20261114)
    for _ in range(300):
        alphabet = rng.choice(["ab", "abc", "ACGT", "abcdefgh"])
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 16)))
        pattern = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 10)))
        k = rng.randint(0, 7)
        expected = as_dict(brute_force_search(text, pattern, k))
        for search in SEARCHES:
            actual = search(text, pattern, k)
            validate_structure(actual, len(text), k)
            assert as_dict(actual) == expected, (
                f"{search.__name__} text={text!r} pattern={pattern!r} k={k}"
            )


# ---------------------------------------------------------------------------
# Generator ground truth and contracts
# ---------------------------------------------------------------------------


def test_generated_dataset_lengths_and_determinism() -> None:
    for m in (0, 1, 10, 80):
        for k in (0, 1, 2, 3, 5):
            first = english_dataset(300, m, k, seed=123)
            second = english_dataset(300, m, k, seed=123)
            assert first == second
            assert len(first.text) == 300
            assert len(first.pattern) == m

    exact_cases = [
        (random_dataset(200, 20, 2, "binary", seed=1), 200, 20),
        (repetitive_dataset(200, 20, 2), 200, 20),
        (repetitive_dataset(201, 21, 2, char="AC"), 201, 21),
        (planted_dataset(200, 20, 2, "dna", seed=2), 200, 20),
    ]
    for ds, expected_text_length, expected_pattern_length in exact_cases:
        assert len(ds.text) == expected_text_length
        assert len(ds.pattern) == expected_pattern_length


def test_planted_copies_are_disjoint_and_ground_truth_valid() -> None:
    for n, m, k, copies in (
        (20, 3, 0, 10),
        (50, 10, 3, 10),
        (120, 20, 5, 10),
        (500, 40, 3, 10),
    ):
        for seed in range(10):
            ds = planted_dataset(n, m, k, "dna", seed=seed, copies=copies)
            spans = sorted((p.start, p.end) for p in ds.planted)
            for (_, left_end), (right_start, _) in zip(spans, spans[1:]):
                assert left_end <= right_start, f"overlap in {ds.name} seed={seed}"
            for plant in ds.planted:
                substring = ds.text[plant.start : plant.end]
                distance = levenshtein_banded(
                    ds.pattern, substring, max(k, len(ds.pattern) + len(substring))
                )
                assert distance <= plant.requested_edits


def test_mutate_once_is_one_unit_away_when_operation_possible() -> None:
    rng = random.Random(7)
    for _ in range(200):
        pattern = "".join(rng.choice("ACGT") for _ in range(rng.randint(1, 10)))
        for edit_type in ("substitution", "insertion", "deletion"):
            mutated = mutate_once(pattern, "ACGT", rng, edit_type)
            exact = levenshtein_banded(
                pattern, mutated, max(len(pattern), len(mutated)) + 2
            )
            assert exact == 1


def test_mutate_cycles_edits_and_deletion_on_empty_is_noop() -> None:
    rng = random.Random(3)
    assert len(mutate("ACGT", 1, "ACGT", rng, "substitution")) == 4
    assert len(mutate("ACGT", 1, "ACGT", rng, "insertion")) == 5
    assert len(mutate("ACGT", 1, "ACGT", rng, "deletion")) == 3
    assert mutate_once("", "ACGT", rng, "deletion") == ""


# ---------------------------------------------------------------------------
# Benchmark and analysis smoke tests
# ---------------------------------------------------------------------------


def test_benchmark_writer_smoke(tmp_path: Path) -> None:
    output = tmp_path / "smoke.csv"
    writer = Writer(output)
    dataset = Dataset(
        name="smoke-dna",
        text="ACGTACGTACGT",
        pattern="ACGT",
        k=1,
        alphabet="dna",
    )
    run_search_case(
        writer,
        "smoke",
        dataset,
        [Algorithm("rolling", "Sellers rolling rows", sellers_rolling)],
        repeats=1,
    )
    writer.flush()
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["status"] == "ok"
    assert float(rows[0]["median_ms"]) >= 0
    assert float(rows[0]["peak_kib"]) > 0
    assert int(rows[0]["matches"]) > 0


def test_combine_benchmarks_script(tmp_path: Path) -> None:
    root = tmp_path
    paths = []
    for index, value in enumerate((5.0, 7.0, 6.0)):
        path = root / f"run{index}.csv"
        fields = [
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
            "median_ms",
            "peak_kib",
            "status",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerow(
                {
                    "experiment": "smoke",
                    "case": "case",
                    "dataset": "case",
                    "alphabet": "dna",
                    "n": 10,
                    "m": 2,
                    "k": 0,
                    "algorithm": "rolling",
                    "label": "rolling",
                    "matches": 1,
                    "median_ms": value,
                    "peak_kib": 10,
                    "status": "ok",
                }
            )
        paths.append(path)

    output = tmp_path / "combined.csv"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "combine_benchmarks.py"),
            *map(str, paths),
            "--output",
            str(output),
            "--stat",
            "min",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert float(rows[0]["median_ms"]) == 5.0


def test_analysis_smoke(tmp_path: Path) -> None:
    input_path = tmp_path / "raw.csv"
    fields = [
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
        "median_ms",
        "peak_kib",
        "status",
    ]
    rows = []
    for n in (100, 200):
        for algorithm in ("sellers_full", "sellers_rolling", "sellers_pruned", "landau_vishkin"):
            rows.append(
                {
                    "experiment": "text_length",
                    "case": f"case-n{n}",
                    "dataset": f"case-n{n}",
                    "alphabet": "dna",
                    "n": n,
                    "m": 10,
                    "k": 1,
                    "algorithm": algorithm,
                    "label": algorithm,
                    "matches": 2,
                    "median_ms": float(n) / 100,
                    "peak_kib": float(n),
                    "status": "ok",
                }
            )
    with input_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    outdir = tmp_path / "analysis"
    analysis_main(["--input", str(input_path), "--outdir", str(outdir)])
    assert (outdir / "analysis.md").is_file()
    figure = outdir / "figures" / "runtime_vs_text_length.png"
    assert figure.is_file() and figure.stat().st_size > 0


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def _run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "asm.cli", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    ("algorithm", "k"),
    [("full", "1"), ("rolling", "1"), ("pruned", "1"), ("lv", "1"), ("kmp", "0")],
)
def test_cli_search_algorithms(algorithm: str, k: str) -> None:
    result = _run_cli(
        "search",
        "--text",
        "ABCXDEFG",
        "--pattern",
        "ABCDEF",
        "--k",
        k,
        "--algorithm",
        algorithm,
    )
    assert result.returncode == 0, result.stderr
    assert "matches=" in result.stdout
    assert "Traceback" not in result.stderr


def test_cli_search_from_file(tmp_path: Path) -> None:
    text_file = tmp_path / "input.txt"
    text_file.write_text("XXABCXX", encoding="utf-8")
    result = _run_cli(
        "search",
        "--text-file",
        str(text_file),
        "--pattern",
        "ABC",
        "--k",
        "0",
        "--algorithm",
        "rolling",
    )
    assert result.returncode == 0, result.stderr
    assert "matches=1" in result.stdout
    assert "end=    5" in result.stdout


def test_cli_distance_and_demo() -> None:
    distance = _run_cli("distance", "kitten", "sitting", "--k", "2")
    assert distance.returncode == 0, distance.stderr
    assert "full matrix" in distance.stdout
    assert "3" in distance.stdout

    demo = _run_cli("demo", "--max-k", "1")
    assert demo.returncode == 0, demo.stderr
    assert "k = 0" in demo.stdout
    assert "k = 1" in demo.stdout


def test_cli_validate() -> None:
    result = _run_cli("validate", "--cases", "10")
    assert result.returncode == 0, result.stderr
    assert "OK:" in result.stdout


def test_cli_negative_k_is_a_clean_argument_error() -> None:
    result = _run_cli(
        "search",
        "--text",
        "ABC",
        "--pattern",
        "ABC",
        "--k",
        "-1",
    )
    assert result.returncode == 2
    assert "must be non-negative" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_missing_text_file_is_clean() -> None:
    result = _run_cli(
        "search",
        "--text-file",
        "does-not-exist.txt",
        "--pattern",
        "ABC",
    )
    assert result.returncode == 1
    assert "cannot read text file" in result.stderr
    assert "Traceback" not in result.stderr
