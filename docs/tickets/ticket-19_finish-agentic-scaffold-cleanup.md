# Ticket 19: finish agentic scaffold cleanup

## Goal
Make the agentic scaffold repo-consistent by removing bootstrap residue, tracking scaffold files, and ensuring run logs + project_state indices are trackable.

## Scope
- Repo hygiene + scaffold integration only.
- Delete stray backup/append files.
- Adjust `.gitignore` to avoid ignoring `docs/agent_runs/` and `project_state/_generated/`.
- Ensure `tools/agentic/`, `PROJECT.md`, and `project_state/{README,RUNBOOK,BACKLOG}.md` are tracked.
- Append a short entry to `docs/DECISIONS.md`.
- Do not change core backtest/strategy logic or numerical outputs.

## Acceptance Criteria
- No stray `.gitignore.append` or `.bak` files remain.
- `.gitignore` does not ignore `docs/agent_runs/**` or `project_state/_generated/**`.
- `tools/agentic/`, `PROJECT.md`, `project_state/README.md`, `project_state/RUNBOOK.md`, and `project_state/BACKLOG.md` are tracked.
- `python3 tools/agentic/project_state_refresh.py --zip` succeeds.
- `make test-fast` passes.
- `docs/DECISIONS.md` has an entry describing what was cleaned/kept.

## Plan
1. Remove bootstrap residue files and update `.gitignore` to keep `docs/agent_runs/` and `project_state/_generated/` trackable.
2. Create run logs in `docs/agent_runs/<RUN_NAME>/` and store the prompt in `docs/prompts/`.
3. Update `docs/DECISIONS.md` and `PROGRESS.md` with this cleanup.
4. Run `python3 tools/agentic/project_state_refresh.py --zip` and `make test-fast`.
5. Generate the GPT bundle and verify clean `git status` before commit.

## Notes
- Risk: medium (repo hygiene + logging).
