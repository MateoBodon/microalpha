<!--
generated_at: 2025-12-23T22:01:33Z
git_sha: ba5b48089091f6a858b065dd3a388b467dd67984
branch: codex/ticket-04-leakage-tests-unsafe-manifest
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

- Latest run: 2025-12-26T17-21-39Z-75ce3c8
- Snapshot:
  - Sharpe_HAC: 0.03
  - MAR: 0.01
  - Max Drawdown: 8.33%
  - Turnover: $32.84MM
  - Reality Check p-value: 0.996
  - SPA p-value: n/a
- Report: `reports/summaries/wrds_flagship.md`


## WRDS smoke (docs/results_wrds_smoke.md)

- Latest run: 2025-12-23T20-19-56Z-7ca855f
- Snapshot:
  - Sharpe_HAC: 0.00
  - MAR: 0.00
  - Max Drawdown: 0.07%
  - Turnover: $434.24K
  - Reality Check p-value: 1.000
  - SPA p-value: n/a
- Report: `reports/summaries/wrds_flagship_smoke.md`
- Note: Smoke run validates WRDS pipeline wiring; metrics are not interpretable for performance.


## Latest progress (PROGRESS.md)

- Date: 2025-12-23
- Ticket-01: SPA/report robustness hardened + WRDS smoke/report rerun (Status: Done). Smoke run: `artifacts/wrds_flagship_smoke/2025-12-23T06-05-28Z-afe1765/`. Report run: `artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/`. Run log: `docs/agent_runs/20251222_200000_ticket-01_fix-spa-robustness/`.
- Ticket-12: PnL integrity checks + same-day fill equity refresh + diagnostic tooling; sample WFV rerun and report generated. WRDS smoke rerun + report completed under `$WRDS_DATA_ROOT` (`artifacts/wrds_flagship_smoke/2025-12-23T20-19-56Z-7ca855f/`), integrity diagnostics OK. WRDS flagship rerun completed (`artifacts/wrds_flagship/2025-12-23T19-40-24Z-ff2979d/`); run remains degenerate (zero trades). Run log: `docs/agent_runs/20251223_080000_ticket-12_fix-wrds-pnl-integrity/`.
- Ticket-04: Leakage guardrails added (signal timestamp invariant, unsafe execution opt-in + manifest fields, report unsafe banner) with red-team tests. Run log: `docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest/`.


## Recent run logs (docs/agent_runs, last 3)

- `20251222_191759_ticket-00_project_state_rebuild` — Regenerated `project_state/` docs and `_generated` indices using updated build/render scripts. (docs/agent_runs/20251222_191759_ticket-00_project_state_rebuild/RESULTS.md)
- `20251222_200000_ticket-01_fix-spa-robustness` — docs/PLAN_OF_RECORD.md: SPA/reality-check must be present; if degenerate it must be labeled with a reason (no crashes, no silent skips). (docs/agent_runs/20251222_200000_ticket-01_fix-spa-robustness/RESULTS.md)
- `20251223_080000_ticket-12_fix-wrds-pnl-integrity` — Fixed same-day fill equity snapshots by refreshing after fills and collapsing per-timestamp entries so trades/costs can’t leave a flat equity curve at run end. (docs/agent_runs/20251223_080000_ticket-12_fix-wrds-pnl-integrity/RESULTS.md)


Sources: `README.md`, `PROGRESS.md`, `docs/results_wrds.md`, `docs/results_wrds_smoke.md`, sample metrics under `artifacts/sample_flagship/`, `artifacts/sample_wfv/`, `artifacts/sample_wfv_holdout/`, and recent `docs/agent_runs/*/RESULTS.md`.
