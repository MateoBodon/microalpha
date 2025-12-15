# Codex Sessions Log

- 2025-11-21 (GPT-5.1-Codex-Max)
  - Tasks: S0 (WRDS docs/notebook refresh), S1 (tighten flagship WRDS risk spec), S2 (add controls + smoke config; rerun TBD).
  - Commands: `pytest -q` (passes; 95 passed, 1 skipped).
  - Notes: Added heat/turnover cap tests and fixed `Portfolio._sized_quantity` to enforce heat caps when `current_time=0`; created `configs/wfv_flagship_wrds_smoke.yaml` for quick validation; WRDS rerun not executed (no `WRDS_DATA_ROOT` locally).
- 2025-11-22 (GPT-5.1-Codex-Max)
  - Tasks: S2 (smoke WFV with tightened caps; full WFV attempts), S3 (notebook visualisations).
  - Commands: `WRDS_CONFIG=configs/wfv_flagship_wrds_smoke.yaml WRDS_DATA_ROOT=/Users/mateobodon/wrds_cache make wfv-wrds` (success, run `2025-11-22T00-21-14Z-c792b44`), three full-run attempts `WRDS_DATA_ROOT=/Users/mateobodon/wrds_cache make wfv-wrds` (timed out at 15m, 30m, 120m; partial artefacts only), notebook edits; no report rerun.
  - Metrics (smoke run): Sharpe_HAC ≈ 0.057, MaxDD ≈ 40.2%, MAR ≈ -0.134, total turnover ≈ $360MM, RC p ≈ 0.745. Drawdown cap now binding vs prior 82% DD.
  - Notes: Full 2005–2024 WFV still pending; requires longer wall-clock execution. Notebook now plots equity+drawdown, rolling Sharpe, and per-fold test metrics while selecting the latest complete run (has `metrics.json`).
