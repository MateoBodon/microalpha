# Results

## Checklist verification

- Order-collapse evidence confirmed in `docs/agent_runs/20251226_091335_ticket-14_order-flow-trace/RESULTS.md` with concrete stage counts: pre-fix debug exclusion shows `targets_nonzero=61`, `orders_created=0`, `orders_accepted=0`, `fills=0`, with drop reasons dominated by `max_exposure` (40) and `max_single_name_weight` (21); post-fix fold shows `orders_created=12`, `orders_accepted=12`, `fills=12` and `filled_notional=2,964,947.94`.
- No threshold/p-hacking changes found: `git diff main..HEAD -- configs` is empty; no edits to `min_adv`, `min_price`, `non_degenerate.min_trades`, or turnover caps.
- Tests recorded: `make test-fast` output summary logged in `docs/agent_runs/20251226_122058_ticket-14_wrds-full-run/TESTS.md`; diagnostics test executed in `docs/agent_runs/20251226_091335_ticket-14_order-flow-trace/TESTS.md` (`pytest -q tests/test_order_flow_diagnostics.py`).
- Diagnostics are sideband; the only behavior change is the bug-level fix in weight-based sizing (cap-aware clipping + no default-qty fallback) documented and tested.
- WRDS debug artifacts exist: `artifacts/wrds_flagship_debug/2025-12-26T09-33-29Z-695a387/` and `artifacts/wrds_flagship_debug/2025-12-26T09-44-24Z-695a387/`; `folds.json` contains `order_flow_diagnostics` and `diagnostic_reason` entries (manifest does not embed diagnostics).
- Run log completeness verified for both ticket-14 runs; updated META files now use concrete SHAs.
- `docs/CODEX_SPRINT_TICKETS.md` confirms ticket-13 DONE and ticket-14 acceptance criteria present.

## Bundle

- `docs/gpt_bundles/2025-12-26T19-22-33Z_ticket-14_20251226_141754_ticket-14_checklist-merge.zip`
- Bundle generation currently fails because `git_sha_after` is concrete (required by checklist) but does not match the current head commit for patch verification; needs a decision on allowing `git_sha_after=HEAD` for bundling or adjusting the bundler.
