# Tests

## Failed
- `make test-fast` (WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds) → failed: empty `META.json` parse error in `scripts/validate_run_logs.py`.
- `make test-fast` → failed: `pytest` not found on PATH (system environment).
- `make wrds-flagship` (WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds) → failed: `Flagship universe file not found: /srv/data/wrds/universes/flagship_sector_neutral.csv`.

## Passed
- `make test-fast` (via `.venv/bin/pytest`).
- `make check-data-policy`.
- `make wrds-flagship` (WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds).
- `make report-wrds` (WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds).
- `make validate-runlogs`.
- `python3 tools/agentic/project_state_refresh.py --zip`.
