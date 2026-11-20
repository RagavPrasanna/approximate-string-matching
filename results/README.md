# Results

Generated on the machine described in `docs/REPORT.md`.

- `benchmark_raw.csv` — final combined measurements used by the report.
- `benchmark_raw.meta.json` — combination method and source files.
- `benchmark_run1.csv`, `benchmark_run2.csv`, `benchmark_run3.csv` — individual
  benchmark suite runs.
- `analysis.md` — automatically generated tables.
- `figures/` — plots used in the report and slides.
- `demo_output.txt` — a sample run of `python -m asm.cli demo`.
- `test_plan_pytest.txt` — full test-suite result.
- `test_plan_generator_audit.txt` — planted-witness audit.
- `test_plan_benchmark.csv` — benchmark smoke run.
- `test_plan_analysis/` — analysis smoke output.
- `test_plan_stress.txt` — large-input stress results.
- `repro_smoke/` — one-run end-to-end pipeline check.

The final CSV uses the lower envelope across three independent suites. Within
each suite, algorithms were timed in interleaved, batched rounds and the value
recorded is a per-call median. This makes the comparison less sensitive to
background load and thermal drift on a laptop.
