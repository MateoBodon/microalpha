<!--
generated_at: 2025-12-23T22:01:33Z
git_sha: ba5b48089091f6a858b065dd3a388b467dd67984
branch: codex/ticket-04-leakage-tests-unsafe-manifest
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->

# Known Issues

- RESOLVED (ticket-16): Run-log META.json files drifted from required schema (missing keys / invalid JSON), breaking audit validation. Impact: run-log integrity checks could not be automated. Detected during ticket-16 repo-wide META.json parse/validation scan. Fix: repaired META.json files and added `scripts/validate_run_logs.py` + Make target. Prevention: `make test-fast` now runs run-log validation.
- WRDS runs require local exports and are blocked without `WRDS_DATA_ROOT` (see `docs/wrds.md`).
- Large data directories (`data/`, `data_sp500/`, `data_sp500_enriched/`) are present; avoid deep parsing in automation.
- RESOLVED (ticket-15): WRDS flagship SPA previously failed with `KeyError: ... not in index` when loading grid returns (report-only run on `artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/`). Fix: reindex grid returns to preserve panel order and classify exceptions as `spa_status=error`; SPA now runs with p-value in range.
- From `PROGRESS.md`: Ticket-01: Tightened WRDS caps + smoke targets + report upgrades (Status: Partial — blocked by missing WRDS exports). Run log: `docs/agent_runs/20251220_223500_ticket-01_wrds-tighten-caps/`.
- From `PROGRESS.md`: Ticket-02: Holdout evaluation mode added for walk-forward validation (Status: FAIL (review) — bundle lacked holdout evidence + DIFF mismatch). Run log: `docs/agent_runs/20251221_154039_ticket-02_holdout-wfv/`.
- From `PROGRESS.md`: Ticket-02: Full WRDS holdout WFV run completed (Status: Done; zero-trade output flagged). Run log: `docs/agent_runs/20251221_173223_ticket-02_holdout-wfv-wrds-full/`.
- From `PROGRESS.md`: Ticket-02: WRDS report run failed at SPA step (Status: Blocked; zero SPA comparator t-stats). Run log: `docs/agent_runs/20251221_175417_ticket-02_holdout-wfv-wrds-report/`. Artifacts: `artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/`.
- From `PROGRESS.md`: Ticket-12: PnL integrity checks + same-day fill equity refresh + diagnostic tooling; sample WFV rerun and report generated. WRDS smoke rerun + report completed under `$WRDS_DATA_ROOT` (`artifacts/wrds_flagship_smoke/2025-12-23T20-19-56Z-7ca855f/`), integrity diagnostics OK. WRDS flagship rerun completed (`artifacts/wrds_flagship/2025-12-23T19-40-24Z-ff2979d/`); run remains degenerate (zero trades). Run log: `docs/agent_runs/20251223_080000_ticket-12_fix-wrds-pnl-integrity/`.
- From `PROGRESS.md`: Ticket-13: WRDS smoke + flagship reruns under `$WRDS_DATA_ROOT` still fail non-degenerate constraints (zero trades); all candidates rejected. Smoke artifacts: `artifacts/wrds_flagship_smoke/2025-12-26T06-19-16Z-364496b/`. Flagship artifacts: `artifacts/wrds_flagship/2025-12-26T06-20-30Z-364496b/`. Run log: `docs/agent_runs/20251226_023453_ticket-13_fix-wrds-degeneracy/`.
- From `PROGRESS.md`: Ticket-13: Filter diagnostics show universe filters pass and sleeve selections are produced, yet trades remain zero; suspected blockage is downstream sizing/risk caps (e.g., `max_single_name_weight`) but needs confirmation. Debug artifacts: `artifacts/wrds_flagship_debug/2025-12-26T07-00-41Z-d4c8edf/`. Run log: `docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/`.
- Ticket-14: Order-flow diagnostics confirmed weight-based orders were being hard-rejected by `max_single_name_weight`/`max_exposure`, collapsing WFV to zero trades. Fix now clips weight-based orders to caps (no threshold loosening) and avoids default-qty fallback when weight sizing rounds to zero. Debug WFV now executes trades; full WRDS flagship rerun still pending. Run log: `docs/agent_runs/20251226_091335_ticket-14_order-flow-trace/`. Artifacts: `artifacts/wrds_flagship_debug/2025-12-26T09-44-24Z-695a387/`.
