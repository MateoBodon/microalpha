<environment_context>
  <cwd>/home/codex/repos/microalpha</cwd>
  <shell>bash</shell>
</environment_context>

You are executing a single ticket in the current repository.

Inputs:
- Ticket id: ticket-19a_commit-and-validate-scaffold
- Goal: Finish ticket-19 by committing the agentic scaffold + project_state docs/indices, adding the DECISIONS entry, and running the required refresh + tests with a clean git state.
- Scope/constraints (optional): Repo hygiene + scaffold integration only: stage/commit PROJECT.md, tools/agentic/, project_state/{README,RUNBOOK,BACKLOG}.md, and project_state/_generated/*; ensure .gitignore does not suppress docs/agent_runs/** or project_state/_generated/**; add a brief docs/DECISIONS.md entry; ensure PROGRESS/CHANGELOG reflect reality; do NOT change backtest/strategy/runtime behavior.
- Acceptance criteria (optional): All required scaffold files are tracked and committed; docs/DECISIONS.md includes ticket-19 decision entry; git check-ignore shows docs/agent_runs and project_state/_generated are not ignored; python3 tools/agentic/project_state_refresh.py --zip succeeds; make test-fast passes; git status --porcelain is clean; post-commit gpt_bundle zip is generated.
- Test command (optional): python3 tools/agentic/project_state_refresh.py --zip && make test-fast
- Risk (optional): med

## Rules
- Be surgical. Minimal diff that meets the goal.
- Don’t refactor unrelated code.
- If tests are missing or weak, add the smallest meaningful test that would catch regressions.
- Keep the repo runnable.

## Steps
1) Confirm the Agentic System scaffold exists:
   - AGENTS.md, PROJECT.md, tools/agentic/
   - If missing, run /prompts:bootstrap first.

2) Write/update a ticket file:
   - Create docs/tickets/ticket-19a_commit-and-validate-scaffold.md with: Goal, Scope, Acceptance Criteria, Plan, Notes.

3) Plan (brief):
   - 3–8 steps max. Include filenames you expect to touch.

4) Execute:
   - Implement the changes.
   - Run the best available tests:
     - If python3 tools/agentic/project_state_refresh.py --zip && make test-fast is provided, run it.
     - Else use the canonical test command in AGENTS.md (or infer: make test, cargo test, pytest, etc.).
   - If a command fails, fix or explain what blocks you.

5) Update repo memory:
   - Append a factual bullet to PROGRESS.md under “Done”.
   - If you made a non-obvious choice, add a short entry to docs/DECISIONS.md.

6) Emit a GPT review bundle:
   - Prefer the installed skill $gpt-bundle OR run:
     - python3 tools/agentic/gpt_bundle.py --zip --ticket ticket-19a_commit-and-validate-scaffold

## Output (single message)
- Summary of changes (files + what changed)
- Commands run + pass/fail
- Known risks / follow-ups
- The path to the generated gpt_bundle.zip

<skill>
<name>gpt-bundle</name>
<path>/home/codex/.codex/skills/gpt-bundle/SKILL.md</path>
---
name: gpt-bundle
description: Create a gpt_bundle.zip for GPT review (status + diffs + key docs).
metadata:
  short-description: Produce review bundle zip
---

# gpt-bundle

## Purpose
After a Codex ticket, produce a gpt_bundle.zip you can upload to GPT Prompt 3.

## Preferred execution
Run the repo-local script:
- python3 tools/agentic/gpt_bundle.py --zip --ticket <TICKET_ID>

If the repo-local script doesn't exist:
- Run $repo-bootstrap first.

## Output
Print the path to the created gpt_bundle.zip.
</skill>
