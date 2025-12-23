# WRDS Flagship Walk-Forward

## Headline Metrics

| Metric | Value |
| --- | ---:|
| Sharpe_HAC | 0.00 |
| MAR | 0.00 |
| MaxDD | 0.00% |
| Turnover | $0 |
| RealityCheck_p_value | 1.000 |
| SPA_p_value | n/a |

## Run is degenerate

This run is not interpretable for performance claims:
- num_trades == 0 (no executed trades)
- returns variance is zero (flat equity curve)

## Exposure Summary

| Metric | Value |
| --- | ---:|
| Avg net exposure | 0.00% |
| Avg gross exposure | 0.00% |
| Max net exposure | 0.00% |
| Max gross exposure | 0.00% |

_Exposure time series is recorded in equity_curve.csv._

## Cost Breakdown

| Category | Total |
| --- | ---:|
| Commission | $0 |
| Slippage | $0 |
| Borrow | n/a |
| Total | $0 |

## Visuals

![Equity Curve](../../docs/img/wrds_flagship/2025-12-23T19-40-24Z-ff2979d/equity_curve.png)

![Bootstrap Sharpe Histogram](../../docs/img/wrds_flagship/2025-12-23T19-40-24Z-ff2979d/bootstrap_hist.png)

![SPA Comparator t-stats](../../docs/img/wrds_flagship/2025-12-23T19-40-24Z-ff2979d/spa_tstats.png)

## Hansen SPA Summary

SPA degenerate: all strategies have zero variance

## Factor Attribution (FF5+MOM)

| Factor | Beta | t-stat |
| --- | ---:| ---:|
| Alpha | -0.0000 | -10.98 |
| Mkt_RF | 0.0000 | 0.10 |
| SMB | 0.0002 | 0.89 |
| HML | 0.0006 | 2.01 |
| RMW | 0.0002 | 0.68 |
| CMA | -0.0007 | -1.48 |
| MOM | 0.0001 | 0.58 |
