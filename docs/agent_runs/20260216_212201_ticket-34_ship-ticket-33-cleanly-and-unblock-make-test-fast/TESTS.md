# Tests

- [x] `python3 tools/agentic/validate_runlog.py --run-name 20260216_033516_ticket-33_wrds-realdata-leaderboard`
  - Result: pass (`OK: /home/codex/repos/microalpha/docs/agent_runs/20260216_033516_ticket-33_wrds-realdata-leaderboard`).

- [x] `python3 tools/agentic/validate_runlog.py --run-name 20260216_212201_ticket-34_ship-ticket-33-cleanly-and-unblock-make-test-fast`
  - Result: pass (`OK: /home/codex/repos/microalpha/docs/agent_runs/20260216_212201_ticket-34_ship-ticket-33-cleanly-and-unblock-make-test-fast`).

- [x] `python3 scripts/wrds_leaderboard.py --help`
  - Result: pass (CLI usage rendered correctly).

- [x] `python3 scripts/wrds_leaderboard.py --out docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
  - Result: pass (wrote leaderboard CSV/MD and `resume_line_best.md`; best eligible run remained `2026-01-27T04-47-22Z-31fe553`).

- [x] `PATH=/home/codex/repos/microalpha/.venv/bin:$PATH make test-fast` (attempt 1)
  - Result: fail at `tests/test_data_policy.py::test_data_policy_check` after run-log validation succeeded.
  - Failure detail: missing allowlist entries for `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/manifest_excerpt.json` and `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/metrics.json`.

- [x] `PATH=/home/codex/repos/microalpha/.venv/bin:$PATH make test-fast` (attempt 2, after allowlist fix)
  - Result: pass (`128 passed, 1 skipped, 1 warning`).

- [x] `PATH=/home/codex/repos/microalpha/.venv/bin:$PATH make test-fast` (final confirmation after run-log/doc updates)
  - Result: pass (`128 passed, 1 skipped, 1 warning`).
