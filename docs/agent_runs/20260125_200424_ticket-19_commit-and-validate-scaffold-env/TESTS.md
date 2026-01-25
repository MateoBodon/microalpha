# Tests

- `source .venv/bin/activate && make test-fast` (failed): pandas 3 no longer accepts `freq="M"` in `tests/test_baselines.py`.
- `source .venv/bin/activate && make test-fast` (failed): multi-asset union timestamps mis-scaled (1970 dates) until datetime indexes were coerced to ns.
- `source .venv/bin/activate && make test-fast` (failed): pandas 3 removed `fillna(method=...)` in analytics timestamp handling.
- `source .venv/bin/activate && make test-fast` (passed): 125 passed, 1 skipped. Warnings: Matplotlib cache dir not writable (`MPLCONFIGDIR`), `ExecModelCfg.aln` deprecation.
