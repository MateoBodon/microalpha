# Results

## Summary
- Shipped ticket-33 WRDS leaderboard deliverables from local-only state to tracked repository files.
- Repaired run-log schema debt in `docs/agent_runs/20260216_025221_ticket-ticket-32b/META.json` so run-log validation no longer blocks `make test-fast`.
- Resolved an additional data-policy gate failure by allowlisting explicit, license-safe WRDS resume aggregate files.
- Regenerated local `project_state` handoff bundle and fixed stale header metadata in `project_state/CURRENT_RESULTS.md`.

## Key outputs
- Script + leaderboard artifacts:
  - `scripts/wrds_leaderboard.py`
  - `docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
  - `docs/artifacts/resume/wrds/leaderboard/leaderboard.md`
  - `docs/artifacts/resume/wrds/leaderboard/resume_line_best.md`
- Ticket-33 prompt/run log:
  - `docs/prompts/20260216_033516_ticket-33_wrds-realdata-leaderboard.md`
  - `docs/agent_runs/20260216_033516_ticket-33_wrds-realdata-leaderboard/`
- Ticket-34 shipping run log:
  - `docs/prompts/20260216_212201_ticket-34_ship-ticket-33-cleanly-and-unblock-make-test-fast.md`
  - `docs/agent_runs/20260216_212201_ticket-34_ship-ticket-33-cleanly-and-unblock-make-test-fast/`
- Metadata/pointer updates:
  - `docs/agent_runs/20260216_025221_ticket-ticket-32b/META.json`
  - `PROGRESS.md`, `CHANGELOG.md`, `docs/CODEX_SPRINT_TICKETS.md`
  - `project_state/CURRENT_RESULTS.md`
  - `scripts/data_policy_allowlist.txt`

## Notes
- `make test-fast` is now green (`128 passed, 1 skipped`) with run-log validation passing first.
- The leaderboard selection remains unchanged: holdout-only best eligible run is `2026-01-27T04-47-22Z-31fe553` with dataset_id `wrds_crsp_export_20251221_v1`.
