# Tests

- `python3 tools/agentic/project_state_refresh.py --zip && make test-fast` (failed):
  - `scripts/validate_run_logs.py` reported missing run-log files for this run.
- `python3 tools/agentic/project_state_refresh.py --zip && make test-fast` (passed):
  - 126 tests passed.
  - Warnings: Matplotlib cache dir not writable/font cache build; pandas monthly freq 'M' deprecation; `ExecModelCfg.aln` deprecation; `fillna(method=...)` deprecation.
- Notes: `project_state_refresh.py` emitted a `datetime.utcnow()` deprecation warning.
