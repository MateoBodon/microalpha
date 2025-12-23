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

- Latest run: 2025-12-21T22-32-44Z-2b48ef7
- Snapshot:
  - Sharpe_HAC: 0.00
  - MAR: 0.00
  - Max Drawdown: 0.00%
  - Turnover: $0.00
  - Reality Check p-value: 1.000
  - SPA p-value: degenerate (all strategies have zero variance)
- Report: `reports/summaries/wrds_flagship.md`
- Rerun status (2025-12-23): WRDS report regenerated; SPA now emits a degenerate summary instead of crashing. Latest run is flat/zero-trade (metrics ~0) and is not interpretable for performance claims.


## WRDS smoke (docs/results_wrds_smoke.md)

- Latest run: 2025-12-23T19-19-16Z-809607a
- Snapshot:
  - Sharpe_HAC: 0.00
  - MAR: 0.00
  - Max Drawdown: 0.07%
  - Turnover: $434.24K
  - Reality Check p-value: 1.000
  - SPA p-value: degenerate (all strategies have zero variance)
- Report: `reports/summaries/wrds_flagship_smoke.md`
- Note: Smoke run validates WRDS pipeline wiring; SPA is degenerate and metrics are not interpretable for performance.


## Latest progress (PROGRESS.md)

- Date: 2025-12-23
- Ticket-01: SPA/report robustness hardened + WRDS smoke/report rerun (Status: Done). Run log: `docs/agent_runs/20251222_200000_ticket-01_fix-spa-robustness/`.


## Recent run logs (docs/agent_runs, last 3)

- `20251223_080000_ticket-12_fix-wrds-pnl-integrity` — PnL integrity checks + WRDS smoke rerun under new checks. (docs/agent_runs/20251223_080000_ticket-12_fix-wrds-pnl-integrity/RESULTS.md)
- `20251222_200000_ticket-01_fix-spa-robustness` — SPA/report robustness and WRDS smoke/report rerun. (docs/agent_runs/20251222_200000_ticket-01_fix-spa-robustness/RESULTS.md)
- `20251222_123806_ticket-11_data-policy-guardrails` — Formalized ticket-11 in `docs/CODEX_SPRINT_TICKETS.md` and set ticket-09 status to DONE. (docs/agent_runs/20251222_123806_ticket-11_data-policy-guardrails/RESULTS.md)


Sources: `README.md`, `PROGRESS.md`, `docs/results_wrds.md`, `docs/results_wrds_smoke.md`, sample metrics under `artifacts/sample_flagship/`, `artifacts/sample_wfv/`, `artifacts/sample_wfv_holdout/`, and recent `docs/agent_runs/*/RESULTS.md`.
