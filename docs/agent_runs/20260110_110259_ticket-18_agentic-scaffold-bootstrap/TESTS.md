# Tests

- `make test-fast` (failed):
  - `docs/agent_runs/20260110_110259_ticket-18_agentic-scaffold-bootstrap` missing required files (`COMMANDS.md`, `RESULTS.md`, `TESTS.md`, `META.json`).
- `make test-fast` (timed out after 10s tool timeout):
  - `scripts/validate_run_logs.py` succeeded; `pytest -q` started but was interrupted by the CLI timeout.
- `make test-fast` (passed, 51s):
  - 126 tests passed.
  - Warnings: Matplotlib cache/font warnings (non-writable `~/.matplotlib`), pandas `date_range` monthly freq deprecation, config `ExecModelCfg.aln` deprecation, and `fillna(method=...)` future warning in reporting analytics.
- `make test-fast` (timed out after 10s tool timeout; accidental rerun while rewriting COMMANDS.md).
