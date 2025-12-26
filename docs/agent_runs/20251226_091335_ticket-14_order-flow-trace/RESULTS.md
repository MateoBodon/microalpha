# Results

- Added order-flow diagnostics across allocation/sizing/orders/broker/fills and persisted per-rebalance payloads (new `src/microalpha/order_flow.py`, engine/portfolio/executor/runner/walkforward hooks). Weight-based sizing now returns 0 when target weights round to zero, and cap breaches clip weight-based orders (counted in diagnostics) instead of hard-dropping.
- Root cause confirmed: pre-fix WRDS debug candidates generated nonzero target weights but all orders were rejected by `max_single_name_weight`/`max_exposure`, yielding `no_orders`. Post-fix diagnostics show cap clipping and executed trades.
- WRDS debug runs:
  - Pre-fix (expected fail): `artifacts/wrds_flagship_debug/2025-12-26T09-33-29Z-695a387/` (non-degenerate rejected all candidates; `folds.json` shows `diagnostic_reason=no_orders` with drop reasons in order-flow payloads).
  - Post-fix: `artifacts/wrds_flagship_debug/2025-12-26T09-44-24Z-695a387/` (single-fold WFV succeeds; `num_trades=12`, `total_turnover=2964947.94`; order-flow summary shows `clipped_by_caps=10` with `max_single_name_weight`/`max_exposure` clips).
- Config used: `docs/agent_runs/20251226_091335_ticket-14_order-flow-trace/wfv_flagship_wrds_single_fold.yaml`.
- Bundle: `docs/gpt_bundles/2025-12-26T09-59-50Z_ticket-14_20251226_091335_ticket-14_order-flow-trace.zip`.
