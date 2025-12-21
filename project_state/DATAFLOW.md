<!--
generated_at: 2025-12-21T22:42:31Z
git_sha: 2b48ef75f24acdb206db20d9f5a2681366ac5afa
branch: feat/ticket-02-holdout-wfv
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
