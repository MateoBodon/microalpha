# WRDS Walk-Forward Results (Flagship Momentum)

> Latest run: **2025-12-26T17-21-39Z-75ce3c8** (`configs/wfv_flagship_wrds.yaml`, 2005-01-03 -> 2020-11-17, 20 folds with 252-day forward tests (~12.0 months))

## Performance Snapshot

| Metric | Value |
| --- | ---:|
| Sharpe_HAC | 0.03 |
| MAR | 0.01 |
| Max Drawdown | 8.33% |
| Turnover | $32.84MM |
| Reality Check p-value | 0.996 |
| SPA p-value | 0.031 |

## Exposure Summary

| Metric | Value |
| --- | ---:|
| Avg net exposure | 7.98% |
| Avg gross exposure | 10.06% |
| Max net exposure | 16.55% |
| Max gross exposure | 16.55% |

_Exposure time series is recorded in equity_curve.csv._

## Cost Breakdown

| Category | Total |
| --- | ---:|
| Commission | $244 |
| Slippage | $0 |
| Borrow | n/a |
| Total | $244 |

## Key Visuals

![Equity Curve](img/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/equity_curve.png)

![Bootstrap Sharpe Histogram](img/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/bootstrap_hist.png)

![SPA Comparator t-stats](img/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/spa_tstats.png)

![IC / Rolling IR](img/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/2025-12-26T17-21-39Z-75ce3c8_ic_ir.png)

![Decile Spreads](img/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/2025-12-26T17-21-39Z-75ce3c8_deciles.png)

![Rolling FF5+MOM Betas](img/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/2025-12-26T17-21-39Z-75ce3c8_rolling_betas.png)

## SPA & Factor Highlights

- Hansen SPA best model: **allocator_kwargs={'risk_model': 'equal'}|lookback_months=9|skip_months=2|top_frac=0.2000** with p-value **0.031** (2000 stationary bootstrap draws, block=63). See `reports/summaries/wrds_flagship_spa.md`.
- FF5 + MOM regression (HAC lags=5):

```
| Factor | Beta | t-stat |
| --- | ---:| ---:|
| Alpha | -0.0001 | -1.41 |
| Mkt_RF | 0.1005 | 9.47 |
| SMB | 0.0150 | 1.00 |
| HML | -0.0467 | -2.22 |
| RMW | -0.0178 | -0.62 |
| CMA | -0.0050 | -0.13 |
| MOM | 0.0469 | 3.79 |
```

## Capacity & Turnover

- Average daily turnover: ~$21.67K (total $32.84MM) across 1421 traded days.
- Portfolio heat cap enforced via max positions per sector and ADV floor; no guardrail breaches detected.

## Notes

- Signals derived from the WRDS flagship universe with 12M lookback / 1M skip and ADV >= $50.00MM.
- Training window spans 756 trading days; forward tests run 252 days each.
- Target turnover ≈ 3.00% of ADV with max 8 positions per sector.
- Execution assumes TWAP slicing with linear+sqrt impact, 5 bps commissions, and borrow spread floor of 8 bps.

Published artifacts (PNG/MD/JSON summaries) live under `docs/img/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8` and reports/summaries for reproducibility.
