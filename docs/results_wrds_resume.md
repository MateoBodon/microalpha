# WRDS Holdout Resume Metrics (Flagship Momentum)

## Run Metadata

- Run ID: `2026-01-27T04-47-22Z-31fe553`
- Git SHA: `31fe55320b5bdf3fdea386de98e627ad15290d0c`
- Config: `configs/wfv_flagship_wrds.yaml` (sha256: `e1be72d6b77367ad02cade13df5ca141b02a66e3ba9d9f4d44bab7cddd2e12e7`)
- Dataset ID: `wrds_crsp_export_20251221_v1`
- Universe: `flagship_sector_neutral.csv` (WRDS, point-in-time)
- Selection window (WFV): 2013-01-02 → 2017-12-29
- Holdout window (locked): 2018-01-02 → 2019-12-31
- Net-of-costs: **Yes** (commission 5 bps, linear+sqrt slippage model; borrow floor 8 bps)
- WRDS data root used: `/srv/data/wrds/wrds`
- Commands:
  - `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds WRDS_DATASET_ID=wrds_crsp_export_20251221_v1 PYTHONPATH=src python -m microalpha.cli wfv --config configs/wfv_flagship_wrds.yaml --out artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship`
  - `WRDS_DATA_ROOT=/srv/data/wrds/wrds PYTHONPATH=src python3 scripts/build_wrds_signals.py --output artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/signals.csv --lookback-months 12 --skip-months 1 --min-adv 30000000`
  - `PYTHONPATH=src python3 reports/analytics.py artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553 --factors data/factors/ff5_mom_daily.csv --plots-dir artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/analytics/plots --analytics-dir artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/analytics/csv`
  - `PYTHONPATH=src python3 reports/factors.py artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553 --factors data/factors/ff5_mom_daily.csv --model ff5_mom --hac-lags 5 --output artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/factors_ff5_mom.md`
  - `PYTHONPATH=src python3 reports/tearsheet.py artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/equity_curve.csv --bootstrap artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/bootstrap.json --metrics artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/metrics.json --output artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/equity_curve.png --bootstrap-output artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/bootstrap_hist.png --title "WRDS Flagship Walk-Forward"`
  - `PYTHONPATH=src python3 reports/spa.py --grid artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/grid_returns.csv --output-json artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/spa.json --output-md artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/spa.md --bootstrap 2000 --avg-block 63`
  - `PYTHONPATH=src python3 reports/render_wrds_flagship.py artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553 --output reports/_runs/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship.md --factors-md artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/factors_ff5_mom.md --analytics-plots artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/analytics/plots --metrics-json-out reports/_runs/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship_metrics.json --spa-json-out reports/_runs/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship_spa.json --spa-md-out reports/_runs/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship_spa.md`

## Holdout Headline Metrics (Locked)

| Metric | Holdout (2018-01-02 → 2019-12-31) |
| --- | ---: |
| Sharpe_HAC (lags=10) | 0.140 |
| Max Drawdown | 3.49% |
| CAGR | 0.307% |
| Turnover | $5.22MM |
| Trades | 26 |

## Inference Fields (WFV Selection Window)

| Metric | Value |
| --- | ---: |
| Reality Check p-value | 0.98813 |
| SPA p-value | 0.015 (status: ok) |

## WFV OOS Headline Metrics (Context Only)

| Metric | WFV OOS (2013-01-02 → 2017-12-29) |
| --- | ---: |
| Sharpe_HAC (lags=10) | 0.272 |
| Max Drawdown | 3.41% |
| CAGR | 0.718% |
| Turnover | $14.75MM (avg $21.1K/day) |
| Trades | 64 |

## Notes

- Holdout selection used: `allocator_kwargs={'risk_model': 'equal'}|lookback_months=9|skip_months=1|top_frac=0.2000`.
- WFV metrics are reported for context only; resume claims should rely on the locked holdout metrics above.
- Artifacts: `artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/`.
- Resume snippet: `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/snippet.md` (metrics JSON alongside).
