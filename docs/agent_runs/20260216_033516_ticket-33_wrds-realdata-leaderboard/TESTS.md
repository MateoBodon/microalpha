# Tests

- [x] `python3 tools/agentic/validate_runlog.py --run-name 20260216_033516_ticket-33_wrds-realdata-leaderboard`
  - Result: pass (`OK: /home/codex/repos/microalpha/docs/agent_runs/20260216_033516_ticket-33_wrds-realdata-leaderboard`).

- [x] `python3 scripts/wrds_leaderboard.py --help`
  - Result: pass (CLI usage rendered correctly).

- [x] `python3 scripts/wrds_leaderboard.py --out docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
  - Result: pass (rewrote leaderboard CSV/MD and best-line artifact; selected best eligible run `2026-01-27T04-47-22Z-31fe553`).

- [x] `python3 -m py_compile scripts/wrds_leaderboard.py`
  - Result: pass (syntax check).

- [ ] `PATH=/home/codex/repos/microalpha/.venv/bin:$PATH make test-fast`
  - Result: fail before pytest due pre-existing run-log schema issues in `docs/agent_runs/20260216_025221_ticket-ticket-32b/META.json`.
  - Key failure lines:
    - `missing required key 'finished_at_utc'`
    - `ticket_id 'ticket-32b' is not in ticket-XX format`
    - `config_paths must be a list`
  - Notes: ticket-33 files validate; failure is unrelated pre-existing debt in ticket-32b run log metadata.
