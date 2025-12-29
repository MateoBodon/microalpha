# WRDS Flagship Walk-Forward

## Selection Constraints

- Non-degenerate: min_trades >= 1 (excluded 268 candidate(s) during selection)

## Headline Metrics

| Metric | Value |
| --- | ---:|
| Sharpe_HAC | 0.03 |
| MAR | 0.01 |
| MaxDD | 8.33% |
| Turnover | $32,836,267 |
| RealityCheck_p_value | 0.996 |
| SPA_p_value | 0.031 |

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

## Visuals

![Equity Curve](../../docs/img/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/equity_curve.png)

![Bootstrap Sharpe Histogram](../../docs/img/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/bootstrap_hist.png)

![SPA Comparator t-stats](../../docs/img/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/spa_tstats.png)

## Hansen SPA Summary

- **Best model:** allocator_kwargs={'risk_model': 'equal'}|lookback_months=9|skip_months=2|top_frac=0.2000
- **Observed max t-stat:** 2.487
- **p-value:** 0.031
- **Bootstrap draws:** 2000 (avg block 63)

| Comparator | Mean Diff | t-stat |
| --- | ---:| ---:|
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=12|skip_months=1|top_frac=0.2000 | 0.0000 | 0.91 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=12|skip_months=1|top_frac=0.3000 | 0.0000 | 0.91 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=12|skip_months=2|top_frac=0.2000 | 0.0000 | 1.94 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=12|skip_months=2|top_frac=0.3000 | 0.0000 | 1.94 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=18|skip_months=1|top_frac=0.2000 | 0.0000 | 1.39 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=18|skip_months=1|top_frac=0.3000 | 0.0000 | 1.39 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=18|skip_months=2|top_frac=0.2000 | 0.0000 | 1.81 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=18|skip_months=2|top_frac=0.3000 | 0.0000 | 1.81 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=9|skip_months=1|top_frac=0.2000 | 0.0000 | 0.31 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=9|skip_months=1|top_frac=0.3000 | 0.0000 | 0.31 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=9|skip_months=2|top_frac=0.3000 | 0.0000 | 0.00 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=12|skip_months=1|top_frac=0.2000 | 0.0000 | 1.45 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=12|skip_months=1|top_frac=0.3000 | 0.0000 | 1.45 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=12|skip_months=2|top_frac=0.2000 | 0.0000 | 2.49 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=12|skip_months=2|top_frac=0.3000 | 0.0000 | 2.49 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=18|skip_months=1|top_frac=0.2000 | 0.0000 | 1.83 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=18|skip_months=1|top_frac=0.3000 | 0.0000 | 1.83 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=18|skip_months=2|top_frac=0.2000 | 0.0000 | 2.05 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=18|skip_months=2|top_frac=0.3000 | 0.0000 | 2.05 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=9|skip_months=1|top_frac=0.2000 | 0.0000 | 0.13 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=9|skip_months=1|top_frac=0.3000 | 0.0000 | 0.13 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=9|skip_months=2|top_frac=0.2000 | 0.0000 | 1.92 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=9|skip_months=2|top_frac=0.3000 | 0.0000 | 1.92 |

## Factor Attribution (FF5+MOM)

| Factor | Beta | t-stat |
| --- | ---:| ---:|
| Alpha | -0.0001 | -1.41 |
| Mkt_RF | 0.1005 | 9.47 |
| SMB | 0.0150 | 1.00 |
| HML | -0.0467 | -2.22 |
| RMW | -0.0178 | -0.62 |
| CMA | -0.0050 | -0.13 |
| MOM | 0.0469 | 3.79 |
