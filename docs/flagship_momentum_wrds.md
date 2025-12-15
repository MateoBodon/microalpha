# WRDS Flagship Momentum Specification

This page pins down the exact strategy, constraints, and run procedure for the WRDS/CRSP flagship momentum study. It lines up with `configs/wfv_flagship_wrds.yaml` (full run) and the shortened smoke config described below.

## Strategy at a glance

- **Signal:** 12–1 cross-sectional momentum (skip 1 month by default), sector-normalised z-scores.
- **Rebalance:** Monthly (`rebalance_frequency='M'`).
- **Universe:** CRSP common shares (see universe CSV under `${WRDS_DATA_ROOT}/universes/flagship_sector_neutral.csv`), sector tags included; ADV columns (`adv_20`, `adv_63`, `adv_126`) expected for liquidity filters.
- **Train/Test:** Walk-forward with 36-month train (756 trading days) and 12-month test (252 days) from 2005-01-03 → 2024-12-31.
- **Hyperparameters (grid):** `lookback_months ∈ {9,12,18}`, `skip_months ∈ {1,2}`, `top_frac ∈ {0.20,0.30}`, allocator risk model ∈ {`risk_parity`, `equal`}. Bottom sleeve fixed at 20%.

## Liquidity, exposure, and turnover controls

- **Liquidity floor:** `min_adv=50MM`, `min_price=$12`.
- **Sleeve breadth:** `max_positions_per_sector=8` for both long and short sleeves.
- **Gross exposure cap:** `max_exposure=1.25x` equity; **portfolio heat:** ≤ `1.5x` equity (sum |position|·price / equity).
- **Drawdown halt:** `max_drawdown_stop=20%` of high-water mark (stops issuing new orders until run end).
- **Turnover discipline:** target 3% of ADV per sleeve entry (`turnover_target_pct_adv=0.03`) plus a hard **$180MM** turnover cap per fold.
- **Sizing:** volatility-scaled capital policy targeting ~$225k daily dollar-vol (21-day lookback) with per-order `min_qty=10`.
- **Execution:** TWAP over 6 slices, IOC limits, linear+sqrt impact with `k_lin=32`, `eta=105`, default ADV 35MM, spread floor 8bps, queue bias (passive multiplier 0.6) and commission 5bps.

## How to run

1. Export CRSP DSF + security master locally and set `WRDS_DATA_ROOT` to that directory.
2. Full walk-forward (grid + SPA + factors):
   ```bash
   WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds
   WRDS_DATA_ROOT=/path/to/wrds make report-wrds
   ```
   Artefacts land under `artifacts/wrds_flagship/<RUN_ID>`; docs assets under `docs/img/wrds_flagship/<RUN_ID>`.
3. **Smoke / shortened run** (faster verification):
   ```bash
   WRDS_CONFIG=configs/wfv_flagship_wrds_smoke.yaml \
   WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds
   ```
   The smoke config trims the date range and grid for turn-around testing; use it before the full run when changing risk limits.

## Artefacts to expect

- `metrics.json`, `bootstrap.json`, `spa.json`, `folds.json`, `grid_returns.csv`
- Plots: `equity_curve.png`, `bootstrap_hist.png`, `spa_tstats.png`, `*_ic_ir.png`, `*_deciles.png`, `*_rolling_betas.png`
- Factor regression markdown: `factors_ff5_mom.md`
- Docs summary: `docs/results_wrds.md` (auto-refreshed by `make report-wrds`)

## Notes & licensing

- Never commit WRDS raw data; only derived artefacts listed above are permitted.
- Universe and metadata paths are env-expanded; no hardcoded user directories.
- If you change constraints, update this page **and** the YAML config, then rerun `make report-wrds` to refresh docs/notebook outputs.
