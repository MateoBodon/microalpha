<!--
generated_at: 2026-02-16T23:31:49Z
git_sha: 8d906214609106197b7e5a9cfbf08a9a5f021380
branch: codex/ticket-36-ship-ticket-35-cleanly
commands:
  - python3 tools/agentic/project_state_refresh.py --zip
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

- Latest run: 2026-02-16T22-33-46Z-8d90621
- Snapshot (overall WFV OOS):
  - Sharpe_HAC: 0.24
  - MAR: 0.14
  - Max Drawdown: 5.32%
  - Turnover: $15.66MM
  - Reality Check p-value: 0.889
- Holdout snapshot (resume rule window 2018-01-02 to 2019-12-31):
  - Sharpe_HAC: 0.588
  - MAR: 0.64
  - Max Drawdown: 1.38%
  - Turnover: $6.12MM
  - Trades: 31
  - Reality Check p-value: 0.941
  - SPA p-value: n/a
- Dataset ID: `wrds_crsp_export_20251221_v1`
- Report: `reports/_runs/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship.md`
- Resume summary: `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/`
- Real-data leaderboard (artifact scan; no rerun): `docs/artifacts/resume/wrds/leaderboard/leaderboard.md`
- Best resume line (window=holdout-only, pre-registered holdout Sharpe rule): `docs/artifacts/resume/wrds/leaderboard/resume_line_best.md`


## WRDS smoke (docs/results_wrds_smoke.md)

- Latest run: 2025-12-24T05-15-43Z-559a99e
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

- Date: 2026-02-16
- ### Done
- - Ticket-35: ran a pre-registered 9-combo WRDS micro-sweep and promoted run `2026-02-16T22-33-46Z-8d90621` as the new best provenance-complete holdout resume line (Sharpe_HAC 0.588, MaxDD 1.38%, 31 trades). Run log: `docs/agent_runs/20260216_223228_ticket-35_wrds-micro-sweep/`.
- - Ticket-36: shipped ticket-35 deliverables as tracked files, fixed ticket-36 run-log schema to unblock validation gates, and prepared clean-bundle regeneration evidence. Run log: `docs/agent_runs/20260216_232907_ticket-ticket-36/`.


## Recent run logs (docs/agent_runs, last 3)

- `20260216_232907_ticket-ticket-36` — Shipped ticket-35 deliverables into tracked state, repaired run-log schema debt for ticket-36, and prepared clean-bundle regeneration with explicit gate runs. (docs/agent_runs/20260216_232907_ticket-ticket-36/RESULTS.md)
- `20260216_223228_ticket-35_wrds-micro-sweep` — Executed pre-registered WRDS sweep (`<=12` combos), generated local WRDS report, and promoted run `2026-02-16T22-33-46Z-8d90621` as the top eligible holdout resume row. (docs/agent_runs/20260216_223228_ticket-35_wrds-micro-sweep/RESULTS.md)
- `20260216_212201_ticket-34_ship-ticket-33-cleanly-and-unblock-make-test-fast` — Shipped ticket-33 leaderboard deliverables, repaired run-log schema metadata, and made `make test-fast` pass. (docs/agent_runs/20260216_212201_ticket-34_ship-ticket-33-cleanly-and-unblock-make-test-fast/RESULTS.md)


Sources: `README.md`, `PROGRESS.md`, `docs/results_wrds.md`, `docs/results_wrds_smoke.md`, sample metrics under `artifacts/sample_flagship/`, `artifacts/sample_wfv/`, `artifacts/sample_wfv_holdout/`, and recent `docs/agent_runs/*/RESULTS.md`.
