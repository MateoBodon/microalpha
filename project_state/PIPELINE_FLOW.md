# Pipeline Flow

## Single Backtest (`microalpha run`)
- **Entry**: `microalpha run -c configs/<name>.yaml [--out <dir>]` or `run.py`.
- **Steps**: parse YAML → build DataHandler (single or multi) → Strategy → Portfolio (risk caps, capital policy) → Executor/Broker → `Engine.run`.
- **Artifacts**: `manifest.json`, `<config>.yaml` copy, `equity_curve.csv`, `metrics.json`, `bootstrap.json`, `exposures.csv`, `factor_exposure.csv`, `trades.jsonl|csv`, optional `profile.pstats`.
- **Outputs directory**: `artifacts/<cfg-stem>/<RUN_ID>/` (configurable via `artifacts_dir` or CLI `--out`).

## Walk‑Forward Validation (`microalpha wfv`)
- **Entry**: `microalpha wfv -c configs/wfv_*.yaml [--out <dir>]` or `walk_forward.py`.
- **Steps per fold**:
  1) Set training/testing windows from `walkforward` block.
  2) Grid search over `grid` parameters using in‑sample data (`_optimise_parameters`).
  3) Reality‑check bootstrap across models (`bootstrap_reality_check`) with stationary/circular blocks.
  4) Run OOS test with best params; collect metrics, exposures, factor summaries.
  5) Append fold metadata.
- **Aggregations**: equity concatenation → `metrics.json`; `folds.json`; `grid_returns.csv`; `bootstrap.json`; optional `reality_check.json`; exposures/factor CSVs per fold + final.
- **Artifacts**: under `artifacts/<label>/<RUN_ID>/`.

## Reporting (`microalpha report`)
- **Entry**: `microalpha report --artifact-dir <dir> [--summary-out ... --title ...]`.
- **Steps**: read metrics/bootstraps/equity → render equity & drawdown PNG + bootstrap histogram (`tearsheet`) → generate Markdown summary (`summary`) with exposures table; auto‑inject FF3 factor table for sample WFV if factors present.
- **Outputs**: `equity_curve.png`, `bootstrap_hist.png`, summary MD (default `reports/summaries/flagship_mom.md`).

## WRDS Flagship (full pipeline via `make wrds-flagship`)
- **Entry**: `make wfv-wrds` (requires `WRDS_DATA_ROOT`, updated `configs/wfv_flagship_wrds.yaml`), then `make report-wrds`.
- **Run phase**: same WFV flow but large dataset; artifacts to `artifacts/wrds_flagship/<RUN_ID>/`.
- **Report phase**:
  - Build signals from WRDS universe (`scripts/build_wrds_signals.py`) → `signals.csv`.
  - Analytics (`reports/analytics.py`) → IC/IR/decile/beta CSVs + plots under `artifacts/analytics` & `artifacts/plots`.
  - Factor regression (`reports/factors.py`) → `factors_ff5_mom.md`.
  - Tearsheet (`reports/tearsheet.py`) → equity/bootstrap PNGs.
  - SPA (`reports/spa.py`) → `spa.json` + `spa.md`.
  - Compose WRDS summary (`reports/render_wrds_flagship.py` / `reporting.wrds_summary`) → `reports/summaries/wrds_flagship*.md` and update `docs/results_wrds.md`, copy images to `docs/img/wrds_flagship/<RUN_ID>`.

## Sample/Public Quickstarts
- **Sample single run**: `make sample` → `configs/flagship_sample.yaml` with bundled `data/sample`.
- **Sample WFV**: `make wfv` → `configs/wfv_flagship_sample.yaml`; `make report-wfv` regenerates summary with factor table.
- **Public mini‑panel**: `microalpha wfv --config configs/wfv_flagship_public.yaml --out artifacts/public_wfv`; report same as above.

## Data Preparation Scripts
- **SP500 cleaning**: `scripts/augment_sp500.py --source data_sp500 --dest data_sp500_enriched ...` cleans volumes, computes ADV/market‑cap proxy, writes enriched CSVs + metadata JSON/CSV.
- **Universe build**: `scripts/build_flagship_universe.py --data-dir data_sp500_enriched --metadata metadata/sp500_enriched.csv --out-dir data/flagship_universe ...` writes monthly universe CSVs + summary.
- **WRDS export**: `scripts/export_wrds_flagship.py` (requires WRDS credentials and `WRDS_DATA_ROOT`) → per‑symbol CSV/Parquet under `$WRDS_DATA_ROOT`, security metadata CSV, manifest.
- **WRDS signals**: `scripts/build_wrds_signals.py --universe <csv> --output <signals.csv>` computes momentum scores/forward returns for analytics pipeline.

## Analytics & Visualisation Extras
- **wfv_report.py**: plots per‑fold train/test Sharpes and best‑param scatter from `folds.json`.
- **html_report.py**: Plotly interactive report from `equity_curve.csv` + optional trades.
- **plot_mm_spread.py**: runs MM config variants (LOB vs TWAP) and plots realised spread vs inventory.

