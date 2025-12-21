<!--
generated_at: 2025-12-21T19:43:02Z
git_sha: bf7e8ea58e82c009404eb0e5fa2ccde8a62a72a2
branch: feat/ticket-06-bundle-commit-consistency
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Architecture

## System overview

```
DataHandler -> Engine -> Strategy -> Portfolio -> Broker -> Execution -> Artifacts
```

- `DataHandler` streams `MarketEvent`s with strict time ordering.
- `Engine` enforces the no-lookahead clock, routes signals, and applies t+1 semantics.
- `Strategy` emits `SignalEvent`s based on market data and a universe definition.
- `Portfolio` enforces risk caps, sizing, and turnover/heat constraints.
- `Broker` + `Execution` implement slippage, commissions, and order routing models.
- Reporting utilities transform artifacts into Markdown summaries and plots.

## Core modules

- `src/microalpha/engine.py` — Event-driven backtest engine enforcing strict time ordering.
- `src/microalpha/data.py` — core module
- `src/microalpha/portfolio.py` — Portfolio management reacting to fills and signals.
- `src/microalpha/broker.py` — Broker wrapper delegating to execution models.
- `src/microalpha/execution.py` — Execution models responsible for producing fills.
- `src/microalpha/strategies/flagship_momentum.py` — Compatibility shim for flagship strategy.
- `src/microalpha/strategies/cs_momentum.py` — core module
- `src/microalpha/reporting/summary.py` — Markdown summary generator for Microalpha artifacts.
- `src/microalpha/reporting/tearsheet.py` — Render separate equity and bootstrap plots for Microalpha runs.
- `src/microalpha/walkforward.py` — Walk-forward validation orchestration.
- `src/microalpha/runner.py` — High-level execution helpers for single backtests.

## Entry points

- CLI: `microalpha` (`src/microalpha/cli.py`).
- Wrappers: `run.py`, `walk_forward.py`.
- Make targets: `make sample`, `make wfv`, `make report`, `make report-wrds`.

## Artifact layout (sampled)

- `artifacts/sample_flagship`: 12 files, 258780 bytes
- `artifacts/sample_wfv`: 30 files, 328433 bytes

## Supporting subsystems

- Config parsing: `src/microalpha/config.py`, `src/microalpha/config_wfv.py`.
- Metrics & risk: `src/microalpha/metrics.py`, `src/microalpha/risk.py`, `src/microalpha/risk_stats.py`.
- Logging/manifest: `src/microalpha/logging.py`, `src/microalpha/manifest.py`.
- WRDS helpers: `src/microalpha/wrds/` and `scripts/export_wrds_flagship.py`.
