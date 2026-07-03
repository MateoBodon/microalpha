# ticket-36 — Ship ticket-35 cleanly (commit WRDS sweep config + resume artifacts + refreshed leaderboard)

## Goal
Commit and ship all ticket-35 deliverables so the improved WRDS holdout metrics are reviewable via `DIFF.patch` and safe to copy onto a resume.

## Required deliverables
- `configs/wfv_flagship_wrds_sweep35.yaml`
- `docs/agent_runs/20260216_223228_ticket-35_wrds-micro-sweep/{PROMPT.md,COMMANDS.md,RESULTS.md,TESTS.md,META.json}`
- `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/{metrics.json,manifest_excerpt.json,snippet.md}`
- `docs/prompts/20260216_223228_ticket-35_wrds-micro-sweep.md`
- `docs/artifacts/resume/wrds/leaderboard/{leaderboard.csv,leaderboard.md,resume_line_best.md}`
- `project_state/CURRENT_RESULTS.md`
- `PROGRESS.md`, `CHANGELOG.md`, `docs/CODEX_SPRINT_TICKETS.md`
- `scripts/data_policy_allowlist.txt`

## Gate commands
- `python3 tools/agentic/validate_runlog.py --run-name 20260216_223228_ticket-35_wrds-micro-sweep`
- `python3 tools/agentic/validate_runlog.py --run-name 20260216_232907_ticket-ticket-36`
- `python3 scripts/wrds_leaderboard.py --out docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
- `make check-data-policy`
- `make test-fast`

## Bundle acceptance
- Clean tree at bundle time (`git status --porcelain` empty)
- Bundled `BUNDLE_META.md` must show `git_dirty: false`
- Bundled `GIT_LOG.txt` includes a `ticket-36` ship commit
- Bundled `DIFF.patch` includes all ticket-35 deliverables above
