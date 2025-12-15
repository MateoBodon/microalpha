# Architecture Overview

## Project Purpose
microalpha is a leakage‑safe, event‑driven backtesting platform that ships with deterministic sample runs, walk‑forward validation, bootstrap reality checks, factor regressions, and reporting pipelines. It aims to be a reproducible research scaffold for cross‑sectional momentum and related strategies, with optional WRDS/CRSP data integrations.

## Top‑Level Layout
- `src/microalpha/` – core library (engine, data handlers, strategies, execution, risk, reporting, CLI).
- `configs/` – YAML configs for single runs, walk‑forward grids, WRDS, public and sample bundles.
- `data/` – bundled sample/public price panels, factor CSVs, flagship universe snapshots, WRDS manifest stub.
- `data_sp500/`, `data_sp500_enriched/` – raw and cleaned S&P‑500 style panels used for universe building.
- `artifacts/` – generated run outputs (metrics, trades, folds, plots, analytics, logs); sample + WRDS runs are checked in.
- `reports/` – thin CLI wrappers around reporting/analytics utilities plus saved summaries.
- `scripts/` – data utilities (WRDS export, signals builder, universe construction, SP500 cleaning, MM demo).
- `docs/` – MkDocs site (overview, leakage guarantees, flagship strategy, WRDS guide, results).
- `tests/` – pytest suite (~70 tests) covering engine invariants, execution models, reporting, configs, WRDS markers.
- `benchmarks/`, `examples/`, `notebooks/` – performance probes and exploratory material.

## Main Components
- **Data loading** – `CsvDataHandler`, `MultiCsvDataHandler` stream `MarketEvent`s from per‑symbol CSVs with datetime indexes; optional volume/price lookups for execution sizing.
- **Pre‑processing / metadata** – `market_metadata.py` for ADV/spread/borrow fee metadata; capital sizing policy in `capital.py`; universe construction scripts in `scripts/augment_sp500.py` & `build_flagship_universe.py`.
- **Engine loop** – `Engine` enforces monotonic timestamps and t+1 semantics, dispatching events to Strategy → Portfolio → Broker/Execution.
- **Strategies** – mean‑reversion, breakout, naive market making, cross‑sectional momentum, and flagship sector‑neutral momentum with sector caps and covariance‑aware allocation.
- **Execution models** – simple executor, TWAP/VWAP/Implementation Shortfall schedulers, square‑root/Kyle impact, queue‑aware IOC/PO limit handling, and an internal limit‑order‑book (`lob.py`) with latency.
- **Risk & metrics** – portfolio constraints (exposure, drawdown, turnover, sector heat), HAC Sharpe & block bootstrap (`risk_stats.py`, `risk.py`), performance summarisation (`metrics.py`).
- **Walk‑forward orchestration** – parameter grid search + reality check bootstraps in `walkforward.py`.
- **Reporting** – PNG/Markdown rendering (`reporting/tearsheet.py`, `summary.py`, `wrds_summary.py`), factor regressions, SPA test, and analytics (IC/IR, deciles, rolling betas).
- **CLI / entrypoints** – `microalpha` script (`cli.py`) plus convenience wrappers `run.py`, `walk_forward.py`.

## High‑Level Data Flow
1. **Inputs**: CSV price panels (`data/sample`, `data/public`, WRDS exports), optional symbol metadata and universe files, YAML configs.
2. **Streaming**: DataHandler emits ordered `MarketEvent`s → Engine.
3. **Signals & Orders**: Strategy consumes events, emits `SignalEvent`s → Portfolio sizing/constraints → `OrderEvent`s.
4. **Execution**: Broker delegates to an Executor (TWAP/VWAP/LOB/impact) producing `FillEvent`s with commissions/slippage.
5. **Portfolio accounting**: positions, cash, exposure, borrow costs, equity curve/trade logs accumulated.
6. **Metrics**: `compute_metrics` builds equity returns, Sharpe/Sortino, drawdowns, turnover, optional HAC; bootstrap p‑values persisted.
7. **Artifacts**: CSV/JSON outputs (equity_curve, metrics, bootstrap, exposures, trades, folds/grid files).
8. **Reporting**: `microalpha report` → plots + Markdown summary; analytics/factor/SPA helpers optionally augment WRDS runs; docs ingest artifacts.

## Control Flow / Pipelines
- **Single backtest**: `microalpha run -c <config>` → `runner.run_from_config` builds handlers/strategy/executor, runs Engine, writes artifacts + manifest.
- **Walk‑forward**: `microalpha wfv -c <config>` → `walkforward.run_walk_forward` does grid search per fold, reality‑check bootstrap, aggregates metrics/folds and grid returns.
- **Reporting**: `microalpha report --artifact-dir <dir>` → renders equity + bootstrap PNGs, summary Markdown, optional factor table injection.
- **Make targets**: `make sample`, `make wfv`, `make report`, `make wfv-wrds`, `make wrds-flagship`, etc. orchestrate full pipelines.
- **WRDS export/analytics**: `scripts/export_wrds_flagship.py` pulls CRSP via WRDS API (requires env + pgpass), `scripts/build_wrds_signals.py` derives signals for analytics, `reports/spa.py` runs Hansen SPA, `reports/render_wrds_flagship.py` composes WRDS docs assets.

