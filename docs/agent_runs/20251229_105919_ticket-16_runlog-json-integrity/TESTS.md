# Tests

1. `make test-fast`
   - Result: success (validator OK, 119 passed).
   - Warnings:
     - DeprecationWarning: `ExecModelCfg.aln` deprecated (use `commission`).
     - FutureWarning: `Series.fillna(method=...)` deprecation in `reporting/analytics.py`.

2. `make validate-runlogs`
   - Result: success.

3. `python3 -m compileall tools scripts`
   - Result: success.
