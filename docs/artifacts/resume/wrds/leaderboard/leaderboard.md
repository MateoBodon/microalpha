# WRDS Real-Data Leaderboard

Pre-registered best rule:
- Primary: maximize holdout `sharpe_hac`.
- Guardrails: `dataset_id` must be present, holdout trades >= 20, holdout max drawdown <= 15.0%
- Tie-breakers: lower holdout max drawdown, then higher holdout MAR, then stable path order.

Candidates scanned: 12
Best eligible row: rank 1 (run_id=2026-02-16T22-33-46Z-8d90621)

| rank | run_id | dataset_id | selection_window | holdout_window | holdout_sharpe_hac | holdout_cagr | holdout_maxdd | holdout_mar | holdout_turnover | holdout_trades | SPA p | RC p | eligible | reasons | config_path | artifact_dir |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| 1 | 2026-02-16T22-33-46Z-8d90621 | wrds_crsp_export_20251221_v1 | 2013-01-02 to 2017-12-29 | 2018-01-02 to 2019-12-31 | 0.588 | 0.88% | 1.38% | 0.638 | $6.12MM | 31 | n/a | 0.941 | yes | - | configs/wfv_flagship_wrds_sweep35.yaml | artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621 |
| 2 | 2026-01-27T04-47-22Z-31fe553 | wrds_crsp_export_20251221_v1 | 2013-01-02 to 2017-12-29 | 2018-01-02 to 2019-12-31 | 0.140 | 0.31% | 3.49% | 0.088 | $5.22MM | 26 | 0.015 | 1.000 | yes | - | configs/wfv_flagship_wrds.yaml | artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553 |
| 3 | 2026-01-25T22-58-24Z-4d08d18 | missing | 2013-01-02 to 2017-12-29 | 2018-01-02 to 2019-12-31 | 0.140 | 0.31% | 3.49% | 0.088 | $5.22MM | 26 | 0.015 | 1.000 | no | missing_dataset_id | configs/wfv_flagship_wrds.yaml | artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18 |
| 4 | 2026-01-26T01-22-23Z-e76eb4d | missing | 2013-01-02 to 2017-12-29 | 2018-01-02 to 2019-12-31 | 0.140 | 0.31% | 3.49% | 0.088 | $5.22MM | 26 | 0.015 | 1.000 | no | missing_dataset_id | configs/wfv_flagship_wrds.yaml | artifacts/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d |
| 5 | 2025-12-21T22-32-44Z-2b48ef7 | missing | 2005-01-03 to 2020-12-31 | 2021-01-04 to 2024-12-31 | 0.000 | n/a | 0.00% | n/a | $0.00MM | n/a | n/a | 1.000 | no | missing_dataset_id|missing_holdout_trades | /Users/mateobodon/Documents/Programming/Projects/microalpha/configs/wfv_flagship_wrds.yaml | artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7 |
| 6 | 2025-12-23T19-40-24Z-ff2979d | missing | 2005-01-03 to 2020-12-31 | 2021-01-04 to 2024-12-31 | 0.000 | n/a | 0.00% | n/a | $0.00MM | 0 | n/a | 1.000 | no | missing_dataset_id|holdout_trades_lt_20 | /Users/mateobodon/Documents/Programming/Projects/microalpha/configs/wfv_flagship_wrds.yaml | artifacts/wrds_flagship/2025-12-23T19-40-24Z-ff2979d |
| 7 | 2025-12-26T17-21-39Z-75ce3c8 | missing | 2005-01-03 to 2020-12-31 | 2021-01-04 to 2024-12-31 | 0.000 | n/a | 0.00% | n/a | $0.00MM | 0 | 0.031 | 1.000 | no | missing_dataset_id|holdout_trades_lt_20 | /Users/mateobodon/Documents/Programming/Projects/microalpha/configs/wfv_flagship_wrds.yaml | artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8 |
| 8 | 2026-01-25T21-01-51Z-4d08d18 | missing | 2005-01-03 to 2020-12-31 | 2021-01-04 to 2024-12-31 | 0.000 | n/a | 0.00% | n/a | $0.00MM | 0 | 0.015 | 1.000 | no | missing_dataset_id|holdout_trades_lt_20 | configs/wfv_flagship_wrds.yaml | artifacts/wrds_flagship/2026-01-25T21-01-51Z-4d08d18 |
| 9 | 2025-11-12T18-50-58Z-b2eaf50 | missing | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.454 | 0.894 | no | missing_dataset_id|missing_holdout_sharpe|missing_holdout_trades|missing_holdout_maxdd | /Users/mateobodon/Documents/Programming/Projects/microalpha/configs/wfv_flagship_wrds.yaml | artifacts/wrds_flagship/2025-11-12T18-50-58Z-b2eaf50 |
| 10 | 2025-11-21T00-28-22Z-54912a8 | missing | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.603 | 0.987 | no | missing_dataset_id|missing_holdout_sharpe|missing_holdout_trades|missing_holdout_maxdd | /Users/mateobodon/Documents/Programming/Projects/microalpha/configs/wfv_flagship_wrds.yaml | artifacts/wrds_flagship/2025-11-21T00-28-22Z-54912a8 |
| 11 | 2025-11-22T00-21-14Z-c792b44 | missing | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.792 | no | missing_dataset_id|missing_holdout_sharpe|missing_holdout_trades|missing_holdout_maxdd | /Users/mateobodon/Documents/Programming/Projects/microalpha/configs/wfv_flagship_wrds_smoke.yaml | artifacts/wrds_flagship/2025-11-22T00-21-14Z-c792b44 |
| 12 | 2025-12-26T06-20-30Z-364496b | missing | 2005-01-03 to 2020-12-31 | 2021-01-04 to 2024-12-31 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | no | missing_dataset_id|missing_holdout_sharpe|missing_holdout_trades|missing_holdout_maxdd | /Users/mateobodon/Documents/Programming/Projects/microalpha/configs/wfv_flagship_wrds.yaml | artifacts/wrds_flagship/2025-12-26T06-20-30Z-364496b |
