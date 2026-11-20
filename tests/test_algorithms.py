"""Unit, property, and regression tests for the approximate matchers."""

from __future__ import annotations

import random

import pytest

from asm.algorithms import (
    hamming_distance,
    kmp_exact,
    landau_vishkin_search,
    levenshtein_banded,
    levenshtein_full,
    levenshtein_rolling,
    naive_exact,
    sellers_full,
    sellers_pruned,
    sellers_rolling,
)
from asm.generator import (
    english_dataset,
    mutate,
    planted_dataset,
    prefix_trap_dataset,
    random_dataset,
    repetitive_dataset,
)
from asm.lce import SuffixArrayLCE, naive_lce
from asm.models import as_dict, normalise
from asm.reference import (
    brute_force_search,
    compare_to_reference,
    validate_structure,
)

SEARCHES = [
    sellers_full,
    sellers_rolling,
    sellers_pruned,
    landau_vishkin_search,
]


# ---------------------------------------------------------------------------
# Distances
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "distance"),
    [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("kitten", "sitting", 3),
        ("flaw", "lawn", 2),
        ("same", "same", 0),
        ("abc", "abc", 0),
    ],
)
def test_levenshtein_known(a: str, b: str, distance: int) -> None:
    assert levenshtein_full(a, b) == distance
    assert levenshtein_rolling(a, b) == distance
    assert levenshtein_banded(a, b, distance) == distance
    if distance > 0:
        assert levenshtein_banded(a, b, distance - 1) == distance


def test_hamming() -> None:
    assert hamming_distance("karolin", "kathrin") == 3
    assert hamming_distance("abc", "abc") == 0
    assert hamming_distance("abc", "ab") is None


def test_banded_against_rolling_random() -> None:
    rng = random.Random(11)
    for _ in range(500):
        a = "".join(rng.choice("abc") for _ in range(rng.randint(0, 18)))
        b = "".join(rng.choice("abc") for _ in range(rng.randint(0, 18)))
        k = rng.randint(0, 8)
        exact = levenshtein_rolling(a, b)
        expected = exact if exact <= k else k + 1
        assert levenshtein_banded(a, b, k) == expected


# ---------------------------------------------------------------------------
# Exact baselines
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "pattern"),
    [
        ("", ""),
        ("abc", ""),
        ("abc", "abc"),
        ("abc", "d"),
        ("aaaa", "aa"),
        ("abababa", "aba"),
        ("ABCXDEFG", "ABCDEF"),
    ],
)
def test_exact_baselines(text: str, pattern: str) -> None:
    expected = as_dict(naive_exact(text, pattern))
    assert as_dict(kmp_exact(text, pattern)) == expected
    assert as_dict(sellers_rolling(text, pattern, 0)) == expected
    assert as_dict(sellers_pruned(text, pattern, 0)) == expected
    assert as_dict(landau_vishkin_search(text, pattern, 0)) == expected


# ---------------------------------------------------------------------------
# Search algorithms versus brute force
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("algorithm", SEARCHES)
@pytest.mark.parametrize(
    ("text", "pattern", "k"),
    [
        ("", "", 0),
        ("", "abc", 1),
        ("abc", "", 2),
        ("abc", "abcdef", 3),
        ("abcdef", "abcdef", 0),
        ("abcdef", "abcdeg", 1),
        ("ABCXDEFG", "ABCDEF", 1),
        ("abc", "abc", 5),  # every end position is a match
        ("aaaaaa", "aaa", 1),
        ("abababa", "aba", 1),
        ("acgtacgt", "acgta", 1),
        ("xyz", "abc", 2),
        ("mississippi", "mss", 2),
        ("hello world", "world", 1),
    ],
)
def test_curated_cases(text: str, pattern: str, k: int, algorithm) -> None:
    ok, detail = compare_to_reference(algorithm, text, pattern, k)
    assert ok, detail
    validate_structure(algorithm(text, pattern, k), len(text), k)


@pytest.mark.parametrize("algorithm", SEARCHES)
def test_random_small_against_brute_force(algorithm) -> None:
    rng = random.Random(1234)
    for _ in range(250):
        alphabet = rng.choice(["ab", "abc", "ACGT"])
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
        pattern = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 8)))
        k = rng.randint(0, 5)
        ok, detail = compare_to_reference(algorithm, text, pattern, k)
        assert ok, f"text={text!r} pattern={pattern!r} k={k}: {detail}"


def test_exhaustive_binary_tiny() -> None:
    from itertools import product

    for n in range(0, 6):
        for text_tuple in product("ab", repeat=n):
            text = "".join(text_tuple)
            for m in range(0, 4):
                for pattern_tuple in product("ab", repeat=m):
                    pattern = "".join(pattern_tuple)
                    for k in range(0, 4):
                        expected = as_dict(brute_force_search(text, pattern, k))
                        for algorithm in SEARCHES:
                            assert as_dict(algorithm(text, pattern, k)) == expected


def test_edit_types_are_found() -> None:
    pattern = "ACGTAC"
    # substitution
    text = "ACGAAC"
    for algorithm in SEARCHES:
        assert 6 in as_dict(algorithm(text, pattern, 1))
    # insertion into text
    text = "ACGTTAC"
    for algorithm in SEARCHES:
        assert 7 in as_dict(algorithm(text, pattern, 1))
    # deletion from text
    text = "ACGAC"
    for algorithm in SEARCHES:
        assert 5 in as_dict(algorithm(text, pattern, 1))


def test_pattern_longer_than_text() -> None:
    for algorithm in SEARCHES:
        matches = as_dict(algorithm("ABC", "ABCDEF", 2))
        assert 3 not in matches  # needs 3 deletions
        matches = as_dict(algorithm("ABC", "ABCDEF", 3))
        assert matches[3] == 3


def test_empty_pattern_matches_every_end() -> None:
    for algorithm in SEARCHES:
        assert as_dict(algorithm("abc", "", 2)) == {0: 0, 1: 0, 2: 0, 3: 0}


def test_no_match() -> None:
    for algorithm in SEARCHES:
        assert as_dict(algorithm("xyzxyz", "abc", 2)) == {}


# ---------------------------------------------------------------------------
# Landau-Vishkin and LCE details
# ---------------------------------------------------------------------------


def test_lce_matches_naive() -> None:
    rng = random.Random(9)
    for _ in range(100):
        pattern = "".join(rng.choice("abc") for _ in range(rng.randint(0, 15)))
        text = "".join(rng.choice("abc") for _ in range(rng.randint(0, 15)))
        lce = SuffixArrayLCE.build(pattern, text)
        for i in range(len(pattern) + 1):
            for j in range(len(text) + 1):
                assert lce.lce(i, j) == naive_lce(pattern, text, i, j)


def test_landau_vishkin_naive_and_suffix_array_agree() -> None:
    rng = random.Random(17)
    for _ in range(100):
        text = "".join(rng.choice("abcd") for _ in range(rng.randint(0, 20)))
        pattern = "".join(rng.choice("abcd") for _ in range(rng.randint(0, 10)))
        k = rng.randint(0, 5)
        a = as_dict(landau_vishkin_search(text, pattern, k, use_naive_lce=True))
        b = as_dict(landau_vishkin_search(text, pattern, k))
        assert a == b


def test_landau_vishkin_larger_planted() -> None:
    ds = planted_dataset(1000, 60, 8, "dna", seed=21)
    expected = as_dict(sellers_rolling(ds.text, ds.pattern, ds.k))
    assert as_dict(landau_vishkin_search(ds.text, ds.pattern, ds.k)) == expected


# ---------------------------------------------------------------------------
# Data generators and structural properties
# ---------------------------------------------------------------------------


def test_normalise_keeps_minimum_distance() -> None:
    from asm.models import Match

    matches = [Match(5, 2), Match(3, 1), Match(5, 1), Match(3, 2)]
    assert normalise(matches) == [Match(3, 1), Match(5, 1)]


def test_planted_mode_contains_requested_upper_bounds() -> None:
    ds = planted_dataset(500, 40, 3, "dna", seed=5, copies=5)
    assert ds.planted
    for plant in ds.planted:
        pattern = ds.pattern
        substring = ds.text[plant.start : plant.end]
        distance = levenshtein_rolling(pattern, substring)
        assert distance <= plant.requested_edits


def test_generator_inputs_are_supported() -> None:
    datasets = [
        random_dataset(200, 20, 2, "binary", seed=1),
        english_dataset(200, 20, 2, seed=2),
        repetitive_dataset(200, 20, 2),
        prefix_trap_dataset(200, 20, 2),
        planted_dataset(200, 20, 2, "english", seed=3),
    ]
    for ds in datasets:
        for algorithm in SEARCHES:
            matches = algorithm(ds.text, ds.pattern, ds.k)
            validate_structure(matches, len(ds.text), ds.k)


def test_mutate_returns_expected_lengths() -> None:
    rng = random.Random(3)
    pattern = "ACGT"
    assert len(mutate(pattern, 1, "ACGT", rng, "substitution")) == len(pattern)
    assert len(mutate(pattern, 1, "ACGT", rng, "insertion")) == len(pattern) + 1
    assert len(mutate(pattern, 1, "ACGT", rng, "deletion")) == len(pattern) - 1
