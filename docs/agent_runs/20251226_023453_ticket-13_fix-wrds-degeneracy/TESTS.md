# Tests

- `make test-fast`
  - Result: 113 passed (21.45s)
  - Warnings:
    - DeprecationWarning: `ExecModelCfg.aln` is deprecated; use `commission` instead.
    - FutureWarning: `Series.fillna(method=...)` deprecated in `reporting/analytics.py`.

## Additional runs (non-test)

- `WRDS_DATA_ROOT=$WRDS_DATA_ROOT microalpha wfv --config configs/wfv_flagship_wrds_smoke.yaml`
  - Result: Failed (non-degenerate constraints rejected all candidates).
- `WRDS_DATA_ROOT=$WRDS_DATA_ROOT microalpha wfv --config configs/wfv_flagship_wrds.yaml`
  - Result: Failed (non-degenerate constraints rejected all candidates).
