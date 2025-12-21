# WRDS Walk-Forward Results (Flagship Momentum)

> Latest run: **2025-12-21T06-06-35Z-0dbb291** (`configs/wfv_flagship_wrds_smoke.yaml`, 2015-01-05 -> 2019-11-05, 10 folds with 126-day forward tests (~6.0 months))

## Performance Snapshot

| Metric | Value |
| --- | ---:|
| Sharpe_HAC | 0.00 |
| MAR | 0.00 |
| Max Drawdown | 0.07% |
| Turnover | $434.24K |
| Reality Check p-value | 1.000 |
| SPA p-value | 1.000 |

## Exposure Summary

| Metric | Value |
| --- | ---:|
| Avg net exposure | -0.04% |
| Avg gross exposure | 0.08% |
| Max net exposure | 0.70% |
| Max gross exposure | 1.54% |

_Exposure time series is recorded in equity_curve.csv._

## Cost Breakdown

| Category | Total |
| --- | ---:|
| Commission | $4 |
| Slippage | $0 |
| Borrow | n/a |
| Total | $4 |

## Key Visuals

![Equity Curve](img/wrds_flagship_smoke/2025-12-21T06-06-35Z-0dbb291/equity_curve.png)

![Bootstrap Sharpe Histogram](img/wrds_flagship_smoke/2025-12-21T06-06-35Z-0dbb291/bootstrap_hist.png)

![SPA Comparator t-stats](img/wrds_flagship_smoke/2025-12-21T06-06-35Z-0dbb291/spa_tstats.png)

![IC / Rolling IR](img/wrds_flagship_smoke/2025-12-21T06-06-35Z-0dbb291/2025-12-21T06-06-35Z-0dbb291_ic_ir.png)

![Decile Spreads](img/wrds_flagship_smoke/2025-12-21T06-06-35Z-0dbb291/2025-12-21T06-06-35Z-0dbb291_deciles.png)

![Rolling FF5+MOM Betas](img/wrds_flagship_smoke/2025-12-21T06-06-35Z-0dbb291/2025-12-21T06-06-35Z-0dbb291_rolling_betas.png)

## SPA & Factor Highlights

- Hansen SPA best model: **allocator_kwargs={'risk_model': 'equal'}|lookback_months=12|skip_months=1|top_frac=0.2000** with p-value **1.000** (500 stationary bootstrap draws, block=63). See `reports/summaries/wrds_flagship_smoke_spa.md`.
- FF5 + MOM regression (HAC lags=5):

```
| Factor | Beta | t-stat |
| --- | ---:| ---:|
| Alpha | -0.0001 | -12.78 |
| Mkt_RF | -0.0000 | -0.22 |
| SMB | 0.0002 | 0.58 |
| HML | 0.0007 | 1.37 |
| RMW | 0.0004 | 0.73 |
| CMA | -0.0014 | -1.83 |
| MOM | 0.0001 | 0.15 |
```

## Capacity & Turnover

- Average daily turnover: ~$499.12 (total $434.24K) across 87 traded days.
- Portfolio heat cap enforced via max positions per sector and ADV floor; no guardrail breaches detected.

## Notes

- Signals derived from the WRDS flagship universe with 12M lookback / 1M skip and ADV >= $50.00MM.
- Training window spans 504 trading days; forward tests run 126 days each.
- Target turnover ≈ 3.00% of ADV with max 8 positions per sector.
- Execution assumes TWAP slicing with linear+sqrt impact, 5 bps commissions, and borrow spread floor of 8 bps.

Published artifacts (PNG/MD/JSON summaries) live under `docs/img/wrds_flagship_smoke/2025-12-21T06-06-35Z-0dbb291` and reports/summaries for reproducibility.
