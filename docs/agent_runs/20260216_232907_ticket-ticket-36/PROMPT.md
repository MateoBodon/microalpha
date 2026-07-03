# Prompt

Ticket: **ticket-36**
Run: **20260216_232907_ticket-ticket-36**
Summary: Ship ticket-35 deliverables cleanly (commit + clean bundle).

## Goal
- Ship all ticket-35 deliverables as tracked files in a real commit and regenerate a clean bundle (`git_dirty: false`).

## Context
- Prior review failed because ticket-35 artifacts and pointer-doc changes were still in a dirty worktree and absent from bundle `DIFF.patch`.
- `project_state/CURRENT_RESULTS.md` contained stale header metadata versus ticket-35 body updates.

## Required fixes
1. Commit untracked ticket-35 deliverables and tracked pointer/doc updates.
2. Refresh run-log/project-state validity so `make test-fast` passes.
3. Regenerate a clean bundle and verify `BUNDLE_META.md`, `GIT_LOG.txt`, and `DIFF.patch` prove shipment.

## Source prompt capture
- `docs/prompts/20260216_232907_ticket-ticket-36_ship-ticket-35-cleanly.md`
