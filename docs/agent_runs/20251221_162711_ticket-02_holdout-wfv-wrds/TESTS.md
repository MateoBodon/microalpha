# Tests

- `WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make wfv-wrds-smoke` (pass)
- `WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make report-wrds-smoke` (pass; warnings about pandas fillna and matplotlib tight_layout)
- `pytest -q` (not run in this follow-up)
