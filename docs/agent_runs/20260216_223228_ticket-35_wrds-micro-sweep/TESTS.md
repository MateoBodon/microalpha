# Tests

- [x] `python3 tools/agentic/validate_runlog.py --run-name 20260216_223228_ticket-35_wrds-micro-sweep`
  - Result: pass (`OK: /home/codex/repos/microalpha/docs/agent_runs/20260216_223228_ticket-35_wrds-micro-sweep`).

- [x] `python3 scripts/wrds_leaderboard.py --help`
  - Result: pass (CLI usage rendered).

- [x] `python3 scripts/wrds_leaderboard.py --out docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
  - Result: pass (leaderboard CSV/MD + best-line refreshed; best eligible run `2026-02-16T22-33-46Z-8d90621`).

- [x] `source .venv/bin/activate && make check-data-policy`
  - Result: pass (`Data policy check passed. Scanned 1073 files; allowlisted 57.`).

- [x] `source .venv/bin/activate && make test-fast`
  - Result: pass (`128 passed, 1 skipped`).
  - Note: an earlier run failed before pytest due incomplete `META.json` schema in this new run log; after `META.json` + `docs/CODEX_SPRINT_TICKETS.md` updates, `make test-fast` passed cleanly.
