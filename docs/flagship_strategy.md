# Flagship Strategy Blueprint

## Objectives
- Deliver a **cross-sectional momentum** product that survives institutional scrutiny.
- Target annualised Sharpe > **1.2**, max drawdown < **10%**, turnover manageable (< 400% annual).
- Showcase realistic execution (VWAP/TWAP with volume slippage) and portfolio risk controls (volatility scaling, sector neutrality, turnover heat).

## Data Preparation (scripts)

1. **Augment the raw panel** – fill volume gaps and extract liquidity stats:

   ```bash
   python scripts/augment_sp500.py --source data_sp500 --dest data_sp500_enriched \
       --sector-map metadata/sp500_sector_overrides.csv \
       --metadata-output metadata/sp500_enriched.csv \
       --summary-output reports/data_sp500_cleaning.json
   ```

2. **Build the monthly universe** – apply price/liquidity/sector filters and cap exposures:

   ```bash
   python scripts/build_flagship_universe.py --data-dir data_sp500_enriched \
       --metadata metadata/sp500_enriched.csv \
       --out-dir data/flagship_universe \
       --min-dollar-volume 15000000 --top-n 120 --start-date 2012-01-01
   ```

3. **Run configs** – use `configs/flagship_mom.yaml` for single runs and `configs/wfv_flagship_mom.yaml` for walk-forward analysis. The CLI run can take tens of minutes:

   ```bash
   python -m microalpha.cli run -c configs/flagship_mom.yaml --out artifacts/flagship_single
   ```

## Universe & Data
- Universe: top 450 US equities by 20-day average dollar volume, rebalanced monthly, drawn from `data_sp500/` (post-processed for liquidity, sector metadata).
- Exclusions: remove tickers with missing/zero volume, corporate actions unresolved, or price below $5.
- Metadata augmentations:
  - Sector classification (GICS / NAICS) for neutralisation and concentration checks.
  - Market capitalisation or shares outstanding to enable size filters.

## Signals
1. **Momentum Leg**
   - 12-1 total return (skip most recent 21 trading days) measured over trailing 252 days.
   - Normalize within sector; rank to pick top `q_long` and bottom `q_short` per month.
2. **Quality Filter (optional)**
   - Optional overlay: trailing realised volatility or idiosyncratic residual to avoid recent blowups.
3. **Liquidity Filter**
   - Enforce minimum 20-day ADV threshold.

## Portfolio Construction
- Long-short with net exposure ~0 (target equal-weighted, risk scaled by volatility).
- Risk sizing: `VolatilityScaledPolicy` to target $20k daily dollar vol per position.
- Sector caps: max 3 names per sector in each sleeve.
- Turnover limit: < 10% of ADV per rebalance; soft cap via `turnover_cap` and portfolio heat.

## Execution
- VWAP executor with 4 slices, pulling volume via `DataHandler.get_volume_at`.
- Volume-based slippage: `impact = 5e-4` to mimic 50 bps impact on 10% ADV trade.
- Commission assumption: $0.0005/share.

## Walk-Forward Design
- Period: 2010-01-01 to 2024-12-31.
- Training window: 504 trading days (~2 years).
- Testing window: 126 trading days (~6 months).
- Grid search over:
  - Momentum lookback: {6, 9, 12} months.
  - Skip window: {1, 2} months.
  - Percentile for longs/shorts: {0.2, 0.25, 0.3} of universe.
  - Volatility target: {10k, 20k, 30k} dollar vol.
- Metrics captured per fold: Sharpe, Sortino, max drawdown, turnover, win rate, SPA p-value.

## Success Metrics
- Out-of-sample (WFV average) Sharpe ≥ 0.8.
- Worst fold Sharpe > 0.
- Max drawdown ≤ 12% across folds.
- Annualised turnover < 4x.
- Hit rate > 50% on trades with positive expectancy.

## Deliverables
1. **Code**
   - `src/microalpha/strategies/flagship_mom.py`
   - Configs: `configs/flagship_mom.yaml`, `configs/wfv_flagship_mom.yaml`
   - Data prep script: `scripts/build_flagship_universe.py`
2. **Tests**
   - Strategy smoke test, ranking logic, risk sizing invariants, data prep validation.
3. **Artifacts**
   - Updated `reports/generate_summary.py` to include flagship runs.
   - Plots (PNG/HTML) for equity, drawdown, per-fold Sharpe, turnover vs. PnL.
4. **Docs**
   - README additions summarising methodology and reproducibility command.
   - `docs/flagship_strategy.md` (this file) kept in sync with implementation.

## Open Questions
- Source for up-to-date sector & shares-outstanding metadata.
- Handling of corporate events (splits, mergers) in `data_sp500/` pipeline.
- Whether to include transaction cost model beyond linear + volume slippage (e.g., borrow costs).
