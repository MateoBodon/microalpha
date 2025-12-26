# Tests

- `make test-fast`
  - Result: 114 passed (21.38s)
  - Warnings:
    - DeprecationWarning: `ExecModelCfg.aln` is deprecated; use `commission` instead.
    - FutureWarning: `Series.fillna(method=...)` deprecated in `reporting/analytics.py`.

## Debug runs (non-test)

- `WRDS_DATA_ROOT=$WRDS_DATA_ROOT microalpha wfv --config docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/wfv_flagship_wrds_single_fold.yaml`
  - Result: Failed (non-degenerate constraints rejected all candidates).
