# WRDS Holdout Resume Metrics (Flagship Momentum)

## Run Metadata

- Run ID: `2026-01-26T01-22-23Z-e76eb4d`
- Git SHA: `e76eb4d576ccbbe4c9af89e8eb9142ea6858a56d`
- Config: `configs/wfv_flagship_wrds.yaml` (sha256: `4b0d8d8a24bbef581b780ff36de6785eee2471db8b02c179be1ebef3747470b2`)
- Universe: `flagship_sector_neutral.csv` (WRDS, point-in-time)
- Selection window (WFV): 2013-01-02 → 2017-12-29
- Holdout window (locked): 2018-01-02 → 2019-12-31
- Net-of-costs: **Yes** (commission 5 bps, linear+sqrt slippage model; borrow floor 8 bps)
- WRDS data root used: `/srv/data/wrds/wrds`
- Commands:
  - `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make wrds-flagship`
  - `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make report-wrds`

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
- Artifacts: `artifacts/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d/`.
