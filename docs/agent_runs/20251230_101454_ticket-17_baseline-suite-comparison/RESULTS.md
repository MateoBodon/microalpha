# Results

- Added baseline suite computation with `baselines.csv` + `baselines_status.json` (equal-weight universe, market proxy w/ SPY fallback, 12-1 momentum long-only, cash/RF).
- Summary and WRDS reports include a Baselines section (Sharpe_HAC/MaxDD/CAGR/turnover table, overlay plot, missing-baseline labels, baselines CSV link).
- Fixed cost-sensitivity text to clarify borrow costs are logged separately (not scaled) and regenerated `reports/summaries/flagship_mom_wfv.md` + `reports/summaries/flagship_mom_wfv_baselines.png`.
- Updated `docs/CODEX_SPRINT_TICKETS.md` ticket-03 status to DONE with run log link.
- Added synthetic tests for lookahead safety and baselines schema stability.
- Generated baseline-enabled sample reports: `reports/summaries/flagship_mom.md`, `reports/summaries/flagship_mom_baselines.png`, `reports/summaries/flagship_mom_wfv.md`, `reports/summaries/flagship_mom_wfv_baselines.png`.
- Sample artifacts updated locally with baselines outputs under `artifacts/sample_flagship/2025-12-23T21-59-20Z-ba5b480/` and `artifacts/sample_wfv/2025-12-23T18-39-59Z-82c14dc/` (git-ignored).
- Data policy check: no `baselines.csv` or `baselines_status.json` tracked in git.
- Identifier scan: no `permno`/`permco`/`cusip` found in sample baselines CSVs.
- WRDS smoke report not run (WRDS_DATA_ROOT not set).
- Bundle (post-merge): `docs/gpt_bundles/2026-01-10T10-46-59Z_ticket-17_20251230_101454_ticket-17_baseline-suite-comparison.zip`.
