<!--
generated_at: 2026-01-25T23:23:20Z
git_sha: 4d08d18202a411cd831efce739cd5cb37e6deb1e
branch: codex/ticket-22-wrds-resume-metrics
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

- Latest run: 2026-01-25T22-58-24Z-4d08d18
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

- Date: 2026-01-25
- ### Done
- - Ticket-19a: committed scaffold + project_state index refresh, ran project_state_refresh and test-fast, and logged the run under ticket-19 naming. Run log: `docs/agent_runs/20260125_191727_ticket-19_commit-and-validate-scaffold/`.
- - Ticket-19a: created local venv, refreshed project_state, fixed pandas 3 compatibility in data/reporting, and ran `make test-fast` successfully. Run log: `docs/agent_runs/20260125_200424_ticket-19_commit-and-validate-scaffold-env/`.
- - Ticket-22: WRDS holdout WFV + report run completed (holdout zero trades; inference fields computed on selection window). Artifacts: `artifacts/wrds_flagship/2026-01-25T21-01-51Z-4d08d18/`. Summary: `docs/results_wrds_resume.md`. Run log: `docs/agent_runs/20260125_205959_ticket-22_wrds-resume-metrics/`.
- - Ticket-23: WRDS holdout WFV + report rerun with coverage-aligned windows; holdout now executes trades (non-degenerate). Artifacts: `artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18/`. Summary: `docs/results_wrds_resume.md`. Run log: `docs/agent_runs/20260125_224419_ticket-23_wrds-holdout-nonzero-trades/`.


## Recent run logs (docs/agent_runs, last 3)

- `20260125_200424_ticket-19_commit-and-validate-scaffold-env` — Created `.venv` and installed dev dependencies for test execution. (docs/agent_runs/20260125_200424_ticket-19_commit-and-validate-scaffold-env/RESULTS.md)
- `20260125_205959_ticket-22_wrds-resume-metrics` — Ran WRDS holdout WFV with `configs/wfv_flagship_wrds.yaml` using `WRDS_DATA_ROOT=/srv/data/wrds/wrds`; run_id `2026-01-25T21-01-51Z-4d08d18`. (docs/agent_runs/20260125_205959_ticket-22_wrds-resume-metrics/RESULTS.md)
- `20260125_224419_ticket-23_wrds-holdout-nonzero-trades` — Added holdout diagnostics (order-flow + filter diagnostics) and a hard guardrail for zero-trade holdout runs in `src/microalpha/walkforward.py`. (docs/agent_runs/20260125_224419_ticket-23_wrds-holdout-nonzero-trades/RESULTS.md)


Sources: `README.md`, `PROGRESS.md`, `docs/results_wrds.md`, `docs/results_wrds_smoke.md`, sample metrics under `artifacts/sample_flagship/`, `artifacts/sample_wfv/`, `artifacts/sample_wfv_holdout/`, and recent `docs/agent_runs/*/RESULTS.md`.
