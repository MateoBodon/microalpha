# Prompt

Ticket: **ticket-32b**
Run: **20260216_025221_ticket-ticket-32b**
Summary: Ship ticket-32 deliverables cleanly (commit + clean bundle)

## Goal
- [x] Commit all ticket-32 deliverables so they are reviewable via `DIFF.patch`, and regenerate a bundle from a clean worktree (`git_dirty: false`).

## Constraints
- [x] Tracking policy followed (no new top-level dirs; outputs in canonical zones)
- [x] No secrets in repo or logs
- [x] Keep scope to shipping and verification only (no new WRDS reruns)

## Plan
1. Revert non-ticket code drift (`tools/agentic/runlog_init.py`) to keep this a docs-only ship.
2. Validate both run logs (`ticket-32` and `ticket-32b`) and stage all ticket-32 deliverables plus required living-doc updates.
3. Commit with ticket-formatted message, regenerate GPT bundle, and verify clean-tree metadata/evidence.

## Files to touch (expected)
- `docs/agent_runs/20260216_021416_ticket-32_wrds-resume-line-window-choice/`
- `docs/agent_runs/20260216_025221_ticket-ticket-32b/`
- `docs/tickets/TICKET-32_wrds_resume_line_pick-the-best-defensible-metric.md`
- `docs/prompts/20260216_021416_ticket-32_wrds-resume-line-window-choice.md`
- `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/resume_line_holdout.md`
- `PROGRESS.md`
- `CHANGELOG.md`
- `docs/CODEX_SPRINT_TICKETS.md`

## Definition of Done
- [x] Acceptance criteria met
- [x] PROGRESS.md updated
- [x] Run log filled (`RESULTS.md`/`TESTS.md`/`COMMANDS.md`/`META.json`)
