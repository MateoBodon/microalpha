# Tests

- `source .venv/bin/activate && make test-fast` (fail: missing required run-log files in `docs/agent_runs/20260125_224419_ticket-23_wrds-holdout-nonzero-trades/`)
- `source .venv/bin/activate && make check-data-policy` (pass)
- `source .venv/bin/activate && make test-fast` (pass; 126 passed, 1 skipped)
