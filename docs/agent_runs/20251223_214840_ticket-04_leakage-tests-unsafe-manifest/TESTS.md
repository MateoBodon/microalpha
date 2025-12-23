# Tests

- `pytest -q tests/test_no_lookahead.py` (failed: FileExistsError creating tmp_path/data on second config write; fixed by allowing `exist_ok=True`)
- `pytest -q tests/test_no_lookahead.py` (passed; 3 tests)
- `make test-fast` (passed; 112 tests). Warnings:
  - DeprecationWarning: ExecModelCfg.aln is deprecated (tests/test_cfg_unify.py)
  - FutureWarning: pandas Series.fillna(method=...) in reporting/analytics.py
