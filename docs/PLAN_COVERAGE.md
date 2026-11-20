# Plan coverage checklist

| Plan item | Status | Where |
|---|---|---|
| Precise problem definition and end-position convention | done | `README.md`, `docs/REPORT.md` §1 |
| Common interface `approximateSearch(text, pattern, k)` | done | `asm/models.py`, `asm/algorithms.py` |
| KMP / naive baseline for `k = 0` | done | `asm/algorithms.py`, `tests/test_algorithms.py` |
| Full Levenshtein DP | done | `asm/algorithms.py` |
| Space-optimised rolling Levenshtein | done | `asm/algorithms.py` |
| Sellers' approximate-search DP | done | `asm/algorithms.py` |
| Banded DP | done for string-to-string distance; unsafe fixed band documented for search | `asm/algorithms.py`, report §2.6/§2.8 |
| Safe search improvement for small `k` | threshold-pruned Sellers and Landau–Vishkin | `asm/algorithms.py` |
| Myers bit-parallel extension | listed as possible extension, not required by the minimum viable scope | report §10 |
| Hamming distance discussion | done | `asm/algorithms.py`, report §2.9 |
| Recurrences, pseudocode, proofs, complexity | done | report §2–3 and appendices |
| Sellers initialisation explanation and `k = 0` equivalence | done | report §2.4 |
| Data generator and planted mutations | done | `asm/generator.py` |
| Brute-force reference and validator | done | `asm/reference.py` |
| Edge cases: empty, longer pattern, no match, overlapping, repetitive, alphabets | done | `tests/test_algorithms.py` |
| Correctness tests and exhaustive small inputs | done; 120 tests | `tests/test_algorithms.py`, `tests/test_production_contracts.py` |
| Benchmark runner with timing and memory | done | `asm/benchmark.py` |
| Text length, pattern length, `k`, alphabet, adversarial parameters | done | `asm/benchmark.py`, `results/` |
| Runtime/memory tables and graphs | done | `results/analysis.md`, `results/figures/` |
| Accuracy / precision-recall discussion | done | report §4 |
| Limitations and improvements | done | report §8, §10 |
| Demo showing effect of increasing `k` | done | `python -m asm.cli demo`, `results/demo_output.txt` |
| Reproduction instructions | done | `README.md`, `scripts/run_experiments.py` |
| Final report and presentation | done | `docs/REPORT.md`, `docs/PRESENTATION.md`, `docs/presentation.html` |
| Test plan and execution report | done; 120 tests plus stress and pipeline checks | `docs/TEST_PLAN.md`, `docs/TEST_REPORT.md` |

## Important technical note

The plan suggested banded DP as the main search improvement. A fixed band
`|i-j| <= k` is correct for **global** edit distance but not for **semi-global**
substring search, because a valid match may begin far from the main diagonal.
This project therefore:

1. uses banded DP only for the string-to-string distance task;
2. implements threshold-pruned Sellers for safe cell pruning in search;
3. implements Landau–Vishkin diagonal states with LCE for a parameter-sensitive
   search algorithm that remains correct.

This distinction is explained in the report and is one of the project's main
findings rather than a silent shortcut.
