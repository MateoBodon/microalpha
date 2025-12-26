# Results

## Diagnosis
- Inspected `artifacts/wrds_flagship/2025-12-23T19-40-24Z-ff2979d/` (manifest, metrics, trades, integrity).
- `trades.jsonl` and `holdout_trades.jsonl` are empty; `metrics.json` shows `num_trades = 0`, `total_turnover = 0`, and `equity_curve.csv` is flat across 2013-04-16 → 2019-12-31.
- `selection_summary.json` shows all grid models with zero Sharpe/vol; `folds.json` test metrics are flat with zero exposure/trades for all evaluated folds.
- `selected_params_full` includes 40 symbols, so the universe is non-empty and market data streamed; degeneracy occurs at the signal/order stage (no executed trades), not due to an empty universe or missing data stream.

## Changes Implemented
- Added configurable non-degenerate WFV constraints (min_trades/min_turnover) and enforced them during selection; excluded candidates are recorded in `folds.json` and `manifest.json`.
- Reports now surface selection constraints when present in the manifest.
- WRDS flagship + smoke configs now require `min_trades >= 1` to prevent zero-trade selection.
- Added regression test: `tests/test_degeneracy_constraints.py`.

## Runs / Artifacts
- Synthetic WFV run exercising non-degenerate gating:
  - Command: `microalpha wfv --config docs/agent_runs/20251226_023453_ticket-13_fix-wrds-degeneracy/wfv_sample_non_degenerate.yaml`
  - Result: **Expected failure** — `Non-degenerate constraints rejected all candidates (min_trades=1; excluded=32).`
  - Artifacts (written before failure): `artifacts/sample_wfv_non_degenerate/2025-12-26T02-36-37Z-6c3fc9f/`
- WRDS smoke rerun skipped (no `WRDS_DATA_ROOT` set).

External references consulted: none.
