# Module Summaries

## Core Engine
### src/microalpha/engine.py
- **Purpose**: Central event loop enforcing chronological integrity (no lookahead) and routing market events → strategy → portfolio → broker/execution.
- **Key class**: `Engine` with `run()` iterating `data.stream()`, `_on_market()` raising `LookaheadError` if timestamps regress, and injecting profiling when `MICROALPHA_PROFILE` is set.

### src/microalpha/events.py
- **Purpose**: Typed dataclasses for all bus traffic.
- **Classes**: `MarketEvent`, `SignalEvent`, `OrderEvent`, `FillEvent`; exception `LookaheadError` to guard temporal ordering.

### src/microalpha/data.py
- **Purpose**: Data ingestion for single and multi‑asset CSV panels.
- **Classes**: `CsvDataHandler` (per‑symbol stream, date‑range slicing, price/volume lookups, future timestamp helpers) and `MultiCsvDataHandler` (synchronises multiple symbols, forward/back‑fills depending on mode, merges timestamp arrays). Internal `_SymbolState` maintains rolling pointers for fast lookup.

### src/microalpha/portfolio.py
- **Purpose**: Portfolio accounting, risk constraints, and signal‑to‑order translation.
- **Classes/logic**: `Portfolio` tracks cash/positions/equity curve, computes drawdowns, caps exposure/turnover/heat, sector limits, Kelly sizing, borrow cost accrual, capital policy hooks, and realised PnL attribution. Methods `on_market`, `on_signal`, `on_fill`, `_sized_quantity`, `_borrow_cost_for`.

### src/microalpha/broker.py
- **Purpose**: Thin wrapper delegating orders to an execution model.
- **Class**: `SimulatedBroker.execute` → `Executor.execute`.

### src/microalpha/execution.py
- **Purpose**: Execution and slippage models.
- **Classes**: `Executor` (market/limit IOC/PO handling, commission/slippage application, queue fill fractions); schedulers `TWAP`, `VWAP`, `ImplementationShortfall`; impact variants `SquareRootImpact`, `KyleLambda`; `LOBExecution` integrates with internal limit order book and enforces optional t+1 fills. Uses symbol metadata for spread/vol/ADV adjustments.

### src/microalpha/lob.py
- **Purpose**: Simplified level‑2 limit order book with latency.
- **Classes**: `LatencyModel` (randomised ack/fill delays), `LimitOrder`, `BookSide` (FIFO queues per price), `LimitOrderBook` (submit/cancel, matching, seeding book, maintaining lookup).

### src/microalpha/slippage.py
- **Purpose**: Price impact abstractions.
- **Classes**: `SlippageModel` base; `VolumeSlippageModel`, `LinearImpact`, `SquareRootImpact`, `LinearPlusSqrtImpact` with spread floors, ADV defaults, and metadata overrides.

### src/microalpha/market_metadata.py
- **Purpose**: Load/merge symbol‑level liquidity and financing metadata.
- **Structures**: `SymbolMeta` dataclass; helpers `load_symbol_meta`, `merge_symbol_meta`, `_coerce_float_or_none`.

### src/microalpha/capital.py
- **Purpose**: Capital sizing policies applied inside Portfolio.
- **Class**: `VolatilityScaledPolicy` scales base quantities to hit target dollar volatility using recent price history.

### src/microalpha/allocators.py
- **Purpose**: Cross‑sectional risk allocation utilities.
- **Functions**: `risk_parity`, `lw_min_var` (Ledoit–Wolf shrinkage), `budgeted_allocator` for long/short sleeves with sector‑bucket handling; includes matrix helpers and minimum‑variance weights.

### src/microalpha/risk_stats.py
- **Purpose**: Statistical utilities.
- **Functions**: `_newey_west_lrv` long‑run variance; `sharpe_stats` with optional HAC; `block_bootstrap` (stationary/circular) with Politis–White defaults.

### src/microalpha/risk.py
- **Purpose**: User‑facing risk helpers.
- **Functions**: `create_sharpe_ratio`, `create_drawdowns`, `bootstrap_sharpe_ratio` (delegates to `block_bootstrap`, returns distribution/p‑value/CI).

### src/microalpha/metrics.py
- **Purpose**: Aggregate portfolio performance metrics and persistables.
- **Functions**: `compute_metrics` builds equity df, returns, Sharpe/Sortino/CAGR/Calmar, drawdown depth/duration, turnover stats, trade stats, optional benchmark alpha/beta/IR, HAC lags (env override `METRICS_HAC_LAGS`). Returns dict with `equity_df` plus scalar metrics.

### src/microalpha/manifest.py
- **Purpose**: Reproducibility manifest for runs.
- **Functions**: `resolve_git_sha`, `generate_run_id`, `_resolve_distribution_version`; `build` seeds global RNGs and captures versions/platform/config SHA; `write` serialises to `manifest.json`.

### src/microalpha/logging.py
- **Purpose**: Minimal JSONL writer for trade logs.
- **Class**: `JsonlWriter` (append+flush, auto directory creation).

### src/microalpha/config.py
- **Purpose**: Pydantic schemas for single backtests.
- **Models**: `SlippageCfg`, `ExecModelCfg`, `StrategyCfg`, `CapitalPolicyCfg`, `BacktestCfg`. Normalises legacy fields, expands env/tilde in `resolved_data_path`. `parse_config` validates YAML dicts.

### src/microalpha/config_wfv.py
- **Purpose**: Pydantic schemas for walk‑forward configs.
- **Models**: `WalkForwardWindow`, `RealityCheckCfg`, `WFVCfg` (template `BacktestCfg`, grid, artifacts dir).

### src/microalpha/runner.py
- **Purpose**: High‑level single‑run orchestration.
- **Functions**: `run_from_config` loads YAML, builds handlers/strategy/executor, seeds RNG, runs engine, writes manifest/config/equity/metrics/bootstrap/exposures/trades. Helpers `prepare_artifacts_dir`, `persist_config`, `_persist_metrics`, `persist_exposures`, `_persist_bootstrap`, `_persist_trades`, `resolve_path`, `resolve_capital_policy`, `resolve_slippage_model`. Strategy/execution mappings centralised (`STRATEGY_MAPPING`, `EXECUTION_MAPPING`).

### src/microalpha/walkforward.py
- **Purpose**: Walk‑forward CV + parameter optimisation + reality check.
- **Functions**: `load_wfv_cfg` (supports legacy schema), `run_walk_forward` (iterates folds, grid search via `_optimise_parameters`, computes per‑fold metrics, exposures, factor summaries, aggregates bootstrap samples, reality check, grid returns). Helper builders for portfolio/executor, RNG spawning, warmup history collection, metrics summaries, grid payload/rows, reality check bootstrap (`bootstrap_reality_check`), `_annualised_sharpe`.

### src/microalpha/cli.py
- **Purpose**: CLI front‑end for `microalpha` console script.
- **Commands**: `run`, `wfv`, `report`, `info`. Dispatches to runner/walkforward/reporting; handles profile flag, reality‑check overrides, report output paths.

### src/microalpha/__init__.py
- **Purpose**: Public surface for core classes/functions (`Engine`, data handlers, execution models, metrics, manifest helpers).

### src/microalpha/wrds/__init__.py
- **Purpose**: WRDS environment detection utilities.
- **Functions**: `has_pgpass_credentials`, `has_wrds_credentials`, `get_wrds_data_root`, `has_wrds_data`, `wrds_status`; constants for WRDS host/port/db.

## Strategies
### src/microalpha/strategies/meanrev.py
- **Purpose**: Simple z‑score mean reversion on one symbol. Emits LONG/EXIT based on deviation from rolling mean.

### src/microalpha/strategies/breakout.py
- **Purpose**: Breakout momentum with time stop and exit on lower breakout.

### src/microalpha/strategies/mm.py
- **Purpose**: Toy market‑making that oscillates inventory until limit reached.

### src/microalpha/strategies/cs_momentum.py
- **Purpose**: Cross‑sectional momentum (12‑1 style) over multiple symbols, monthly rebalance, optional long/short sleeves with top/bottom fractions.

### src/microalpha/strategies/flagship_mom.py
- **Purpose**: Flagship sector‑neutral momentum with ADV/price filters, sector caps, turnover heat targeting, covariance‑aware allocation (`budgeted_allocator`), sleeve resolution, conflict handling, weight‑per‑signal metadata, warmup history support. Shim `flagship_momentum.py` re‑exports the class.

## Reporting & Analytics
### src/microalpha/reporting/summary.py
- **Purpose**: Markdown summary generator for run artifacts; renders metrics table, visuals, bootstrap stats, exposures, optional factor regression section.
- **Key function**: `generate_summary` plus CLI `main`.

### src/microalpha/reporting/tearsheet.py
- **Purpose**: Plot equity curve + drawdown and bootstrap histogram; annotate Sharpe/DD/etc.
- **Key function**: `render_tearsheet`, CLI `main`.

### src/microalpha/reporting/factors.py
- **Purpose**: Factor regressions (FF3/Carhart/FF5+MOM) with Newey–West errors.
- **Functions**: `compute_factor_regression`, helpers for design matrix, NW SE; CLI `main`.

### src/microalpha/reporting/analytics.py
- **Purpose**: IC/IR series, decile spreads, rolling betas; writes CSV + plots.
- **Functions**: `generate_analytics`, `compute_ic_series`, `compute_rolling_ir`, `compute_decile_table`, `compute_rolling_betas`, plot helpers; CLI `main`.

### src/microalpha/reporting/spa.py
- **Purpose**: Hansen SPA test on grid returns.
- **Functions**: `load_grid_returns`, `compute_spa`, `write_outputs`; CLI `main`.

### src/microalpha/reporting/wrds_summary.py
- **Purpose**: Compose WRDS Markdown summary and docs assets (charts, SPA, factor tables), copy images to docs, write docs/results_wrds.md if requested.
- **Functions**: `render_wrds_summary`, helpers for headline extraction, relative paths, SPA plot rendering.

## Scripts & Wrappers
- `run.py`, `walk_forward.py` – compatibility wrappers around CLI `run`/`wfv`.
- `scripts/augment_sp500.py` – cleanse SP500 panel, fill volumes, compute ADV/market‑cap proxy, emit enriched prices + metadata + summary JSON.
- `scripts/build_flagship_universe.py` – build monthly universes from enriched data with liquidity/sector caps; writes per‑rebalance CSVs and summary.
- `scripts/build_wrds_signals.py` – derive momentum scores/forward returns from WRDS universe for analytics.
- `scripts/export_wrds_flagship.py` – WRDS/CRSP export template (dsf query, GICS merge, per‑symbol CSV & Parquet, manifest, metadata).
- `scripts/plot_mm_spread.py` – demo comparing LOB vs TWAP execution for market‑making config.
- `reports/*.py` – thin wrappers delegating to reporting modules (`analytics`, `factors`, `spa`, `tearsheet`, `wrds_summary`, `wfv_report`, `html_report`).

