# Experiments & Configured Runs

## Flagship Momentum – Sample Bundle
- **Configs**: `configs/flagship_sample.yaml` (single), `configs/wfv_flagship_sample.yaml` (walk‑forward).
- **Data**: `data/sample/` prices + metadata + universe.
- **Goal**: Demonstrate full stack (sector‑neutral momentum, budgeted RP, queue/impact) on deterministic data.
- **Outputs**: `artifacts/sample_flagship/<RUN_ID>/` and `artifacts/sample_wfv/<RUN_ID>/` with metrics/bootstrap/exposures/trades; summaries under `reports/summaries/flagship_mom*.md`.
- **Metrics (latest committed)**: Sharpe≈−0.66 single, +0.22 WFV (see CURRENT_RESULTS).

## Flagship Momentum – Public Mini Panel
- **Config**: `configs/wfv_flagship_public.yaml`.
- **Data**: `data/public/` (AAPL, MSFT, AMZN, GOOGL, TSLA, NVDA).
- **Goal**: Walk‑forward demo on recognisable tickers without licenses.
- **Outputs**: user‑specified artifacts dir (e.g., `artifacts/public_wfv`), report via `microalpha report`.

## Flagship Momentum – WRDS / CRSP
- **Configs**: `configs/wfv_flagship_wrds.yaml` (full), `configs/wfv_flagship_wrds_smoke.yaml` (shortened).
- **Data**: `$WRDS_DATA_ROOT` exports (CSV/Parquet), universe `universes/flagship_sector_neutral.csv`, metadata `meta/crsp_security_metadata.csv`.
- **Goal**: Resume‑ready 12–1 sector‑neutral momentum with tight risk (1.25x gross, 20% DD halt, ADV/price floors, turnover 3% ADV).
- **Pipeline**: `make wfv-wrds` then `make report-wrds` → analytics, SPA, factor regressions, docs updates.
- **Status**: Prior run 2025-11-21 recorded Sharpe≈0.40 (pre‑tightening). Latest smoke rerun (2015–2019 window) completed; full rerun with tightened caps still pending due to runtime (see OPEN_QUESTIONS).

## Flagship Momentum – CS Momentum Variants
- **Configs**: `configs/wfv_cs_mom.yaml`, `configs/wfv_cs_mom_small.yaml`, `configs/wfv_cs_mom_sp500_small.yaml`, `configs/wfv_cs_mom_sp500_med.yaml`.
- **Data**: `data_sp500` or subsets listed in configs.
- **Goal**: Cross‑sectional momentum experiments with different universes and grid sizes.
- **Outputs**: artifacts under paths configured in YAML (defaults to `artifacts/`).

## Mean Reversion
- **Config**: `configs/meanrev.yaml`.
- **Data**: `../data/` (expects SPY CSV).
- **Goal**: Simple z‑score mean‑reversion baseline; demonstrates single‑asset flow and capital policy.

## Breakout Momentum
- **Config**: `configs/breakout.yaml`.
- **Goal**: Entry on N‑day high, exit on N‑day low or time stop; illustrates basic signal lifecycle.

## Market Making (LOB vs TWAP)
- **Configs**: `configs/mm.yaml`, `configs/mm_lob_tplus1.yaml`, `configs/mm_lob_same_tick.yaml`.
- **Goal**: Compare limit‑order‑book execution vs TWAP/market fills; used by `scripts/plot_mm_spread.py` to visualise realised spread vs inventory.
- **Outputs**: artifacts under `artifacts/mm_demo/...` plus `mm_spread.png`.

## WRDS Single Test
- **Config**: `configs/flagship_wrds_single.yaml`.
- **Goal**: Smoke backtest on WRDS data (no walk‑forward) to validate wiring.
- **Outputs**: `artifacts/wrds_single_test/<RUN_ID>/` (latest metrics are zero because no trades; see CURRENT_RESULTS).

## Benchmarks / Performance
- **Files**: `benchmarks/bench_engine.py`, `benchmarks/bench_multi_stream.py`.
- **Goal**: Measure event‑loop throughput and multi‑asset streaming performance (manual invocation).

## Reporting/Analytics Experiments
- **Factor regressions**: `reports/factors.py` / `reports/factors_ff.py` on any artifact with `equity_curve.csv`.
- **SPA**: `reports/spa.py` on `grid_returns.csv`.
- **Analytics**: `reports/analytics.py` on `signals.csv` + `equity_curve.csv` (IC/IR/deciles/betas).
- **Interactive HTML**: `reports/html_report.py` for per‑run interactive visualisation.
