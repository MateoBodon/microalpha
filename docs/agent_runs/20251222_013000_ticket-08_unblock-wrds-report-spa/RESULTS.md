Summary of changes:
- SPA rendering now returns a structured status, skips invalid comparator stats with a placeholder plot, and records `spa_status`/`spa_skip_reason` in report JSON outputs (`src/microalpha/reporting/wrds_summary.py`).
- Reports now surface a "Run is degenerate" section when zero trades or flat returns are detected (`src/microalpha/reporting/summary.py`, `src/microalpha/reporting/wrds_summary.py`).
- Walk-forward metrics now carry aggregate trade counts/PNL to keep turnover and trade counts consistent, including holdout metrics (`src/microalpha/walkforward.py`).
- Added tests for SPA skip path, degenerate-summary warnings, and turnover/trade invariant (`tests/test_wrds_summary_render.py`, `tests/test_reporting_robustness.py`, `tests/test_walkforward.py`).

Report-only runs (no WRDS exports required):
- `microalpha report --artifact-dir artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e`
  - Summary: `reports/summaries/flagship_mom.md`
  - Plots: `artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/equity_curve.png`, `artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/bootstrap_hist.png`
- `microalpha report --artifact-dir artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7`
  - Summary: `reports/summaries/flagship_mom.md`
  - Plots: `artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/equity_curve.png`, `artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/bootstrap_hist.png`

Notes:
- The prior WRDS SPA failure did not reproduce on report-only runs; SPA skip handling is enforced via unit tests.
- `make report-wrds` was not run (requires `WRDS_DATA_ROOT`).
