# Tests

- (accidental) `make test-fast` — failed (run-log validator): missing `RESULTS.md`, `TESTS.md`, `META.json` before logs were initialized.
- `make test-fast` — failed: SyntaxError in `src/microalpha/reporting/baselines.py` (f-string typo).
- `make validate-runlogs` — passed.
- `make test-fast` — passed (126 tests). Warnings: pandas FutureWarnings (date_range freq='M'), ExecModelCfg.aln deprecation, analytics fillna deprecation.
