<!--
generated_at: 2026-01-25T23:23:20Z
git_sha: 4d08d18202a411cd831efce739cd5cb37e6deb1e
branch: codex/ticket-22-wrds-resume-metrics
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->

# Known Issues

- WRDS runs require local exports and are blocked without `WRDS_DATA_ROOT` (see `docs/wrds.md`).
- Large data directories (`data/`, `data_sp500/`, `data_sp500_enriched/`) are present; avoid deep parsing in automation.
- From `PROGRESS.md`: Ticket-12: PnL integrity checks + same-day fill equity refresh + diagnostic tooling; sample WFV rerun and report generated. WRDS smoke rerun + report completed under `$WRDS_DATA_ROOT` (`artifacts/wrds_flagship_smoke/2025-12-23T20-19-56Z-7ca855f/`), integrity diagnostics OK. WRDS flagship rerun completed (`artifacts/wrds_flagship/2025-12-23T19-40-24Z-ff2979d/`); run remains degenerate (zero trades). Run log: `docs/agent_runs/20251223_080000_ticket-12_fix-wrds-pnl-integrity/`.
- From `PROGRESS.md`: Ticket-13: Added non-degenerate WFV selection constraints (min_trades/min_turnover) with manifest/report surfacing and WRDS configs updated; added regression test and sample non-degenerate run (expected failure when zero-trade). Run log: `docs/agent_runs/20251226_023453_ticket-13_fix-wrds-degeneracy/`.
- From `PROGRESS.md`: Ticket-13: WRDS smoke + flagship reruns executed under `$WRDS_DATA_ROOT`; both failed non-degenerate constraints (zero trades). Smoke artifacts: `artifacts/wrds_flagship_smoke/2025-12-26T06-19-16Z-364496b/`. Flagship artifacts: `artifacts/wrds_flagship/2025-12-26T06-20-30Z-364496b/`. Run log: `docs/agent_runs/20251226_023453_ticket-13_fix-wrds-degeneracy/`.
- From `PROGRESS.md`: - Ticket-22: WRDS holdout WFV + report run completed (holdout zero trades; inference fields computed on selection window). Artifacts: `artifacts/wrds_flagship/2026-01-25T21-01-51Z-4d08d18/`. Summary: `docs/results_wrds_resume.md`. Run log: `docs/agent_runs/20260125_205959_ticket-22_wrds-resume-metrics/`.
- From `PROGRESS.md`: - Ticket-23: WRDS holdout WFV + report rerun with coverage-aligned windows; holdout now executes trades (non-degenerate). Artifacts: `artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18/`. Summary: `docs/results_wrds_resume.md`. Run log: `docs/agent_runs/20260125_224419_ticket-23_wrds-holdout-nonzero-trades/`.
