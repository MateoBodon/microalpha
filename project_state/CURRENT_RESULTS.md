<!--
generated_at: 2026-01-26T01:36:06Z
git_sha: e76eb4d576ccbbe4c9af89e8eb9142ea6858a56d
branch: main
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

- Latest run: 2026-01-26T01-22-23Z-e76eb4d
- Snapshot:
  - Sharpe_HAC: 0.27
  - MAR: 0.21
  - Max Drawdown: 3.41%
  - Turnover: $14.75MM
  - Reality Check p-value: 0.988
  - SPA p-value: 0.015
- Report: `reports/summaries/wrds_flagship.md`


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

- Date: 2026-01-26
- ### Done
- - Ticket-24: WRDS flagship rerun completed with local exports at `/srv/data/wrds/wrds`; resume metrics refreshed. Artifacts: `artifacts/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d/`. Run log: `docs/agent_runs/20260126_011723_ticket-24_wrds-resume-metrics-refresh/`.


## Recent run logs (docs/agent_runs, last 3)

- `20260126_011723_ticket-24_wrds-resume-metrics-refresh` — Reran WRDS flagship + report with `WRDS_DATA_ROOT=/srv/data/wrds/wrds` and refreshed resume metrics. (docs/agent_runs/20260126_011723_ticket-24_wrds-resume-metrics-refresh/RESULTS.md)
- `20260125_224419_ticket-23_wrds-holdout-nonzero-trades` — Added holdout diagnostics (order-flow + filter diagnostics) and a hard guardrail for zero-trade holdout runs in `src/microalpha/walkforward.py`. (docs/agent_runs/20260125_224419_ticket-23_wrds-holdout-nonzero-trades/RESULTS.md)
- `20260125_205959_ticket-22_wrds-resume-metrics` — Ran WRDS holdout WFV with `configs/wfv_flagship_wrds.yaml` using `WRDS_DATA_ROOT=/srv/data/wrds/wrds`; run_id `2026-01-25T21-01-51Z-4d08d18`. (docs/agent_runs/20260125_205959_ticket-22_wrds-resume-metrics/RESULTS.md)


Sources: `README.md`, `PROGRESS.md`, `docs/results_wrds.md`, `docs/results_wrds_smoke.md`, sample metrics under `artifacts/sample_flagship/`, `artifacts/sample_wfv/`, `artifacts/sample_wfv_holdout/`, and recent `docs/agent_runs/*/RESULTS.md`.
