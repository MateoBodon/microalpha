# Tests

- [x] `python3 tools/agentic/validate_runlog.py --run-name 20260216_223228_ticket-35_wrds-micro-sweep`
  - Result: pass.

- [x] `python3 scripts/wrds_leaderboard.py --out docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
  - Result: pass (wrote `leaderboard.csv`, `leaderboard.md`, `resume_line_best.md`; best eligible run is `2026-02-16T22-33-46Z-8d90621`).

- [x] `make check-data-policy`
  - Result: pass (`Data policy check passed. Scanned 1073 files; allowlisted 57.`).

- [x] `make test-fast` (attempt 1)
  - Result: fail at run-log validation due missing required `META.json` keys in `docs/agent_runs/20260216_232907_ticket-ticket-36/`.
  - Failure detail: required keys included `ticket_id`, `started_at_utc`, `finished_at_utc`, `git_sha_before`, `git_sha_after`, `branch_name`, `dataset_id`, and list/dict schema fields.

- [x] `python3 tools/agentic/validate_runlog.py --run-name 20260216_232907_ticket-ticket-36`
  - Result: pass (`OK: /home/codex/repos/microalpha/docs/agent_runs/20260216_232907_ticket-ticket-36`).

- [x] `make test-fast` (attempt 2 after run-log schema fix)
  - Result: pass (`128 passed, 1 skipped, 1 warning`).
