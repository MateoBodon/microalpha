<!--
generated_at: 2025-12-21T22:42:31Z
git_sha: 2b48ef75f24acdb206db20d9f5a2681366ac5afa
branch: feat/ticket-02-holdout-wfv
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

- Holdout WFV: `artifacts/sample_wfv_holdout/2025-12-21T20-53-05Z-4457b33`
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


Sources: `README.md`, `docs/results_wrds.md`, sample metrics under `artifacts/sample_flagship/`, `artifacts/sample_wfv/`, and `artifacts/sample_wfv_holdout/`.
