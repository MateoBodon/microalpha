# Tests

- `make test-fast` (via `make test-fast && make check-data-policy && pytest -q tests/test_docs_links.py && make validate-runlogs && git status -sb`) **FAILED**
  - Error: missing run log files in `docs/agent_runs/20260126_023947_ticket-24b_finalize-wrds-refresh/` (RESULTS.md, TESTS.md, META.json).
- `make test-fast` (via `make test-fast && make check-data-policy && pytest -q tests/test_docs_links.py && make validate-runlogs && git status -sb`) **FAILED**
  - Error: `pytest` not found on PATH (no active venv).
- `source .venv/bin/activate && make test-fast && make check-data-policy && pytest -q tests/test_docs_links.py && make validate-runlogs && git status -sb` **PASSED**
  - `pytest -q`: 126 passed, 1 skipped (warning: deprecated ExecModelCfg.aln).
