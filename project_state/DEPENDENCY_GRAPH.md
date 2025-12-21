<!--
generated_at: 2025-12-21T19:48:07Z
git_sha: 631272f7041bff01de865fa5139a4a9e4004c3b2
branch: feat/ticket-06-bundle-commit-consistency
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->

# Dependency Graph

Internal import edges (microalpha.*): 83

## Adjacency list (file -> internal imports)
- `src/microalpha/__init__.py` -> microalpha.broker, microalpha.data, microalpha.engine, microalpha.execution, microalpha.manifest, microalpha.metrics, microalpha.portfolio, microalpha.risk_stats
- `src/microalpha/allocators.py` -> (none)
- `src/microalpha/broker.py` -> microalpha.microalpha.events, microalpha.microalpha.execution
- `src/microalpha/capital.py` -> (none)
- `src/microalpha/cli.py` -> microalpha.microalpha.runner, microalpha.microalpha.walkforward, microalpha.reporting.robustness, microalpha.reporting.summary, microalpha.reporting.tearsheet
- `src/microalpha/config.py` -> (none)
- `src/microalpha/config_wfv.py` -> microalpha.microalpha.config
- `src/microalpha/data.py` -> microalpha.microalpha.events
- `src/microalpha/engine.py` -> microalpha.microalpha.events
- `src/microalpha/events.py` -> (none)
- `src/microalpha/execution.py` -> microalpha.microalpha.events, microalpha.microalpha.lob, microalpha.microalpha.market_metadata, microalpha.microalpha.slippage
- `src/microalpha/lob.py` -> microalpha.microalpha.events
- `src/microalpha/logging.py` -> (none)
- `src/microalpha/manifest.py` -> (none)
- `src/microalpha/market_metadata.py` -> (none)
- `src/microalpha/metrics.py` -> microalpha.microalpha.risk_stats
- `src/microalpha/portfolio.py` -> microalpha.microalpha.events, microalpha.microalpha.logging, microalpha.microalpha.market_metadata
- `src/microalpha/reporting/__init__.py` -> microalpha.microalpha.summary, microalpha.microalpha.tearsheet, microalpha.microalpha.wrds_summary
- `src/microalpha/reporting/analytics.py` -> (none)
- `src/microalpha/reporting/factors.py` -> (none)
- `src/microalpha/reporting/robustness.py` -> microalpha.market_metadata, microalpha.risk_stats
- `src/microalpha/reporting/spa.py` -> (none)
- `src/microalpha/reporting/summary.py` -> microalpha.microalpha.reporting.factors
- `src/microalpha/reporting/tearsheet.py` -> (none)
- `src/microalpha/reporting/wrds_summary.py` -> microalpha.reporting.robustness, microalpha.wrds
- `src/microalpha/risk.py` -> microalpha.microalpha.risk_stats
- `src/microalpha/risk_stats.py` -> (none)
- `src/microalpha/runner.py` -> microalpha.microalpha.broker, microalpha.microalpha.capital, microalpha.microalpha.config, microalpha.microalpha.data, microalpha.microalpha.engine, microalpha.microalpha.execution, microalpha.microalpha.lob, microalpha.microalpha.logging, microalpha.microalpha.manifest, microalpha.microalpha.market_metadata, microalpha.microalpha.metrics, microalpha.microalpha.portfolio, microalpha.microalpha.risk, microalpha.microalpha.slippage, microalpha.microalpha.strategies.breakout, microalpha.microalpha.strategies.cs_momentum, microalpha.microalpha.strategies.flagship_momentum, microalpha.microalpha.strategies.meanrev, microalpha.microalpha.strategies.mm, microalpha.microalpha.wrds
- `src/microalpha/slippage.py` -> microalpha.microalpha.market_metadata
- `src/microalpha/strategies/breakout.py` -> microalpha.microalpha.events
- `src/microalpha/strategies/cs_momentum.py` -> microalpha.microalpha.events
- `src/microalpha/strategies/flagship_mom.py` -> microalpha.microalpha.allocators, microalpha.microalpha.events
- `src/microalpha/strategies/flagship_momentum.py` -> microalpha.microalpha.strategies.flagship_mom
- `src/microalpha/strategies/meanrev.py` -> microalpha.microalpha.events
- `src/microalpha/strategies/mm.py` -> microalpha.microalpha.events
- `src/microalpha/walkforward.py` -> microalpha.microalpha.broker, microalpha.microalpha.config, microalpha.microalpha.config_wfv, microalpha.microalpha.data, microalpha.microalpha.engine, microalpha.microalpha.execution, microalpha.microalpha.lob, microalpha.microalpha.logging, microalpha.microalpha.manifest, microalpha.microalpha.market_metadata, microalpha.microalpha.metrics, microalpha.microalpha.portfolio, microalpha.microalpha.risk_stats, microalpha.microalpha.runner, microalpha.microalpha.strategies.breakout, microalpha.microalpha.strategies.cs_momentum, microalpha.microalpha.strategies.flagship_mom, microalpha.microalpha.strategies.meanrev, microalpha.microalpha.strategies.mm
- `src/microalpha/wrds/__init__.py` -> (none)
- `tools/build_project_state.py` -> (none)
- `tools/gpt_bundle.py` -> (none)
- `tools/render_project_state_docs.py` -> (none)

Source: `project_state/_generated/import_graph.json`.
