# Approximate String Matching — Algorithms, Analysis, and Experiments

Python implementations and experiments for:

> **Design, Analysis, and Experimental Comparison of Algorithms for Approximate String Matching**

Given a text `T`, a pattern `P`, and a maximum edit distance `k`, the project finds every text position at which a substring matches `P` with at most `k` Levenshtein edits. It also compares the algorithms in time, memory, correctness, and behaviour as `n`, `m`, and `k` change.

## Implemented algorithms

- Naive exact search
- Knuth–Morris–Pratt (KMP)
- Full-matrix Levenshtein distance
- Rolling-row Levenshtein distance
- Banded Levenshtein distance for the string-to-string task
- Sellers' semi-global approximate-search DP (full matrix and rolling rows)
- Correctness-preserving threshold-pruned Sellers search
- Landau–Vishkin diagonal-band search with deterministic LCE queries
- Hamming distance (restricted substitutions-only case)

Every approximate matcher returns `(end, distance)` pairs, where `end` is a **0-based exclusive** end position. Add one for a 1-based ending position. All matchers are exact; no heuristic pruning is used.

## Quick start

```powershell
python -m pytest -q                    # 120 tests
python -m asm.cli demo                 # effect of increasing k
python -m asm.cli search --text ABCXDEFG --pattern ABCDEF --k 1
python -m asm.cli validate --cases 200 # random comparison with brute force
python -m asm.cli distance kitten sitting
```

Example search output:

```text
text length=8 pattern length=6 k=1
algorithm=rolling time=0.025 ms matches=1
  end=    7 (1-based     7)  d=1  before: 'ABCXDEF'
```

## Reproduction

Install the analysis dependencies (the core algorithms use only the Python standard library):

```powershell
python -m pip install -r requirements.txt
```

Run the full experimental pipeline:

```powershell
python scripts/run_experiments.py
```

This runs the tests, three independent benchmark suites, combines repeated runs, and regenerates all figures and tables. It takes several minutes. To run a single suite:

```powershell
python -m asm.cli bench --repeats 5
python -m asm.cli analyze
```

Outputs:

| Path | Contents |
|---|---|
| `results/benchmark_raw.csv` | combined benchmark measurements |
| `results/benchmark_run*.csv` | individual benchmark suites |
| `results/analysis.md` | generated tables |
| `results/figures/` | all plots |
| `docs/REPORT.md` | full report with theory, pseudocode, correctness, results |
| `docs/PRESENTATION.md` | slide deck source |
| `docs/presentation.html` | standalone presentation |
| `docs/PLAN_COVERAGE.md` | checklist mapping the original project plan to files |
| `docs/TEST_PLAN.md` | complete testing plan |
| `docs/TEST_REPORT.md` | executed test results and issues fixed |
| `tests/test_algorithms.py` | unit, property, and exhaustive tests |
| `tests/test_production_contracts.py` | contracts, generator, CLI, benchmark/analysis integration |

## Project structure

```text
asm/
  algorithms.py     # all matching and distance implementations
  lce.py            # suffix array, LCP, RMQ, O(1) LCE
  models.py         # Match interface and normalisation
  reference.py      # brute-force reference and validation helpers
  generator.py      # random, planted, repetitive, adversarial datasets
  benchmark.py      # benchmark runner
  analysis.py       # figures and markdown tables
  cli.py            # command-line interface
tests/
  test_algorithms.py
  test_production_contracts.py
scripts/
  run_experiments.py
  combine_benchmarks.py
  stress_test.py
data/
  sample_dna.txt
  sample_english.txt
results/
  ...
docs/
  REPORT.md
  PRESENTATION.md
  presentation.html
  PLAN_COVERAGE.md
  TEST_PLAN.md
  TEST_REPORT.md
```

## Key results

These are representative measurements on an AMD Ryzen 7 7840HS / Windows 11 / Python 3.14 machine. See the report for the full tables.

- **Rolling rows** reduce peak memory by about **40×** at `n = 4000, m = 80` while leaving time unchanged.
- **Banded edit distance** is **7–129×** faster than full distance when the true distance is small (length 1000, `k = 1..32`).
- **Threshold pruning** is fastest for small `k` and long patterns, but becomes slower than plain DP on repetitive text and for large `k`.
- **Landau–Vishkin** is almost independent of pattern length for fixed `n`, `k`, and handles repetitive text well, but pays suffix-array preprocessing and a reporting overhead.
- **KMP is about 189× faster** than rolling Sellers at `k = 0` on the tested case.
- A fixed `|i-j| <= k` band is **not** correct for semi-global search; the project explains this and uses banding only for global distance, with safe alternatives for search.

## Correctness

The test suite compares every search implementation against brute force on:

- curated cases;
- exhaustive binary strings with `n < 6`, `m < 4`, and `k < 4`;
- randomized binary, DNA, English-like, and Unicode inputs;
- structural and CLI contracts;
- generator ground truth and benchmark/analysis smoke tests.

All 120 tests pass. Every reported distance is the exact minimum for that end position under unit-cost Levenshtein distance. See `docs/TEST_PLAN.md` for the full plan and `docs/TEST_REPORT.md` for the executed results.

For the larger stress/soak run:

```powershell
python scripts/stress_test.py
```

## Notes on design

- The algorithms are implemented from scratch; pandas, matplotlib, and tabulate are used only for analysis and plots.
- The empty pattern matches every end position `0..n`; a non-empty pattern never matches the empty substring.
- The Landau–Vishkin implementation uses a deterministic suffix-array LCE structure rather than a probabilistic rolling hash.
- Benchmark times are per-call medians from batched, interleaved rounds; the final CSV uses the lower envelope of three independent suites to reduce shared-machine noise.
