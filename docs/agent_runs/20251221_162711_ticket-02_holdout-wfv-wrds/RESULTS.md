# Results

Summary:
- Located WRDS exports under `/Volumes/Storage/Data/wrds` with expected `crsp`, `meta`, and `universes` paths.
- Ran WRDS holdout-capable smoke WFV; holdout artifacts were written alongside WFV outputs.
- Rendered WRDS smoke report outputs and updated `docs/results_wrds_smoke.md` plus summary assets; regenerated project_state docs.

WRDS run:
- WFV smoke run: `artifacts/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a/`
- Holdout artifacts: `holdout_metrics.json`, `holdout_manifest.json`, `holdout_equity_curve.csv`, `holdout_returns.csv`
- Selection summary: `artifacts/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a/selection_summary.json`
- OOS returns: `artifacts/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a/oos_returns.csv`

Docs/report updates:
- `docs/results_wrds_smoke.md`
- `reports/summaries/wrds_flagship_smoke.md`
- `reports/summaries/wrds_flagship_smoke_factors.md`
- `reports/summaries/wrds_flagship_smoke_metrics.json`
- `docs/img/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a/*`

Notes:
- WRDS raw exports remain local; only derived summaries/images updated.
- No new bundle generated for this follow-up run.
