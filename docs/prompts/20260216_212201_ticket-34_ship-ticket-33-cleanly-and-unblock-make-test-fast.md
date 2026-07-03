# Ticket 34 Prompt — Ship ticket-33 cleanly and unblock make test-fast

## User verdict summary (input)
Verdict: **FAIL** for `mi01-26-26prompt1-diagnosis.md` because ticket-33 deliverables were present only in a dirty tree and were not shipped in commit/bundle evidence.

Key evidence provided by user:
- Bundle metadata showed `git_dirty: true` and no ticket-33 commit in `GIT_LOG.txt`.
- `DIFF.patch` and `STAGED.patch` did not include ticket-33 deliverables.
- `GIT_STATUS.txt` showed untracked ticket-33 files (`scripts/wrds_leaderboard.py`, leaderboard artifacts, prompt/run-log files) and modified pointer docs.
- `make test-fast` failed due run-log schema issues in `docs/agent_runs/20260216_025221_ticket-ticket-32b/META.json`.
- `project_state/CURRENT_RESULTS.md` header metadata was stale/inconsistent.

## Required fixes requested by user
1. Commit ticket-33 deliverables so they appear in `DIFF.patch`:
- `scripts/wrds_leaderboard.py`
- `docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
- `docs/artifacts/resume/wrds/leaderboard/leaderboard.md`
- `docs/artifacts/resume/wrds/leaderboard/resume_line_best.md`
- `docs/prompts/20260216_033516_ticket-33_wrds-realdata-leaderboard.md`
- `docs/agent_runs/20260216_033516_ticket-33_wrds-realdata-leaderboard/` (required run-log files)
- Pointer docs (`PROGRESS.md`, `CHANGELOG.md`, `docs/CODEX_SPRINT_TICKETS.md`, `project_state/CURRENT_RESULTS.md`, `project_state/KNOWN_ISSUES.md`)

2. Repair repo gate blocker:
- Fix `docs/agent_runs/20260216_025221_ticket-ticket-32b/META.json` to satisfy run-log schema (`finished_at_utc`, `ticket_id` format, `config_paths` type, and other required keys as needed), or update policy consistently.

3. Re-run required tests and record outcomes in shipping run log:
- `python3 tools/agentic/validate_runlog.py --run-name 20260216_033516_ticket-33_wrds-realdata-leaderboard`
- `python3 scripts/wrds_leaderboard.py --help`
- `python3 scripts/wrds_leaderboard.py --out docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
- `make test-fast`

4. Regenerate project-state metadata consistency and produce a clean bundle:
- Header metadata in `project_state/CURRENT_RESULTS.md` should reflect current context.
- Regenerate `gpt_bundle` after commit with clean worktree (`git_dirty: false`).

## Ticket objective for this run
Ship ticket-33 leaderboard work as an auditable commit-ready change set, fix schema/test blockers, and generate clean review evidence.
