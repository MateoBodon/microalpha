# Tests

- `WRDS_DATA_ROOT=<EXTERNAL_STORAGE>/Data/wrds make wfv-wrds-smoke` (pass)
- `WRDS_DATA_ROOT=<EXTERNAL_STORAGE>/Data/wrds make report-wrds-smoke` (pass; warnings about pandas fillna and matplotlib tight_layout)
- `pytest -q` (not run in this follow-up)
