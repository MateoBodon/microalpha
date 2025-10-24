Results (Preview)

This page summarizes representative results produced by Microalpha’s cross-sectional strategies. Full reproducibility instructions are included; WRDS-derived datasets are not redistributed.

Cross-Sectional Momentum (Public Subset)

- Universe: Top 10 US tickers (SPY, AAPL, MSFT, GOOG, AMZN, META, NVDA, TSLA, JPM, V)
- Period: 2015–2020
- Execution: TWAP, commission = 1 bps
- Parameters: 12-1 momentum, top 30%, volatility targeting 10%

Artifacts produced:
- Equity vs SPY overlay
- Drawdown and exposure panels
- Rolling 252d Sharpe
- Summary table (Sharpe, Sortino, Calmar, alpha/beta, IR, turnover/day)

Cross-Sectional Momentum (WRDS CRSP – Flagship)

- Universe: S&P 500 constituents (rolling membership), 2005–2025
- Execution: TWAP, commission schedule (bps), square-root impact defaults
- WFV: 1y train / 1q test rolling folds

Outputs mirror the public subset but at larger scale, with fold tables and SPA p-values.

Note: WRDS-derived CSVs are prepared locally via scripts/wrds_crsp_prep.py and are not committed to the repository.

Reproduction

- Public: python scripts/fetch_public_data.py SPY AAPL MSFT ... --out data then microalpha wfv -c configs/wfv_xsec_mom.yaml
- WRDS: python scripts/wrds_crsp_prep.py --universe sp500.txt --out data_sp500 then update data_path and run the same WFV.

