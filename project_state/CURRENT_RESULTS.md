<!--
generated_at: 2025-12-22T19:29:50Z
git_sha: e08b720b29a8d96342e12e8fb1fc0beaf009f221
branch: chore/project_state_refresh
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Current Results


## Sample bundle (README + artifacts)

- Run: `artifacts/sample_flagship/2025-10-30T18-39-31Z-a4ab8e7`
- Sharpe (HAC): -0.66
- MAR (Calmar): -0.41
- Max DD: 17.26%
- RealityCheck p-value: 0.861
- Turnover: $1,211,971.84

- Walk-forward: `artifacts/sample_wfv/2025-10-30T18-39-47Z-a4ab8e7`
- Sharpe (HAC): 0.22
- MAR (Calmar): 0.03
- Max DD: 34.79%
- RealityCheck p-value: 1.000
- Turnover: $28,525,695.10

- Holdout WFV: `artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e`
- Holdout Sharpe (HAC): 1.29
- Holdout MAR (Calmar): 4.03
- Holdout Max DD: 9.36%
- Holdout Turnover: $5,417,903.30



## WRDS results (docs/results_wrds.md)

- Latest run: 2025-11-21T00-28-22Z-54912a8
- Snapshot:
  - Sharpe_HAC: 0.40
  - MAR: 0.04
  - Max Drawdown: 82.35%
  - Turnover: $1.84B
  - Reality Check p-value: 0.986
  - SPA p-value: 0.603
- Report: `reports/summaries/wrds_flagship.md`
- Rerun status (2025-11-22): a smoke walk-forward using the tightened caps finished on run `2025-11-22T00-21-14Z-c792b44` (2015–2019 window). Report artifacts for that run were not generated, so no verified performance metrics are published. A full 2005–2024 rerun with the tightened spec is still pending; previous attempts exceeded the interactive time window (>2h).


## WRDS smoke (docs/results_wrds_smoke.md)

- Latest run: 2025-12-21T21-28-14Z-33c9c2a
- Snapshot:
  - Sharpe_HAC: 0.00
  - MAR: 0.00
  - Max Drawdown: 0.07%
  - Turnover: $434.24K
  - Reality Check p-value: 1.000
  - SPA p-value: 1.000
- Report: `reports/summaries/wrds_flagship_smoke.md`
- Note: Smoke run validates WRDS pipeline wiring; metrics are not interpretable for performance.


## Latest progress (PROGRESS.md)

- Date: 2025-12-22
- Ticket-07: Ticket-02 evidence + bundle integrity fixes (Status: Done). Run log: `docs/agent_runs/20251222_001500_ticket-07_ticket-02-evidence-and-bundle-fix/`.
- Ticket-08: WRDS report SPA/degenerate-case robustness (Status: Done). Run log: `docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/`.
- Ticket-08: Review FAIL (missing sprint ticket entry in `docs/CODEX_SPRINT_TICKETS.md`).
- Ticket-09: Enforced sprint ticket id checks in bundling + backfilled ticket-08 definition (Status: Done). Run log: `docs/agent_runs/20251222_034500_ticket-09_ticket-id-enforcement/`.
- Ticket-10: Block placeholder run logs in gpt-bundle + fix ticket-09 RESULTS (Status: Done). Run log: `docs/agent_runs/20251222_051500_ticket-10_block-placeholder-runlogs/`.
- Ticket-11: Data policy scan + automated guardrails (Status: Done). Run log: `docs/agent_runs/20251222_123806_ticket-11_data-policy-guardrails/`.
- Project-state rebuild: regenerated `project_state/` docs + indices with PROGRESS and recent run summaries, updated generation script, and recorded run log at `docs/agent_runs/20251222_191759_ticket-00_project_state_rebuild/`. Bundle: `docs/gpt_bundles/project_state_2025-12-22T19-27-41Z_e08b720b.zip`.


## Recent run logs (docs/agent_runs, last 3)

- `20251222_051500_ticket-10_block-placeholder-runlogs` — Replaced the ticket-09 RESULTS placeholder with a concrete summary and bundle path. (docs/agent_runs/20251222_051500_ticket-10_block-placeholder-runlogs/RESULTS.md)
- `20251222_123806_ticket-11_data-policy-guardrails` — Formalized ticket-11 in `docs/CODEX_SPRINT_TICKETS.md` and set ticket-09 status to DONE. (docs/agent_runs/20251222_123806_ticket-11_data-policy-guardrails/RESULTS.md)
- `20251222_191759_ticket-00_project_state_rebuild` — Regenerated `project_state/` docs and `_generated` indices using updated build/render scripts. (docs/agent_runs/20251222_191759_ticket-00_project_state_rebuild/RESULTS.md)


Sources: `README.md`, `PROGRESS.md`, `docs/results_wrds.md`, `docs/results_wrds_smoke.md`, sample metrics under `artifacts/sample_flagship/`, `artifacts/sample_wfv/`, `artifacts/sample_wfv_holdout/`, and recent `docs/agent_runs/*/RESULTS.md`.
