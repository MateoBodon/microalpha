# Prompt

Ticket: **ticket-34**
Run: **20260216_212201_ticket-34_ship-ticket-33-cleanly-and-unblock-make-test-fast**
Summary: Ship ticket-33 leaderboard cleanly and unblock make test-fast.

## Goal
- Ship ticket-33 leaderboard deliverables as tracked, reviewable files and resolve test blockers so `make test-fast` is green.

## Context
- Prior review marked FAIL because ticket-33 outputs existed locally but were untracked/uncommitted and therefore absent from `DIFF.patch`.
- `make test-fast` was blocked by malformed run-log metadata in `docs/agent_runs/20260216_025221_ticket-ticket-32b/META.json`.
- `project_state/CURRENT_RESULTS.md` header metadata was stale versus body content.

## Required fixes
1. Commit ticket-33 deliverables (`scripts/wrds_leaderboard.py`, leaderboard artifacts, prompt/run-log files, pointer docs).
2. Repair run-log schema blocker so run-log validation and `make test-fast` pass.
3. Refresh project-state metadata consistency.
4. Generate a clean `gpt_bundle` after commit (`git_dirty: false`).

## Source prompt capture
- `docs/prompts/20260216_212201_ticket-34_ship-ticket-33-cleanly-and-unblock-make-test-fast.md`
