# Results

- Ran WRDS holdout WFV with `configs/wfv_flagship_wrds.yaml` using `WRDS_DATA_ROOT=/srv/data/wrds/wrds`; run_id `2026-01-25T21-01-51Z-4d08d18`.
- Holdout window (2021-01-04 → 2024-12-31) produced **zero trades**; holdout metrics are degenerate and noted in `docs/results_wrds_resume.md` and `project_state/KNOWN_ISSUES.md`.
- Report pipeline completed for the latest run and updated WRDS summaries/analytics:
  - `reports/summaries/wrds_flagship.md`
  - `reports/summaries/wrds_flagship_metrics.json`
  - `reports/summaries/wrds_flagship_spa.json`
  - `reports/summaries/wrds_flagship_spa.md`
  - `reports/summaries/wrds_flagship_factors.md`
  - `docs/results_wrds.md`
  - `docs/results_wrds_resume.md`
- Run artifacts: `artifacts/wrds_flagship/2026-01-25T21-01-51Z-4d08d18/` (manifest, metrics, holdout metrics, trades).

Key headline metrics (WFV OOS context): Sharpe 0.0316 (HAC lags=10), MaxDD 8.33%, CAGR 0.045%, turnover $32.84MM; Reality Check p=0.99595; SPA p=0.015 (status ok).
