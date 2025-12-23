# Tests

- `make test-fast` (fail: `test_holdout_selection_excludes_holdout_data` raised integrity error; fixed by setting `run_mode: dev` in the fixture)
- `make test-fast` (pass; 109 passed, 1 skipped)
- `WRDS_DATA_ROOT=$WRDS_DATA_ROOT make wfv-wrds-smoke` (pass)
- `WRDS_DATA_ROOT=$WRDS_DATA_ROOT make report-wrds-smoke` (pass; warnings: pandas fillna FutureWarning, matplotlib tight_layout)
- `WRDS_DATA_ROOT=$WRDS_DATA_ROOT make wfv-wrds` (pass)
- `WRDS_DATA_ROOT=$WRDS_DATA_ROOT make report-wrds` (pass; warnings: pandas fillna FutureWarning, matplotlib tight_layout)
- `make test-fast` (pass; 110 passed; warnings: pandas fillna FutureWarning, ExecModelCfg.aln deprecation)
- `pytest -q` (pass; 110 passed; warnings: pandas fillna FutureWarning, ExecModelCfg.aln deprecation)
- `WRDS_DATA_ROOT=$WRDS_DATA_ROOT make wfv-wrds-smoke` (pass)
- `WRDS_DATA_ROOT=$WRDS_DATA_ROOT make report-wrds-smoke` (pass; warnings: pandas fillna FutureWarning, matplotlib tight_layout)
