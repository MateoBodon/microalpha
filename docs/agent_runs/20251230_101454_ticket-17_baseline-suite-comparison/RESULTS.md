# Results

- Added baseline suite computation with `baselines.csv` + `baselines_status.json` (equal-weight universe, market proxy w/ SPY fallback, 12-1 momentum long-only, cash/RF).
- Summary and WRDS reports now include a Baselines section (Sharpe_HAC/MaxDD/CAGR/turnover table, overlay plot, missing-baseline labels, baselines CSV link).
- Added synthetic tests for lookahead safety and baselines schema stability.
- Generated baseline-enabled sample report: `reports/summaries/flagship_mom.md` with overlay `reports/summaries/flagship_mom_baselines.png`.
- Sample artifacts updated locally with `artifacts/sample_flagship/2025-12-23T21-59-20Z-ba5b480/baselines.csv` + `baselines_status.json` (ignored by git).
- WRDS smoke report not run (WRDS_DATA_ROOT not set).
- Bundle: `docs/gpt_bundles/2025-12-30T10-58-58Z_ticket-17_20251230_101454_ticket-17_baseline-suite-comparison.zip`.
