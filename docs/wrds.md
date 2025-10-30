# WRDS / CRSP Integration

Microalpha can operate directly on WRDS-hosted CRSP equities data. This guide describes the
expected directory layout, mandatory columns, and the licensing caveats you must observe before
pointing the engine at production-quality datasets.

## Data Layout

Set the `template.data_path` field in [`configs/wfv_flagship_wrds.yaml`](../configs/wfv_flagship_wrds.yaml)
to a directory containing per-symbol pricing files exported from WRDS/CRSP. Each file can be CSV
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
- The provided Makefile target `wrds` will refuse to run until you replace the placeholder
  values in `configs/wfv_flagship_wrds.yaml`.
- Store your WRDS credentials outside the repo (environment variables or `.pgpass`). Microalpha
  only consumes local CSV/Parquet exports and does not connect to WRDS directly.

## Recommended Workflow

1. Export CRSP/Compustat data to a local directory (`/wrds/crsp/<project>`).
2. Update `configs/wfv_flagship_wrds.yaml` with the absolute paths from step 1.
3. Run `make wrds` to produce walk-forward artifacts under `artifacts/wrds_flagship/`.
4. Execute `microalpha report --artifact-dir <artifact>` to render summaries and visuals.

By keeping raw data outside the repository and documenting every transformation, you maintain a
clear audit trail while respecting WRDS licensing requirements.
