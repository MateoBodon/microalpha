# Results

## Summary
- Extracted the best-model holdout metrics from the existing WRDS run (`2026-01-27T04-47-22Z-31fe553`) using SPA + holdout artifacts; no backtest rerun.
- Published resume artifacts: `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/best_model_metrics.json` and `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/best_model_snippet.md`.
- Added ticket/prompt/run-log documentation and updated sprint/progress/changelog entries.

## Details
- SPA best-model id matches holdout selection:
  - `allocator_kwargs={'risk_model': 'equal'}|lookback_months=9|skip_months=1|top_frac=0.2000`
- Best-model holdout metrics (from `holdout_metrics.json`):
  - Sharpe_HAC: 0.1398
  - MaxDD: 3.49%
  - MAR (Calmar): 0.0882
  - Turnover: $5.22MM
- SPA p-value: 0.015 (from `spa.json`)
- RealityCheck p-value: 0.988 (from `metrics.json`)
- Dataset id: `wrds_crsp_export_20251221_v1` (from `manifest.json`)

## Artifacts
- `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/best_model_metrics.json`
- `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/best_model_snippet.md`
- `artifacts/_local/gpt_bundles/gpt_bundle_20260128_005616_ticket-ticket-31.zip`

## Docs
- `docs/tickets/TICKET-31_wrds_best-real-data-resume-line_from_spa.md`
- `docs/prompts/20260128_000243_ticket-31_wrds-best-model-resume-line.md`
- `docs/CODEX_SPRINT_TICKETS.md`
- `PROGRESS.md`
- `CHANGELOG.md`

## Notes
- No new reports or backtests executed; all values are read from existing outputs under `artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/`.
