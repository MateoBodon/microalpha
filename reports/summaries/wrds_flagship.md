# WRDS Flagship Walk-Forward

## Headline Metrics

| Metric | Value |
| --- | ---:|
| Sharpe_HAC | 0.46 |
| MAR | -0.01 |
| MaxDD | 93.20% |
| Turnover | $2,229,998,821 |
| RealityCheck_p_value | 0.908 |
| SPA_p_value | 0.454 |

## Visuals

![Equity Curve](../../docs/img/wrds_flagship/2025-11-12T08-51-11Z-65187e4/equity_curve.png)

![Bootstrap Sharpe Histogram](../../docs/img/wrds_flagship/2025-11-12T08-51-11Z-65187e4/bootstrap_hist.png)

## Hansen SPA Summary

- **Best model:** top_frac=0.2500|turnover_target_pct_adv=0.1000
- **Observed max t-stat:** 1.724
- **p-value:** 0.454
- **Bootstrap draws:** 2000 (avg block 63)

| Comparator | Mean Diff | t-stat |
| --- | ---:| ---:|
| top_frac=0.2500|turnover_target_pct_adv=0.1400 | 0.0000 | 0.00 |
| top_frac=0.3500|turnover_target_pct_adv=0.1000 | 0.0042 | 1.72 |
| top_frac=0.3500|turnover_target_pct_adv=0.1400 | 0.0042 | 1.72 |

## Factor Attribution (FF5+MOM)

| Factor | Beta | t-stat |
| --- | ---:| ---:|
| Alpha | 0.0007 | 0.61 |
| Mkt_RF | 2.2319 | 6.28 |
| SMB | 0.3238 | 1.35 |
| HML | -0.7878 | -2.87 |
| RMW | -0.6352 | -2.11 |
| CMA | -0.3157 | -0.76 |
| MOM | 0.3266 | 1.64 |
