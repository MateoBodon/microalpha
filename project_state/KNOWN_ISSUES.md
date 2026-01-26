# Known Issues

- WRDS pipelines require local exports and are blocked without `WRDS_DATA_ROOT` (see `docs/wrds.md`).
- `make export-wrds` requires `~/.pgpass` with 0600 perms and network access to WRDS.
- Large data directories (`data_sp500/`, `data_sp500_enriched/`) are present; avoid deep parsing in automation.
