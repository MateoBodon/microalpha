<!--
generated_at: 2025-12-23T22:01:33Z
git_sha: ba5b48089091f6a858b065dd3a388b467dd67984
branch: codex/ticket-04-leakage-tests-unsafe-manifest
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Dataflow

## Inputs

- Sample data: `data/sample/` (CSV panel + metadata + universe + risk-free series)
- Public data: `data/public/` (per-symbol CSVs + metadata)
- WRDS exports (local only): `${WRDS_DATA_ROOT}/...` referenced by `configs/wfv_flagship_wrds.yaml`
- Factor data: `data/factors/ff3_sample.csv` and `data/factors/ff5_mom_daily.csv`

## Processing

1. Configs in `configs/` define data paths, strategy params, execution, risk caps.
2. `DataHandler` loads CSVs and streams `MarketEvent`s (`src/microalpha/data.py`).
3. `Engine` enforces monotonic timestamps and dispatches signals (`src/microalpha/engine.py`).
4. `Portfolio` applies sizing/constraints, forwards orders to broker (`src/microalpha/portfolio.py`).
5. `Broker` + `Execution` apply slippage/impact/LOB semantics (`src/microalpha/broker.py`, `src/microalpha/execution.py`).

## Outputs

- Artifacts under `artifacts/<run_id>/`: `manifest.json`, `metrics.json`, `equity_curve.csv`, `trades.jsonl`, `bootstrap.json`.
- Summaries under `reports/summaries/`: Markdown + factor tables + SPA outputs.
- Docs assets (WRDS): `docs/img/wrds_flagship/<RUN_ID>/`.
