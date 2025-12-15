# Dataflow

## Inputs
- **Per‑symbol price CSVs**  
  - Location: `data/sample/prices/*.csv`, `data/public/prices/*.csv`, `data_sp500(_enriched)/*.csv`, `$WRDS_DATA_ROOT/crsp/daily_csv/*.csv`.  
  - Schema: datetime index/`timestamp` (parsed), `close` (required), optional `open/high/low/volume/ret/shares_out`.  
  - Used by `CsvDataHandler` / `MultiCsvDataHandler`.
- **Metadata**  
  - `data/sample/meta_sample.csv`, `data/public/meta_public.csv`, `metadata/sp500_enriched.csv`, `$WRDS_DATA_ROOT/meta/crsp_security_metadata.csv`.  
  - Columns: `symbol`, `adv`, `borrow_fee_annual_bps`, `spread_bps`, optional `volatility_bps`. Loaded via `market_metadata.load_symbol_meta` for slippage/borrow models and portfolio caps.
- **Universe files**  
  - `data/sample/universe_sample.csv`, `data/flagship_universe/FLAGSHIP_*.csv`, `$WRDS_DATA_ROOT/universes/flagship_sector_neutral.csv`.  
  - Columns: `symbol`, `date`, `sector`, optional liquidity stats; consumed by `FlagshipMomentumStrategy` to select eligible names.
- **Factors**  
  - `data/factors/ff3_sample.csv`, `data/factors/ff5_mom_daily.csv` used by reporting/factor regressions.
- **Configs**  
  - YAML files in `configs/` describe data paths, strategy params, execution, risk caps, walk‑forward windows, grids, and artifact roots. Env vars (`$WRDS_DATA_ROOT`, `$HOME`, `$ENVVAR`) are expanded by Pydantic.

## Processing & Intermediate Artefacts
- **Data handlers** slice date ranges per backtest/walk‑forward fold and stream events.
- **Strategies** maintain in‑memory price histories (e.g., Flagship keeps capped history for momentum/sector z‑scores).
- **Portfolio** produces `equity_curve` records and trade logs in memory before persistence.
- **Runner/WFV outputs** (written to `artifacts/<label>/<RUN_ID>/`):
  - `manifest.json`, copied `<config>.yaml`
  - `equity_curve.csv` with `timestamp,equity,exposure,returns`
  - `metrics.json`, `bootstrap.json`
  - `exposures.csv`, `factor_exposure.csv` (per fold for WFV plus final)
  - `trades.jsonl` (or `trades.csv` fallback)
  - Walk‑forward extras: `folds.json`, `grid_returns.csv`, optional `reality_check.json`.
- **Analytics outputs**:
  - `signals.csv` (WRDS signals builder) with `as_of, symbol, score, forward_return, adv, sector`
  - `artifacts/analytics/*_ic_series.csv`, `*_deciles.csv`, `*_rolling_betas.csv`
  - `artifacts/plots/*_{ic_ir|deciles|rolling_betas}.png`
  - SPA results `spa.json`, `spa.md`; factor tables `factors_ff5_mom.md`.

## Transform Pipelines
- **SP500 cleaning** (`scripts/augment_sp500.py`)  
  - Reads `data_sp500/*.csv`, fills non‑positive volumes, computes ADV (20/63/126), market‑cap proxy, writes cleaned prices to `data_sp500_enriched/`, metadata to `metadata/sp500_enriched.csv`, summary JSON to `reports/data_sp500_cleaning.json`.
- **Universe construction** (`scripts/build_flagship_universe.py`)  
  - Combines enriched SP500 prices + metadata; applies ADV/price/sector caps; writes monthly `FLAGSHIP_YYYY-MM-DD.csv` and concatenated `all.csv` to `data/flagship_universe/`; summary JSON to `reports/flagship_universe_summary.json`.
- **WRDS export** (`scripts/export_wrds_flagship.py`)  
  - Queries CRSP DSF via WRDS, computes total_return incl. delists, writes per‑symbol CSV (`crsp/daily_csv`), Parquet partitioned dataset (`crsp/dsf`), security metadata (`meta/crsp_security_metadata.csv`), and manifest (`data/wrds/manifest.json`) under `$WRDS_DATA_ROOT`.
- **WRDS signals** (`scripts/build_wrds_signals.py`)  
  - From WRDS universe CSV, computes 12‑1 momentum score and 1‑step forward return (skipping recent months, ADV filter), writes `signals.csv` (used for IC/IR analytics).

## Outputs & Publication
- **Reporting** writes PNGs/MD to artifacts or `reports/summaries/`. `report-wrds` copies curated images to `docs/img/wrds_flagship/<RUN_ID>` and updates `docs/results_wrds.md`.
- **Docs** (MkDocs) reference committed artifacts (sample runs + stored WRDS images) to keep site deterministic; raw WRDS data is never committed.

## Environment & Path Assumptions
- `WRDS_DATA_ROOT` must point to local WRDS export; configs interpolate it.
- `MICROALPHA_PROFILE` and `MICROALPHA_ARTIFACTS_DIR` guide profiling output.
- `METRICS_HAC_LAGS` can override HAC lag count at runtime.
- WRDS credentials expected via `~/.pgpass` (0600 perms) or `WRDS_USERNAME`.
