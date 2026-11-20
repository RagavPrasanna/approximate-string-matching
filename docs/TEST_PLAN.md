# Test Plan — Approximate String Matching

This plan covers correctness, structural contracts, generators, command-line
behaviour, benchmarks, analysis, reproduction, and optional stress testing.

## 1. Objectives

1. Confirm exact Levenshtein distances and band outcomes.
2. Confirm that every search algorithm reports exactly the brute-force set of
   end positions and minimum distances.
3. Confirm `k = 0` matches KMP exactly.
4. Confirm optimized algorithms remain exact: rolling Sellers, threshold
   pruning, and Landau–Vishkin.
5. Confirm edge cases and data-generation ground truth.
6. Confirm CLI and pipeline integration.
7. Exercise larger inputs without imposing fragile runtime thresholds.

## 2. Fast correctness suite

Run:

```powershell
python -m pytest
```

### 2.1 Distance tests

- Empty strings, identical strings, one edit of each type.
- Known distances: `kitten/sitting = 3`, `flaw/lawn = 2`.
- Banded distance equals full distance when `d <= k`; returns `k + 1`
  otherwise.
- Negative `k` raises `ValueError`.

### 2.2 Search contract

Every returned match must have:

- `0 <= end <= n`
- `0 <= distance <= k`
- sorted end positions with no duplicates
- minimum distance for that end position

Test against an independent brute-force substring enumeration.

### 2.3 Golden cases

- `ABCXDEFG`, `ABCDEF`, `k=0`: no match.
- `ABCXDEFG`, `ABCDEF`, `k=1`: end `7`, distance `1`.
- `XXXXXABC`, `ABC`, `k=0`: end `8`; guards the unsafe fixed-band trap.
- `abababa`, `aba`, `k=0`: overlapping ends `3, 5, 7`.
- Pattern longer than text, empty text, empty pattern, `k` larger than `m`.
- Unicode input.

### 2.4 Exhaustive and randomized comparison

- Exhaustive binary texts `n < 6`, patterns `m < 4`, `k < 4`.
- Existing 250 random cases per algorithm plus 300 extended-fuzz cases.
- Compare full Sellers, rolling Sellers, pruned Sellers, and Landau–Vishkin.
- Verify KMP agreement at `k=0`.

### 2.5 Algorithm-specific checks

- LCE equals a naive longest-common-extension implementation.
- Landau–Vishkin with naive LCE equals Landau–Vishkin with suffix-array LCE.
- Landau–Vishkin agrees with rolling Sellers on larger planted data.
- Pruned Sellers agrees with full Sellers on small and medium random data.
- Rolling and full Sellers agree on all random cases.

## 3. Generator tests

- Same seed gives identical datasets.
- `random_dataset`, `repetitive_dataset`, and `english_dataset` honor `n` and `m`.
- Every planted span is disjoint.
- Every planted witness has distance at most its requested number of edits.
- `mutate_once` changes distance by exactly one for substitution, insertion,
  and deletion when the operation is possible.
- Multi-character repetitive patterns preserve exact lengths.

## 4. CLI and integration tests

```powershell
python -m asm.cli search --text ABCXDEFG --pattern ABCDEF --k 1 --algorithm rolling
python -m asm.cli search --text-file data/sample_dna.txt --pattern GATTACAGATTACA --k 1 --algorithm lv
python -m asm.cli distance kitten sitting
python -m asm.cli demo
python -m asm.cli validate --cases 500
```

Also test:

- all search algorithm names
- negative `k`: clean argument error, exit code 2, no traceback
- missing text file: clean error, no traceback
- benchmark writer smoke
- `combine_benchmarks.py` lower-envelope behaviour
- analysis smoke: `analysis.md` and at least one figure are created

## 5. Benchmark and reproduction checks

```powershell
python -m asm.cli bench --repeats 1 --output results/test_plan_benchmark.csv
python -m asm.cli analyze --input results/test_plan_benchmark.csv --outdir results/test_plan_analysis
python scripts/run_experiments.py --skip-tests --runs 1 --repeats 1
```

Check:

- no benchmark rows with `status != ok`
- positive runtimes and memory readings
- correct match counts
- all reported figures generated
- deterministic dataset seeds and documented conventions

Performance assertions should be limited to completion, correctness, stability
of ordering, and broad growth trends. Exact timings are machine-dependent.

## 6. Stress/soak tests

```powershell
python scripts/stress_test.py
```

Cases:

- `n = 10,000`, `m = 10`, `k = 0` (exact baseline)
- `n = 50,000`, `m = 100`, `k = 3`
- `n = 100,000`, `m = 10`, `k = 2`
- `n = 20,000`, `m = 1,000`, `k = 2`
- unary repetitive text, `n = 50,000`, `m = 100`, `k = 3`

Acceptance:

- all search algorithms agree
- KMP agrees at `k = 0`
- no crashes
- rolling-row peak memory is below full-matrix peak memory
- output is written to `results/test_plan_stress.txt`

## 7. Acceptance criteria

The plan passes when:

- all pytest tests pass;
- `validate --cases 500` completes with no mismatch;
- golden outputs are correct;
- all benchmark smoke rows are successful;
- analysis regenerates tables and figures;
- stress checks complete with agreement between exact implementations;
- generator witnesses have no overlaps and no ground-truth violations.
