# Tests

- FAIL: `PATH=.venv/bin:$PATH make test-fast`
  - Error: run-log validator rejected empty git_sha_before/git_sha_after in `docs/agent_runs/20260125_205959_ticket-22_wrds-resume-metrics/META.json`.
- PASS: `PATH=.venv/bin:$PATH make check-data-policy`
- PASS: `PATH=.venv/bin:$PATH make test-fast`
  - Warnings: Matplotlib cache dir under `/home/codex/.config` not writable; cached in `/tmp`.
