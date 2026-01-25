<!--
generated_at: 2026-01-25T23:23:20Z
git_sha: 4d08d18202a411cd831efce739cd5cb37e6deb1e
branch: codex/ticket-22-wrds-resume-metrics
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Module Summaries

## Inventory (AST-derived)

| Module | Docstring | Classes | Functions |
| --- | --- | ---: | ---: |
| `src/microalpha/__init__.py` |  | 0 | 0 |
| `src/microalpha/allocators.py` | Portfolio allocators using covariance information. | 0 | 8 |
| `src/microalpha/broker.py` | Broker wrapper delegating to execution models. | 1 | 0 |
| `src/microalpha/capital.py` | Capital allocation policies for multi-asset sizing. | 4 | 0 |
| `src/microalpha/cli.py` | Command line entrypoints for microalpha. | 0 | 3 |
| `src/microalpha/config.py` | Configuration schemas for microalpha backtests. | 6 | 1 |
| `src/microalpha/config_wfv.py` | Walk-forward validation configuration schemas. | 5 | 0 |
| `src/microalpha/data.py` |  | 4 | 0 |
| `src/microalpha/engine.py` | Event-driven backtest engine enforcing strict time ordering. | 1 | 0 |
| `src/microalpha/events.py` | Core event types exchanged between components. | 5 | 0 |
| `src/microalpha/execution.py` | Execution models responsible for producing fills. | 8 | 0 |
| `src/microalpha/execution_safety.py` | Helpers for detecting execution modes that can violate timing assumptions. | 0 | 1 |
| `src/microalpha/integrity.py` | Integrity checks for PnL and equity consistency. | 1 | 3 |
| `src/microalpha/lob.py` | Simplified limit order book with FIFO price levels and latency model. | 4 | 0 |
| `src/microalpha/logging.py` | Lightweight logging utilities for structured artifacts. | 1 | 0 |
| `src/microalpha/manifest.py` | Utilities for recording reproducibility manifests. | 2 | 8 |
| `src/microalpha/market_metadata.py` | Utility helpers for symbol-level market metadata. | 1 | 3 |
| `src/microalpha/metrics.py` | Utility functions for computing portfolio performance metrics. | 0 | 1 |
| `src/microalpha/order_flow.py` | Order flow diagnostics for post-signal execution tracing. | 1 | 4 |
| `src/microalpha/portfolio.py` | Portfolio management reacting to fills and signals. | 2 | 0 |
| `src/microalpha/reporting/__init__.py` | Reporting utilities for tearsheets and markdown summaries. | 0 | 0 |
| `src/microalpha/reporting/analytics.py` | Analytics helpers for IC/IR curves, deciles, and rolling betas. | 1 | 15 |
| `src/microalpha/reporting/baselines.py` | Baseline suite computation and reporting helpers. | 0 | 33 |
| `src/microalpha/reporting/factors.py` | Factor regression utilities for Microalpha summaries. | 3 | 15 |
| `src/microalpha/reporting/robustness.py` | Reporting helpers for cost sensitivity and metadata coverage. | 1 | 10 |
| `src/microalpha/reporting/spa.py` | Hansen SPA test utilities for Microalpha parameter grids. | 1 | 10 |
| `src/microalpha/reporting/summary.py` | Markdown summary generator for Microalpha artifacts. | 0 | 29 |
| `src/microalpha/reporting/tearsheet.py` | Render separate equity and bootstrap plots for Microalpha runs. | 0 | 7 |
| `src/microalpha/reporting/wrds_summary.py` | WRDS-specific markdown and docs summary renderer. | 2 | 46 |
| `src/microalpha/risk.py` |  | 0 | 3 |
| `src/microalpha/risk_stats.py` | Statistical helpers for risk analytics. | 0 | 5 |
| `src/microalpha/runner.py` | High-level execution helpers for single backtests. | 0 | 15 |
| `src/microalpha/slippage.py` | Slippage and market impact models. | 6 | 0 |
| `src/microalpha/strategies/breakout.py` |  | 1 | 0 |
| `src/microalpha/strategies/cs_momentum.py` |  | 1 | 0 |
| `src/microalpha/strategies/flagship_mom.py` | Flagship cross-sectional momentum strategy. | 2 | 0 |
| `src/microalpha/strategies/flagship_momentum.py` | Compatibility shim for flagship strategy. | 0 | 0 |
| `src/microalpha/strategies/meanrev.py` |  | 1 | 0 |
| `src/microalpha/strategies/mm.py` |  | 1 | 0 |
| `src/microalpha/walkforward.py` | Walk-forward validation orchestration. | 0 | 26 |
| `src/microalpha/wrds/__init__.py` | Lightweight helpers for detecting local WRDS credentials and exports. | 0 | 11 |
| `tools/agentic/gpt_bundle.py` | gpt_bundle.py | 0 | 6 |
| `tools/agentic/project_state_refresh.py` | project_state_refresh.py | 0 | 6 |
| `tools/agentic/repo_snapshot.py` | Create a deterministic, lightweight repo snapshot for GPT review. | 0 | 5 |
| `tools/build_project_state.py` | Generate machine-derived indices for project_state. | 0 | 13 |
| `tools/gpt_bundle.py` | Create a Prompt-3 bundle for Codex audit artifacts. | 0 | 14 |
| `tools/render_project_state_docs.py` | Render project_state Markdown docs from generated indices and repo files. | 0 | 41 |

## Notes

- Only top-level classes/functions are indexed (no nested symbols).
- Source: `project_state/_generated/symbol_index.json`.
