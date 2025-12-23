# WRDS / CRSP Integration

Microalpha can operate directly on WRDS-hosted CRSP equities data. This guide describes the
expected directory layout, mandatory columns, and the licensing caveats you must observe before
pointing the engine at production-quality datasets.

## Data Layout

Set the `template.data_path` field in ``configs/wfv_flagship_wrds.yaml`` to a directory containing per-symbol pricing files exported from WRDS/CRSP. Each file can be CSV
or Parquet and must be named `SYMBOL.ext` (upper-case ticker symbols). Microalpha expects the
following schema:

| Column | Description | Type | Frequency |
| --- | --- | --- | --- |
| `date` | Trading day in ISO format (`YYYY-MM-DD`) | date | Daily (NYSE calendar) |
| `open`, `high`, `low`, `close` | Split- and dividend-adjusted prices | float | Daily |
| `volume` | Shares traded | float/int | Daily |
| `ret` | Total return for the period (optional; used for QA) | float | Daily |
| `shares_out` | Shares outstanding (optional; feeds ADV calc) | float | Daily |

All files should share the same timezone (New York). Missing trading days must be forward-filled
by WRDS; Microalpha will drop dates that are absent in the price file.

## Metadata & Universe

Set `template.meta_path` to a CSV exported from WRDS security master (`crsp.stocknames`). The
file must contain at least:

- `symbol` – ticker symbol (upper-case).
- `permno` – CRSP permanent number.
- `sic` or `gics_sector` – sector/industry classification used for turnover limits.
- `delist_date` – optional; if present Microalpha will stop trading on the delisting day.

Provide a universe file via `strategy.params.universe_path`. A minimal file contains `symbol`
and optional `sector` columns. You can export the CRSP constituents you care about and roll
them forward to the testing window (e.g., keep entries where `namedt <= test_end < nameendt`).

## Survivorship & Corporate Actions

- Download *full-history* panels from WRDS to avoid survivorship bias. Do not pre-filter the
  security master to only active listings.
- Use WRDS adjustment factors (e.g., `ajex`, `cfacpr`) to back-adjust prices for splits and
  distribute dividends via the bundled total-return column.
- When running walk-forward, ensure any share-class mergers are handled in your universe file.

## Licensing & Access Controls

- WRDS/CRSP data is licensed content. Do **not** commit any of it to this repository or build
  artifacts.
- The provided Makefile targets expect `WRDS_DATA_ROOT` to point at your local export. Paths are
  interpolated from that env var in `configs/wfv_flagship_wrds.yaml` (no hardcoded directories).
- For this machine, the local WRDS export root is documented in `docs/local/WRDS_DATA_ROOT.md`.
- Store your WRDS credentials outside the repo (environment variables or `.pgpass`). Microalpha
  only consumes local CSV/Parquet exports and does not connect to WRDS directly.

## Flagship WRDS walk-forward defaults

The flagship momentum configuration (`configs/wfv_flagship_wrds.yaml`) encodes the study described
in Plan.md and the docs. Key defaults:

- Data window: **2005-01-03 → 2024-12-31**.
- Walk-forward windows: **36 months training** (`training_days=756`) then **12 months testing**
  (`testing_days=252`) per fold.
- Strategy: 12–1 sector-neutral momentum with ADV and price filters (`min_adv=50MM`,
  `min_price=12`), turnover target capped at **3% of ADV**, max **8 names per sector**, and bottom sleeve fixed at 20%.
- Grid: `lookback_months ∈ {9,12,18}`, `skip_months ∈ {1,2}`, `top_frac ∈ {0.20,0.30}`,
  allocator risk model ∈ {`risk_parity`, `equal`} (bottom_frac remains 0.20).
- Artefacts root: `artifacts/wrds_flagship/<RUN_ID>`; summaries land in
  `reports/summaries/wrds_flagship*.md` and docs assets under `docs/img/wrds_flagship/<RUN_ID>`.
- Risk caps baked into the template: gross exposure ≤ **1.25x**, drawdown stop at **20%**, portfolio heat ≤ **1.5x equity**, turnover cap **$180MM** per fold, and volatility-scaling target of **$225k** daily dollar-vol with a 21-day lookback.

## Recommended Workflow

1. Export CRSP/Compustat data to a local directory (`/wrds/crsp/<project>`).
2. Ensure `WRDS_DATA_ROOT` points at the export root (paths inside the YAML are env-expanded).
3. Run `make wrds-flagship` to execute the walk-forward grid and build the summary/plots; artefacts
   will appear under `artifacts/wrds_flagship/<RUN_ID>`.
4. Optionally run `make report-wrds` again to refresh docs after inspecting the artefacts or
   tweaking plots.

By keeping raw data outside the repository and documenting every transformation, you maintain a
clear audit trail while respecting WRDS licensing requirements.
