You are executing a single ticket in the current repository.

Inputs:
- Ticket id: ticket-19_finish-agentic-scaffold-cleanup
- Goal: Make agentic scaffold repo-consistent: remove bootstrap residue, ensure tools/agentic + PROJECT.md + project_state docs are tracked, and keep run logs + project_state indices trackable (not gitignored).
- Scope/constraints (optional): Touch only repo hygiene + scaffold integration: delete stray backup/append files; adjust .gitignore to not ignore docs/agent_runs or project_state/_generated; add tools/agentic/, PROJECT.md, and project_state/{README,RUNBOOK,BACKLOG}.md; append a short entry to docs/DECISIONS.md. Do NOT change core backtest/strategy logic or numerical outputs.
- Acceptance criteria (optional): No stray .gitignore.append or .bak. files remain; git status --porcelain is clean after commit; .gitignore does not ignore docs/agent_runs/** or project_state/_generated/**; tools/agentic/ + PROJECT.md + project_state/README.md + project_state/RUNBOOK.md + project_state/BACKLOG.md are tracked; python3 tools/agentic/project_state_refresh.py --zip succeeds; make test-fast passes; docs/DECISIONS.md has an entry describing what was cleaned/kept.
- Test command (optional): python3 tools/agentic/project_state_refresh.py --zip && make test-fast
- Risk (optional): med

## Rules
- Be surgical. Minimal diff that meets the goal.
- Don’t refactor unrelated code.
- If tests are missing or weak, add the smallest meaningful test that would catch regressions.
- Keep the repo runnable.

## Steps
1) Confirm the Agentic System scaffold exists:
   - `AGENTS.md`, `PROJECT.md`, `tools/agentic/`
   - If missing, run `/prompts:bootstrap` first.

2) Write/update a ticket file:
   - Create `docs/tickets/ticket-19_finish-agentic-scaffold-cleanup.md` with: Goal, Scope, Acceptance Criteria, Plan, Notes.

3) Plan (brief):
   - 3–8 steps max. Include filenames you expect to touch.

4) Execute:
   - Implement the changes.
   - Run the best available tests:
     - If `python3 tools/agentic/project_state_refresh.py --zip && make test-fast` is provided, run it.
     - Else use the canonical test command in `AGENTS.md` (or infer: `make test`, `cargo test`, `pytest`, etc.).
   - If a command fails, fix or explain what blocks you.

5) Update repo memory:
   - Append a factual bullet to `PROGRESS.md` under “Done”.
   - If you made a non-obvious choice, add a short entry to `docs/DECISIONS.md`.

6) Emit a GPT review bundle:
   - Prefer the installed skill **$gpt-bundle** OR run:
     - `python3 tools/agentic/gpt_bundle.py --zip --ticket ticket-19_finish-agentic-scaffold-cleanup`

## Output (single message)
- Summary of changes (files + what changed)
- Commands run + pass/fail
- Known risks / follow-ups
- The path to the generated `gpt_bundle.zip`

<skill>
<name>gpt-bundle</name>
<path>/Users/mateobodon/.codex/skills/gpt-bundle/SKILL.md</path>
---
name: gpt-bundle
description: Create a gpt_bundle.zip for GPT review (status + diffs + key docs).
metadata:
  short-description: Produce review bundle zip
---

# gpt-bundle

## Purpose
After a Codex ticket, produce a `gpt_bundle.zip` you can upload to GPT Prompt 3.

## Preferred execution
Run the repo-local script:
- `python3 tools/agentic/gpt_bundle.py --zip --ticket <TICKET_ID>`

If the repo-local script doesn't exist:
- Run `$repo-bootstrap` first.

## Output
Print the path to the created `gpt_bundle.zip`.

</skill>
