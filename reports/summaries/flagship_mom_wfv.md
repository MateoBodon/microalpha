# Flagship Walk-Forward

## Performance Snapshot

| Metric | Value |
| --- | ---:|
| Sharpe_HAC | 0.23 |
| MAR | 0.03 |
| MaxDD | 34.79% |
| Turnover | $28,525,695 |
| RealityCheck_p_value | 1.000 |

## Exposure Summary

| Metric | Value |
| --- | ---:|
| Avg net exposure | 17.37% |
| Avg gross exposure | 158.60% |
| Max gross exposure | 403.02% |
| Max net exposure | 163.52% |

_Exposure time series is recorded in equity_curve.csv._

## Visuals

![Equity Curve](../../artifacts/sample_wfv/2025-12-23T18-39-59Z-82c14dc/equity_curve.png)

![Bootstrap Sharpe Histogram](../../artifacts/sample_wfv/2025-12-23T18-39-59Z-82c14dc/bootstrap_hist.png)

## Bootstrap Reality Check

- Samples: 6400
- Mean Sharpe: 0.00
- Std: 0.00
- 95% CI: [0.00, 0.00]
- p-value: 1.000

## Top Exposures

| Symbol | Qty | Market Value | Weight |
| --- | ---:| ---:| ---:|
| ZETA | 42204 | $1,143,721 | 112.65% |
| BETA | 31525 | $754,333 | 74.30% |
| GAMM | -18684 | $-590,860 | -58.20% |
| ALFA | -6175 | $-528,997 | -52.10% |

## Factor Regression (FF3 sample)

| Factor | Beta | t-stat |
| --- | ---:| ---:|
| Alpha | -0.0051 | -1.27 |
| Mkt_RF | 11.1851 | 1.85 |
| SMB | -1.3603 | -0.12 |
| HML | -13.5354 | -0.82 |

_Computed against `data/factors/ff3_sample.csv` using Newey-West standard errors._

## Cost & Metadata Robustness

_Robustness artifacts unavailable._
