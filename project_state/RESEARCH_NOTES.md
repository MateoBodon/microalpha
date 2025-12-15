# Research Notes

## Problem Setting
- Event‑driven portfolio backtesting with strict chronology (no lookahead), supporting both single‑asset and cross‑sectional strategies.
- Primary exemplar: **12–1 cross‑sectional momentum**, sector‑neutral, with liquidity/turnover constraints and covariance‑aware allocation.
- Evaluation emphasises out‑of‑sample realism: walk‑forward CV, bootstrap reality checks, HAC‑adjusted statistics, and factor regressions against canonical risk models.

## Core Statistical Blocks
- **Momentum signal**: trailing return over `lookback_months`, skipping `skip_months` most recent; sector‑normalised z‑scores in flagship implementation. Implemented in `strategies/cs_momentum.py` (simple ranking) and `strategies/flagship_mom.py` (sector z + sleeve selection).
- **Allocation**: `allocators.budgeted_allocator` splits long/short sleeves, applies risk parity or Ledoit–Wolf min‑var weights (optionally allow shorts), preserves total budget. Used by flagship to convert sleeve scores into portfolio weights.
- **Risk caps**: Portfolio enforces gross exposure, drawdown halt, turnover cap, sector heat, Kelly sizing, portfolio heat (sum |pos|*price / equity), max names per sector; capital policy (`VolatilityScaledPolicy`) scales quantities to target dollar vol.
- **Execution models**:
  - Impact/slippage: linear, sqrt, or linear+sqrt in bps with spread floor and ADV defaults; queue model for IOC/PO limit orders based on spread/vol/ADV.
  - Schedulers: TWAP, VWAP (volume‑weighted), Implementation Shortfall (geometric urgency).
  - Limit order book: FIFO per level, latency jitter, optional t+1 fill timestamps to preserve no‑peek.
- **Borrow/financing**: Daily borrow cost accrued per short position using `borrow_fee_annual_bps` and trading‑day conventions.

## Inference & Validation
- **Sharpe with HAC**: `risk_stats.sharpe_stats` applies Newey–West long‑run variance when `hac_lags` is set; exposed via `compute_metrics` and env override `METRICS_HAC_LAGS`.
- **Bootstrap Sharpe**: `risk.bootstrap_sharpe_ratio` and `_persist_bootstrap` draw stationary/circular blocks; p‑value = P(Sharpe ≤ 0).
- **Reality check (WFV)**: `walkforward.bootstrap_reality_check` bootstraps max Sharpe across grid models to penalise data‑snooping; p‑value stored in `reality_check.json`.
- **Hansen SPA**: `reporting.spa.compute_spa` bootstraps the distribution of max comparator t‑stats vs best model; used in WRDS reporting.
- **Factor regression**: `reporting.factors.compute_factor_regression` runs OLS with Newey–West SE for FF3/Carhart/FF5+MOM; results displayed in summaries and docs.
- **Analytics (signals)**: IC/IR curves and decile spreads from `reporting.analytics` quantify cross‑sectional predictive power; rolling betas track factor drift.

## Data Handling & Leakage Safety
- Monotonic timestamp checks in `Engine` and `Portfolio`; t+1 enforcement in execution models (including LOB); tests cover `LookaheadError` conditions.
- Walk‑forward keeps training/testing disjoint; warmup histories passed explicitly to avoid peeking into test windows.
- Universe/metadata supplied externally (e.g., WRDS exports) to avoid embedding licensed data.

## Conceptual Notes & Potential Ambiguities
- Flagship weights are emitted via `SignalEvent.meta["weight"]`; Portfolio interprets weight as target fraction of equity converted to quantity at current price. Confirm this contract when adding new allocators.
- WRDS runs rely on locally exported total‑return prices (dlret merged); ensure preprocessing aligns with return definition used in analytics/SPA to avoid model mismatch.
- Bootstrap and SPA both address multiple‑testing, but only SPA is reported in WRDS docs; consider aligning their inputs (grid returns vs per‑fold best Sharpe) in future work.
