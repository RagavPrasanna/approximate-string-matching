# Test Execution Report

**Project:** Design, Analysis, and Experimental Comparison of Algorithms for Approximate String Matching  
**Date:** 14 November 2026  
**Machine:** AMD Ryzen 7 7840HS, Windows 11, Python 3.14.4  
**Plan:** `docs/TEST_PLAN.md`

---

## 1. Summary

| Check | Result |
|---|---|
| Fast automated suite | **120 passed** in 6.05 s |
| Random validation | **2,000 algorithm/case comparisons**, no mismatch |
| Extended fuzz | 300 random cases × 4 algorithms, no mismatch |
| Generator audit | **30,898 planted witnesses, 0 failures, 0 overlaps** |
| CLI matrix | All tested commands and error paths passed |
| Benchmark smoke | **121 rows, 0 failed rows** |
| Analysis smoke | `analysis.md` and **10 figures** generated |
| End-to-end pipeline smoke | One full suite completed and regenerated all outputs |
| Stress/soak | Agreement on inputs up to **n = 100,000** and **m = 1,000** |

**Verdict: the test plan passes.** No correctness discrepancy remains in the
tested scope.

---

## 2. Fast test suite

Command:

```powershell
python -m pytest
```

Result:

```text
120 passed in 6.05s
```

Raw output: `results/test_plan_pytest.txt`.

The suite includes the original algorithm tests and the new production-contract
tests:

- distances and banded distance;
- Sellers full/rolling/pruned search;
- Landau–Vishkin with both naive and suffix-array LCE;
- exhaustive binary small inputs;
- randomized and curated cases;
- negative thresholds;
- sorted/no-duplicate/minimum-distance output contract;
- the `XXXXXABC / ABC` banding trap;
- Unicode input;
- generator determinism, lengths, disjoint planted spans, and ground truth;
- benchmark writer, run-combining script, and analysis smoke tests;
- CLI search, file input, distance, demo, validation, and clean errors.

---

## 3. Random validation

Command:

```powershell
python -m asm.cli validate --cases 500
```

Result:

```text
OK: 2000 algorithm/case comparisons against brute force
```

Every comparison used all four exact implementations: full Sellers, rolling
Sellers, threshold-pruned Sellers, and Landau–Vishkin.

The automated suite additionally includes a 300-case extended fuzz test over
binary, DNA, and larger alphabets.

---

## 4. Golden cases

| Case | Expected | Result |
|---|---|---|
| `ABCXDEFG`, `ABCDEF`, `k=0` | no matches | pass |
| `ABCXDEFG`, `ABCDEF`, `k=1` | end 7, distance 1 | pass |
| `XXXXXABC`, `ABC`, `k=0` | end 8, distance 0 | pass |
| `abababa`, `aba`, `k=0` | ends 3, 5, 7 | pass |
| Unicode text and pattern | matches brute force | pass |
| Empty text/pattern and pattern longer than text | correct edge behavior | pass |
| `k` larger than pattern length | all qualifying ends with correct minimum distances | pass |

---

## 5. Generator audit

The generator was audited over:

- 5 text lengths;
- 5 pattern lengths;
- 4 thresholds;
- 50 seeds per combination;
- 10 requested copies per dataset.

Result:

```text
datasets=5000 planted_spans=30898 witness_failures=0 overlaps=0 datasets_without_fit=600
```

Raw output: `results/test_plan_generator_audit.txt`.

The 600 datasets without a planted witness are all cases where the requested
pattern was longer than the text (`n = 20, 50, or 100`, `m = 80`). No witness
was expected there.

### Issue found and fixed

The original generator could place planted copies on overlapping spans. A later
copy could overwrite part of an earlier copy, invalidating the earlier ground
truth record. The generator now skips a copy if its span would overlap an
existing planted span. For all benchmark cases used by the project there was no
overlap, so the existing measurements remain reproducible.

An audit found this concretely, for example a 3-character pattern planted on a
20-character text with 10 requested copies. After the fix, all 30,898 retained
witnesses satisfy `distance(pattern, planted_span) <= requested_edits`.

---

## 6. CLI and integration checks

Executed commands and behaviours:

| Check | Result |
|---|---|
| `search` with `full`, `rolling`, `pruned`, `lv`, `kmp` | pass |
| `search --text-file` with sample data | pass |
| `distance kitten sitting --k 2` | full/rolling/banded all report 3 |
| `demo` | pass |
| `validate --cases 500` | 2,000 comparisons pass |
| negative `--k` | clean argument error, exit code 2, no traceback |
| missing text file | clean error, exit code 1, no traceback |
| `bench --repeats 1` | pass, 121 rows |
| `analyze` on smoke benchmark | 10 figures and `analysis.md` |

### Issue found and fixed

A negative `--k` previously produced a Python traceback and exit code 1. It is
now validated by `argparse`; the command prints a concise usage error and exits
with code 2. Missing text files are also reported cleanly instead of raising a
traceback.

---

## 7. Benchmark smoke test

Command:

```powershell
python -m asm.cli bench --repeats 1 --output results/test_plan_benchmark.csv
```

Result:

- 121 case/algorithm rows;
- 0 rows with `status != ok`;
- all timings and memory measurements finite and positive;
- output: `results/test_plan_benchmark.csv`.

Analysis smoke:

```powershell
python -m asm.cli analyze --input results/test_plan_benchmark.csv --outdir results/test_plan_analysis
```

Result:

- `results/test_plan_analysis/analysis.md` created;
- 10 PNG figures created;
- smallest figure size 47,004 bytes.

The existing final benchmark artifacts in `results/benchmark_raw.csv` and
`results/figures/` were left unchanged.

---

## 8. End-to-end reproducibility smoke

Command:

```powershell
python scripts/run_experiments.py --skip-tests --runs 1 --repeats 1 --output-dir results/repro_smoke
```

Result:

- benchmark suite completed;
- `results/repro_smoke/benchmark_raw.csv`: 121 rows, 0 failures;
- `results/repro_smoke/analysis.md` created;
- 10 figures created;
- no errors in the pipeline.

This verifies the combined benchmark → combine → analysis path from the current
working tree.

---

## 9. Stress and soak results

Command:

```powershell
python scripts/stress_test.py
```

Raw output: `results/test_plan_stress.txt`.

| Case | n | m | k | Full | Rolling | Pruned | Landau–Vishkin | Matches |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Exact small pattern | 10,000 | 10 | 0 | 0.016 s | 0.016 s | 0.017 s | 0.046 s | 333 |
| Medium | 50,000 | 100 | 3 | 0.745 s | 0.721 s | 0.346 s | 0.537 s | 712 |
| Large text | 100,000 | 10 | 2 | 0.156 s | 0.155 s | 0.827 s | 1.931 s | 110 |
| Long pattern | 20,000 | 1,000 | 2 | skipped | 7.508 s | 0.242 s | 0.495 s | 18 |
| Repetitive | 50,000 | 100 | 3 | 1.576 s | 1.592 s | 8.238 s | 1.324 s | 49,904 |

All algorithms agreed on every case. KMP agreed at `k = 0`.

The long-pattern case intentionally omitted the full matrix: `20,000 × 1,000`
cells are not a practical storage choice, while rolling Sellers exercises the
same recurrence.

Peak memory at `n = 50,000`, `m = 100`, `k = 3`:

- full matrix: **39,517.5 KiB**
- rolling rows: **781.3 KiB**

Rolling rows use about 50× less memory in this stress case.

---

## 10. Additional issues found during execution

| Issue | Resolution |
|---|---|
| Planted spans could overlap and invalidate ground truth | disjoint-span check added |
| `english_dataset` could change pattern length after mixed mutations | pattern length now always exactly `m` |
| Negative CLI `--k` printed a traceback | argparse validation added |
| Missing text file printed a traceback | clean `SystemExit` message added |
| Structural validator did not check sorted output | sorted-order assertion added |

The `english_dataset` fix preserves the benchmark seed used in the report; the
pattern for that seed was already length 80, so the reported benchmark inputs
remain unchanged.

---

## 11. Residual notes and limitations

- Timing results are environment-dependent. The stress test is a soak/agreement
  check, not a replacement for the repeated benchmark methodology.
- The optional Myers bit-parallel extension is still not implemented; it remains
  outside the minimum viable project scope.
- The generator intentionally keeps only disjoint planted copies; a caller that
  requests more copies than fit receives fewer witnesses.
- Full-matrix Sellers is skipped for the long-pattern stress case by design to
  avoid an impractical allocation.

---

## 12. Acceptance result

| Acceptance criterion | Status |
|---|---|
| All pytest tests pass | pass |
| `validate --cases 500` has no mismatch | pass |
| Golden cases correct | pass |
| Benchmark rows all successful | pass |
| Analysis tables and figures generated | pass |
| Stress cases agree across implementations | pass |
| Generator witnesses valid and disjoint | pass |
| CLI error paths clean | pass |
| End-to-end pipeline reproducible | pass |

**Test plan execution completed successfully.**
