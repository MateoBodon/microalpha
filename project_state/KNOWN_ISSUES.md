<!--
generated_at: 2025-12-22T19:29:50Z
git_sha: e08b720b29a8d96342e12e8fb1fc0beaf009f221
branch: chore/project_state_refresh
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->

# Known Issues

- WRDS runs require local exports and are blocked without `WRDS_DATA_ROOT` (see `docs/wrds.md`).
- docs/results_wrds.md notes the published WRDS metrics are pre-tightening and a full rerun is pending.
- Large data directories (`data/`, `data_sp500/`, `data_sp500_enriched/`) are present; avoid deep parsing in automation.
- From `PROGRESS.md`: Ticket-01: Tightened WRDS caps + smoke targets + report upgrades (Status: Partial — blocked by missing WRDS exports). Run log: `docs/agent_runs/20251220_223500_ticket-01_wrds-tighten-caps/`.
- From `PROGRESS.md`: Ticket-02: Holdout evaluation mode added for walk-forward validation (Status: FAIL (review) — bundle lacked holdout evidence + DIFF mismatch). Run log: `docs/agent_runs/20251221_154039_ticket-02_holdout-wfv/`.
- From `PROGRESS.md`: Ticket-02: Full WRDS holdout WFV run completed (Status: Done; zero-trade output flagged). Run log: `docs/agent_runs/20251221_173223_ticket-02_holdout-wfv-wrds-full/`.
- From `PROGRESS.md`: Ticket-01 (2025-12-23) reports now complete; WRDS smoke rerun under ticket-12 integrity checks is complete, but SPA remains degenerate (“all strategies have zero variance”). Full WRDS flagship rerun under the new integrity checks is complete but remains zero-trade/flat-equity, so performance claims are still not interpretable.
