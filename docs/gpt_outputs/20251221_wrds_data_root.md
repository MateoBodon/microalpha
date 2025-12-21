# WRDS local data root (microalpha)

- **WRDS_DATA_ROOT:** `$WRDS_DATA_ROOT`
- **Layout observed:** `raw/`, `meta/`, `derived/`, `manifests/`.
- **Raw datasets present (examples):**
  - `raw/crsp/dsf_v2/dsf_v2_2013.parquet` … `dsf_v2_2024.parquet`
  - `raw/crsp/stocknames_v2.parquet`, `raw/crsp/dsenames.parquet`, `raw/crsp/dsedelist.parquet`
  - `raw/ff_all/*`, `raw/taq/*`, `raw/comp/*`, `raw/optionm/*`

## Derived outputs created for WRDS smoke run (2025-12-21)

These are **outside the repo** under `$WRDS_DATA_ROOT` and are safe to use for local runs:

- `crsp/daily_csv/` — per-symbol CSVs (40 symbols, permno strings) with columns `timestamp, close, volume`.
- `universes/flagship_sector_neutral.csv` — monthly snapshot universe for the smoke run, 2013–2019, with `symbol,date,close,adv_20,adv_63,adv_126,market_cap_proxy,sector`.
- `meta/crsp_security_metadata.csv` — symbol metadata (`symbol, adv, borrow_fee_annual_bps, spread_bps, volatility_bps`).

Notes:
- Symbols are **permno strings** (e.g., `10107`), not tickers.
- ADV values are computed from CRSP `prc × vol` rolling averages.
- This dataset is meant for **pipeline validation**, not performance claims.
- No raw WRDS exports are stored in the repo.
