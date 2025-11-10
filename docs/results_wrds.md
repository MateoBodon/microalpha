# WRDS Walk-Forward Results (Flagship Momentum)

## Overview
- **Universe:** Top ~1,000 U.S. equities by market cap from CRSP daily data (delistings included).
- **Period:** 2000-01-03 through 2025-06-30 with 3-year train / 6-month test walk-forward windows.
- **Costs:** Commission 5 bps, square-root impact calibrated to 35mm ADV, borrow spread floor at 8 bps.
- **Constraints:** Sector-neutral sleeves (max 10 names per GICS sector), 35% turnover cap, T+1 execution.

## Runbook
1. Export WRDS data locally under `$WRDS_DATA_ROOT` (CRSP OHLCV, delisting returns, GICS sectors, ADV snapshots).
2. Configure `.pgpass` (host `wrds-pgdata.wharton.upenn.edu`, port `9737`, db `wrds`) and keep perms at `600`.
3. Execute `make wfv-wrds` to run the flagship walk-forward config in `configs/wfv_flagship_wrds.yaml`.
4. Summarise analytics via:
   - `python reports/analytics.py ARTIFACT_DIR`
   - `python reports/factors.py ARTIFACT_DIR --model ff5_mom`
   - `python reports/spa.py --grid ARTIFACT_DIR/grid_returns.csv`
5. Publish the resulting plots/markdown under `docs/` or `reports/summaries/` (PNG/MD/JSON only).

## Analytics Checklist
- Equity & drawdown curves (existing tearsheet).
- IC / rolling IR plot, decile bars (P1–P10 and P10–P1) saved to `artifacts/plots/`.
- Rolling factor betas (FF5 + MOM) leveraging `reports/analytics.py`.
- Carhart 4F and FF5(+MOM) HAC regressions via `reports/factors.py`.
- Hansen SPA or MCS summary with JSON + markdown produced by `reports/spa.py`.

## Attribution Targets
| Metric | Target | Notes |
| --- | --- | --- |
| Annualised Sharpe | ≥ 1.0 | Measured on out-of-sample folds |
| Max drawdown | ≤ 25% | After costs |
| Sector contribution spread | Balanced | Ensure no single sector >20% exposure |
| SPA p-value | < 0.10 | White/SPA controlling grid snooping |

## Next Steps
- Wire figures/tables generated above into `docs/results_wrds.md` once WRDS runs complete.
- Track artifacts in git only when they are PNG/MD/JSON summaries (never raw WRDS data).
- Extend the same workflow to PEAD and weekly-reversal strategies after flagship momentum is stable.
