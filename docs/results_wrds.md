# WRDS Walk-Forward Results (Flagship Momentum)

> Latest run: **2025-11-21T00-28-22Z-54912a8** (`configs/wfv_flagship_wrds.yaml`, 2005-01-03 -> 2024-04-30, 25 folds with 252-day forward tests (~12.0 months))

## Performance Snapshot

| Metric | Value |
| --- | ---:|
| Sharpe_HAC | 0.40 |
| MAR | 0.04 |
| Max Drawdown | 82.35% |
| Turnover | $1.84B |
| Reality Check p-value | 0.986 |
| SPA p-value | 0.603 |

## Key Visuals

![Equity Curve](img/wrds_flagship/2025-11-21T00-28-22Z-54912a8/equity_curve.png)

![Bootstrap Sharpe Histogram](img/wrds_flagship/2025-11-21T00-28-22Z-54912a8/bootstrap_hist.png)

![SPA Comparator t-stats](img/wrds_flagship/2025-11-21T00-28-22Z-54912a8/spa_tstats.png)

![IC / Rolling IR](img/wrds_flagship/2025-11-21T00-28-22Z-54912a8/2025-11-21T00-28-22Z-54912a8_ic_ir.png)

![Decile Spreads](img/wrds_flagship/2025-11-21T00-28-22Z-54912a8/2025-11-21T00-28-22Z-54912a8_deciles.png)

![Rolling FF5+MOM Betas](img/wrds_flagship/2025-11-21T00-28-22Z-54912a8/2025-11-21T00-28-22Z-54912a8_rolling_betas.png)

## SPA & Factor Highlights

- Hansen SPA best model: **allocator_kwargs={'risk_model': 'equal'}|lookback_months=9|skip_months=2|top_frac=0.2000** with p-value **0.603** (2000 stationary bootstrap draws, block=63). See `reports/summaries/wrds_flagship_spa.md`.
- FF5 + MOM regression (HAC lags=5):

```
| Factor | Beta | t-stat |
| --- | ---:| ---:|
| Alpha | 0.0008 | 1.15 |
| Mkt_RF | 1.0570 | 6.52 |
| SMB | -0.2939 | -1.78 |
| HML | -0.2257 | -1.26 |
| RMW | -0.3265 | -1.36 |
| CMA | -0.7185 | -1.79 |
| MOM | 0.4449 | 4.25 |
```

## Capacity & Turnover

- Average daily turnover: ~$423.00K (total $1.84B) across 2909 traded days.
- Portfolio heat cap enforced via max positions per sector and ADV floor; no guardrail breaches detected.

## Notes

- Signals derived from the WRDS flagship universe with 12M lookback / 1M skip and ADV >= $30.00MM.
- Training window spans 756 trading days; forward tests run 252 days each.
- Target turnover ≈ 5.00% of ADV with max 10 positions per sector.
- Execution assumes TWAP slicing with linear+sqrt impact, 5 bps commissions, and borrow spread floor of 8 bps.

Published artifacts (PNG/MD/JSON summaries) live under `docs/img/wrds_flagship/2025-11-21T00-28-22Z-54912a8` and reports/summaries for reproducibility.
