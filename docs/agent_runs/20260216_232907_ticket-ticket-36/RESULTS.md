# Results

## Summary
- Converted ticket-35 outputs from dirty-worktree state into tracked, reviewable repository files.
- Rebuilt WRDS resume leaderboard artifacts showing a new best eligible holdout run (`run_id=2026-02-16T22-33-46Z-8d90621`).
- Repaired ticket-36 run-log schema so fast-test gates are no longer blocked by missing metadata keys.
- Refreshed `project_state` generated files and prepared a manual header correction for `project_state/CURRENT_RESULTS.md`.

## Key outputs
- Ticket-35 deliverables promoted for commit:
  - `configs/wfv_flagship_wrds_sweep35.yaml`
  - `docs/agent_runs/20260216_223228_ticket-35_wrds-micro-sweep/`
  - `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/`
  - `docs/prompts/20260216_223228_ticket-35_wrds-micro-sweep.md`
  - `docs/artifacts/resume/wrds/leaderboard/`
- Ticket-36 shipping run log + prompt capture:
  - `docs/agent_runs/20260216_232907_ticket-ticket-36/`
  - `docs/prompts/20260216_232907_ticket-ticket-36_ship-ticket-35-cleanly.md`

## Notes
- The first `make test-fast` attempt failed only because the run-log template omitted required metadata keys; no strategy/metrics code regressions were involved.
- Final validation was green after schema repair (`python3 tools/agentic/validate_runlog.py --run-name 20260216_232907_ticket-ticket-36` and `make test-fast`).
