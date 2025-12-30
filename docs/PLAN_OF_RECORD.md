# PLAN OF RECORD — microalpha

## What this repo is trying to prove (core claim)
- microalpha is a **leakage-safe**, **deterministic**, **event-driven** backtesting + **walk-forward** research system that produces **audit-grade artifacts** (manifest, configs, trade logs, reports).
- Secondary claim (only after validity is locked): the repo can run a **bias-aware** evaluation of a pre-specified equity strategy on **real WRDS/CRSP data**. This is *not* an “alpha discovery” claim by default.

## Stop-the-line rules (non-negotiable)
- No lookahead / leakage: **t+1 execution**, monotonic timestamps, no implicit forward-fill leakage.
- No survivorship bias: **point-in-time universe** and explicit **delisting handling**.
- No p-hacking: pre-declared candidate grids; **final holdout** untouched until the end.
- No fabricated results: every number in docs must link to a run directory produced by a recorded command.

## Estimand (target object)
Let r_t be the **daily net return series** of a strategy on an investable point-in-time universe after:
- commissions,
- slippage/impact,
- borrow (short rebate/borrow cost).

Primary estimand:
- **Holdout** annualized Sharpe of r_t, with **HAC** standard errors (headline metric).

Reporting window:
- A single immutable **holdout period H** (configured once; never used for tuning).

## Headline metrics (must report ALL, net-of-costs)
Holdout:
- Sharpe_HAC (net)
- Annualized return, annualized vol
- Max drawdown
- Turnover (gross and net)
- Cost decomposition: commission / slippage+impact / borrow (each in bps and $)
- Multiple-testing adjusted inference: **Hansen SPA p-value** over the full candidate set evaluated during tuning
- Reality-check / bootstrap p-value (if SPA is degenerate, report **“degenerate” + reason**, do not crash)

Diagnostics (not headline, but must exist for audit):
- Net/gross exposure time series + concentration
- Trade count, average holding period
- Factor regression on holdout (FF5+Mom): alpha + HAC t-stat, plus key betas

## Baselines (same calendar, same universe rules)
Required:
- Equal-weight universe portfolio (monthly rebalance)
- Market proxy: CRSP value-weighted index (preferred) or SPY total return (fallback)
- Naive momentum baseline (simple, not “flagship”): rank by 12-1m return, equal-weight top decile, monthly rebalance
- Cash / risk-free

## Evaluation protocol (defensible; no p-hacking)
### Data (WRDS)
- Returns/prices: CRSP daily for common stocks (shrcd 10/11; exchcd 1/2/3).
- Risk-free + factors: Ken French daily via WRDS export (repo sample factors are weekly; reports resample returns explicitly).
- Delisting: incorporate dlret/terminal returns via ETL or explicit engine rule (documented; tested).

### Universe (point-in-time)
Default (recommended because it’s point-in-time by construction):
- Monthly top N by lagged market cap at month-end, effective next month.
- Universe snapshots written to disk with `effective_date`.
- Strategy uses the latest snapshot **<= t** (never future).

### Execution & costs (headline runs)
- Signals computed at close t → executed earliest at **t+1** (no same-tick fills in safe/headline mode).
- Costs always ON for headline:
  - commission
  - slippage/impact
  - borrow
- Report must include **cost sensitivity** (0.5× / 1× / 2× costs).

### Splits (nested evaluation)
- Walk-forward is for parameter selection only:
  - For fold i: train window → fit/estimate; validation window → select params.
  - Candidate grid is **declared in config** and stored in artifacts.
- Final holdout:
  - A single immutable holdout window H evaluated once per strategy/config.
  - Holdout metrics stored separately (e.g., `holdout_metrics.json`) and are the only headline numbers.

### Inference (selection bias control)
- SPA / reality-check computed on the **holdout** return series across **ALL candidates considered during tuning**.
- If inference cannot be computed, the run cannot be labeled “headline”.

### Robustness (pre-registered; NOT tuned on holdout)
Minimum robustness grid:
- Universe size: N in {300, 500, 1000} (or documented alternatives)
- Rebalance: monthly vs weekly
- Cost multipliers: 0.5× / 1× / 2×
- Training window sensitivity (within reasonable bounds)

## What counts as “resume-credible”
A run is resume-credible only if ALL are true:
- Reproducible: exact command + config + dataset_id reproduce artifacts; manifest captures git SHA + config hash.
- Valid: point-in-time universe, delist handling, t+1 execution; unsafe flags absent (or loudly labeled and excluded from headline).
- No p-hacking: holdout untouched during tuning; candidate set declared up front.
- Contextualized: baselines reported; claims match evidence (no “alpha” language unless justified).
- Inference present: SPA/reality-check output exists and is interpretable (not silently skipped).

Aspirational “strong headline” target (not guaranteed; do not contort protocol to hit it):
- Holdout Sharpe_HAC (net) >= 0.8
- MaxDD <= 25%
- SPA p-value <= 0.10
- Robustness: Sharpe stays positive at 2× costs and across >=2 universe variants

## Roadmap (commands + expected artifacts)
### Horizon: 1–2 weeks (validity + one locked WRDS headline run)
1) Make inference/reporting robust (no SPA crashes; degenerate cases handled)
- Commands:
  - `pytest -q`
  - (if WRDS available) `WRDS_DATA_ROOT=/path/to/wrds make report-wrds`
- Expected artifacts:
  - `artifacts/<run_id>/spa.json` + `spa.md` (or equivalent)
  - `reports/summaries/<run_id>_wrds_flagship.md` references SPA output explicitly

2) Enforce unsafe-mode labeling (no accidental lookahead)
- Commands: `pytest -q`
- Expected artifacts:
  - `manifest.json` contains explicit `unsafe_*` flags when relevant
  - Reports show a **NOT LEAKAGE-SAFE** banner for unsafe runs

3) Produce ONE locked WRDS run (nested eval + holdout) and publish it
- Commands:
  - `WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds`
  - `WRDS_DATA_ROOT=/path/to/wrds make report-wrds`
- Expected artifacts (must exist for “headline”):
  - `manifest.json`, `metrics.json`, `holdout_metrics.json`
  - `equity_curve.csv`, `trades.jsonl`
  - `folds/` (per-fold metrics + chosen params)
  - `tearsheet.png` + `drawdown.png`
  - `baselines.csv` + baseline overlay plot
  - `spa.md/json` + reality-check outputs (or “degenerate + reason”)
- Docs updated:
  - `PROGRESS.md`
  - `docs/results_wrds.md` (links to run_id + caveats)
  - `README.md` (one-line link to results page; no hype)

### Horizon: 4–8 weeks (robustness grid + attribution)
- Run the pre-registered robustness grid (do not change after holdout review)
  - Command (to add): `python scripts/run_robustness_grid.py --config configs/robustness_grid_wrds.yaml`
  - Artifacts: summary table + cost sensitivity + universe sensitivity + fold stability plots
- Add factor attribution on holdout (FF5+Mom) + rolling betas
  - Artifacts: `reports/summaries/<run_id>_factors.md` + CSV tables

### Longer-term (institution-grade polish)
- Data provenance: dataset_id + checksums for exports; schema validation in CI.
- Performance: caching + profiling; deterministic parallelization for grids.
- Research hygiene: deflated Sharpe / selection bias adjustments; documented model risk.
