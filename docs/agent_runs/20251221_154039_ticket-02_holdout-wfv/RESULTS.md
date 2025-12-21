# Results

Summary:
- Added holdout support to WFV configs and walk-forward runner, including holdout-only evaluation, selection summary aggregation, and explicit manifest linkage for holdout windows/params.
- Wrote new sample holdout config and updated WRDS configs with holdout ranges; WFV now emits `oos_returns.csv` plus holdout artifacts.
- Added leakage-catching tests for holdout selection and window overlap; fixed WFV fold boundary to prevent holdout overlap.
- Regenerated project_state docs; CURRENT_RESULTS now includes latest sample holdout run.
- Unignored the sample holdout artifact run directory for audit tracking.

Key files changed:
- `.gitignore`
- `src/microalpha/config_wfv.py`
- `src/microalpha/walkforward.py`
- `tests/test_walkforward.py`
- `configs/wfv_flagship_sample_holdout.yaml`
- `configs/wfv_flagship_wrds.yaml`
- `configs/wfv_flagship_wrds_smoke.yaml`
- `tools/render_project_state_docs.py`
- `PROGRESS.md`
- `project_state/CURRENT_RESULTS.md`
- `CHANGELOG.md`

Artifacts generated (sample holdout run):
- Run dir: `artifacts/sample_wfv_holdout/2025-12-21T20-53-05Z-4457b33/`
- Holdout metrics: `artifacts/sample_wfv_holdout/2025-12-21T20-53-05Z-4457b33/holdout_metrics.json`
- Holdout manifest: `artifacts/sample_wfv_holdout/2025-12-21T20-53-05Z-4457b33/holdout_manifest.json`
- Selection summary: `artifacts/sample_wfv_holdout/2025-12-21T20-53-05Z-4457b33/selection_summary.json`
- OOS returns: `artifacts/sample_wfv_holdout/2025-12-21T20-53-05Z-4457b33/oos_returns.csv`

Blocked:
- WRDS holdout smoke/full run skipped: `WRDS_DATA_ROOT` not set.

Notes:
- Selection is aggregated from training-only grid summaries (mean Sharpe), with holdout evaluated once on the chosen params.
