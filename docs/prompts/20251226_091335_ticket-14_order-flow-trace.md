TICKET: ticket-14
TITLE: Trace post-signal order pipeline to explain WRDS zero-trade degeneracy (no p-hacking)

You are operating in the microalpha repo. Follow AGENTS.md exactly (stop-the-line rules, data policy, branch/commit rules, and required run logs).

DO NOT write a long upfront plan. Start working immediately: inspect → implement → test → log → bundle.

## Objective
Ticket-13 diagnostics show sleeve selection is non-empty on WRDS flagship, yet WFV candidates still produce 0 trades and fail non-degeneracy constraints.
This ticket must:
1) instrument the *post-signal pipeline* (allocation → sizing → order creation → broker acceptance → fills) to produce a compact, per-rebalance “where did orders go to zero?” trace, and
2) use that trace to identify the FIRST real bug causing 0 trades (if obvious + safe), then fix it with tests.
No threshold loosening. No “make it trade” hacks.

## Branch + run setup (required)
- Create feature branch: `codex/ticket-14-order-flow-trace`
- Create RUN_NAME: `YYYYMMDD_HHMMSS_ticket-14_order-flow-trace`
- Create run log dir: `docs/agent_runs/$RUN_NAME/` and write:
  - PROMPT.md (exact prompt)
  - COMMANDS.md (every command, in order)
  - RESULTS.md (what changed + what you found + artifact links)
  - TESTS.md (tests + outputs)
  - META.json (git SHA before/after, env notes, dataset id, config hashes, artifact paths, web sources)

## What to inspect first (fast)
- Strategy output: where target weights/desired positions are computed for flagship momentum.
- Allocation code paths: risk_parity / equal (whatever “equal” means here) and how NaNs or insufficient history are handled.
- Portfolio sizing & order generation:
  - look for min_qty / rounding-to-zero behavior
  - min_trade_notional thresholds (if any)
  - turnover / leverage / single-name caps that could clip everything to zero
- Broker/execution:
  - reasons orders could be rejected / never filled
  - required price fields (open/close) and behavior if missing

## Implementation requirements
### A) Add “order-flow diagnostics” (sideband, must not change trading decisions)
Add a per-rebalance diagnostic payload that records counts at each stage:
- rebalance_date
- selected_long / selected_short (already have filter diagnostics; reuse if possible)
- target_weights_nonzero_count, sum_abs_weights, min/max weight, count_clipped_by_caps (if applicable)
- orders_created_count, orders_nonzero_qty_count
- orders_dropped_reason_counts (e.g., qty==0 due to rounding, min_qty, min_notional, missing price, risk model failure, etc.)
- orders_accepted/rejected by broker (with reason buckets)
- fills_count (if available) and “filled notional” summary

Where to store:
- For single backtest runs: write `artifacts/.../order_flow_diagnostics.json` (or `.jsonl`) plus include a summary in `manifest.json`.
- For walk-forward: attach this payload to each candidate’s `folds.json` record (especially when excluded for degeneracy), similar to how `filter_diagnostics` is captured.

This must work even when the candidate produces empty equity / 0 trades (that’s the point).

### B) Make degeneracy explainable
When `non_degenerate.min_trades` rejects a candidate, record a concise failure reason in the exclusion record based on diagnostics, e.g.:
- `no_targets` (weights all zero / NaN)
- `no_orders` (orders_created_count==0)
- `qty_rounded_to_zero`
- `broker_rejected_all`
- `no_fills`
Keep this purely diagnostic; do not change selection or scoring.

### C) Tests (synthetic, required)
Add unit tests that:
- construct a tiny synthetic price/universe case where selection exists and verify diagnostics fields are populated
- trigger at least one “dropped reason bucket” deterministically (e.g., price so high qty rounds to 0) and assert the bucket increments
- ensure diagnostics code does NOT crash the run if some optional field is missing (but must still return an “error” payload only for diagnostics, not swallow core errors)

Run at minimum:
- `make test-fast`
- `pytest -q tests/test_order_flow_diagnostics.py` (or whatever you name it)

### D) Minimal real-data smoke (WRDS-derived, required)
Do a small debug run that uses the existing WRDS debug config pattern (single fold; no parameter changes).
- Reuse or extend the existing `wfv_flagship_wrds_single_fold.yaml` pattern from ticket-13, but add whatever config toggles you need to enable the new diagnostics output.
- Command must be recorded in COMMANDS.md, and artifact directory must be recorded in RESULTS.md + META.json.
- It is OK if the run still fails due to non-degenerate constraints; the acceptance criterion is that diagnostics pinpoint the stage where everything collapses.

## Documentation updates (required)
- Update `PROGRESS.md` with a one-line entry for ticket-14 and the run log path.
- Update `project_state/KNOWN_ISSUES.md` with the new concrete finding (e.g., “weights NaN because …”, “orders rounded to zero because …”, “broker rejects because …”, etc.).
- Update `docs/CODEX_SPRINT_TICKETS.md`:
  - Mark ticket-13 as DONE (diagnostics complete) with note that root-cause fix is ticket-14.
  - Add ticket-14 section with acceptance criteria matching what you implement.
- If results/claims change, update `project_state/CURRENT_RESULTS.md` (otherwise leave it alone).

## Commit policy (required)
- Small logical commits on the feature branch.
- Each commit message starts with `ticket-14: ...`
- Each commit body includes:
  - `Tests: ...`
  - `Artifacts: ...`
  - `Docs: ...`

## Finish (required)
1) Ensure tests pass.
2) Ensure run log is complete and points to artifact dirs.
3) Generate the bundle:
   `make gpt-bundle TICKET=ticket-14 RUN_NAME=$RUN_NAME`
4) Record the bundle path in `docs/agent_runs/$RUN_NAME/RESULTS.md`.
