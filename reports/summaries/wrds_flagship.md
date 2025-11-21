# WRDS Flagship Walk-Forward

## Headline Metrics

| Metric | Value |
| --- | ---:|
| Sharpe_HAC | 0.40 |
| MAR | 0.04 |
| MaxDD | 82.35% |
| Turnover | $1,837,084,905 |
| RealityCheck_p_value | 0.986 |
| SPA_p_value | 0.603 |

## Visuals

![Equity Curve](../../docs/img/wrds_flagship/2025-11-21T00-28-22Z-54912a8/equity_curve.png)

![Bootstrap Sharpe Histogram](../../docs/img/wrds_flagship/2025-11-21T00-28-22Z-54912a8/bootstrap_hist.png)

![SPA Comparator t-stats](../../docs/img/wrds_flagship/2025-11-21T00-28-22Z-54912a8/spa_tstats.png)

## Hansen SPA Summary

- **Best model:** allocator_kwargs={'risk_model': 'equal'}|lookback_months=9|skip_months=2|top_frac=0.2000
- **Observed max t-stat:** 0.979
- **p-value:** 0.603
- **Bootstrap draws:** 2000 (avg block 63)

| Comparator | Mean Diff | t-stat |
| --- | ---:| ---:|
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=12|skip_months=1|top_frac=0.2000 | 0.0030 | 0.89 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=12|skip_months=1|top_frac=0.3000 | 0.0030 | 0.88 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=12|skip_months=2|top_frac=0.2000 | 0.0031 | 0.90 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=12|skip_months=2|top_frac=0.3000 | 0.0031 | 0.90 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=18|skip_months=1|top_frac=0.2000 | 0.0033 | 0.95 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=18|skip_months=1|top_frac=0.3000 | 0.0032 | 0.94 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=18|skip_months=2|top_frac=0.2000 | 0.0033 | 0.97 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=18|skip_months=2|top_frac=0.3000 | 0.0033 | 0.97 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=9|skip_months=1|top_frac=0.2000 | 0.0026 | 0.76 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=9|skip_months=1|top_frac=0.3000 | 0.0026 | 0.76 |
| allocator_kwargs={'risk_model': 'equal'}|lookback_months=9|skip_months=2|top_frac=0.3000 | 0.0024 | 0.65 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=12|skip_months=1|top_frac=0.2000 | 0.0030 | 0.89 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=12|skip_months=1|top_frac=0.3000 | 0.0030 | 0.88 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=12|skip_months=2|top_frac=0.2000 | 0.0031 | 0.90 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=12|skip_months=2|top_frac=0.3000 | 0.0031 | 0.89 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=18|skip_months=1|top_frac=0.2000 | 0.0032 | 0.95 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=18|skip_months=1|top_frac=0.3000 | 0.0032 | 0.93 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=18|skip_months=2|top_frac=0.2000 | 0.0033 | 0.98 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=18|skip_months=2|top_frac=0.3000 | 0.0033 | 0.97 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=9|skip_months=1|top_frac=0.2000 | 0.0027 | 0.78 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=9|skip_months=1|top_frac=0.3000 | 0.0025 | 0.74 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=9|skip_months=2|top_frac=0.2000 | 0.0000 | 0.26 |
| allocator_kwargs={'risk_model': 'risk_parity'}|lookback_months=9|skip_months=2|top_frac=0.3000 | 0.0024 | 0.67 |

## Factor Attribution (FF5+MOM)

| Factor | Beta | t-stat |
| --- | ---:| ---:|
| Alpha | 0.0008 | 1.15 |
| Mkt_RF | 1.0570 | 6.52 |
| SMB | -0.2939 | -1.78 |
| HML | -0.2257 | -1.26 |
| RMW | -0.3265 | -1.36 |
| CMA | -0.7185 | -1.79 |
| MOM | 0.4449 | 4.25 |
