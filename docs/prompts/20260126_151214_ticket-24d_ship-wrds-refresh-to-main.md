# Prompt

You are executing a single ticket in the current repository.

Inputs:
- Ticket id: TICKET-24d_ship-wrds-refresh-to-main
- Goal: Complete TICKET-24c by committing all remaining WRDS refresh docs/runlogs/images, merging to main, and pushing a clean audited state.
- Scope/constraints (optional): Only ship docs/project_state/report outputs for run 2026-01-26T01-22-23Z-e76eb4d; add missing run logs and images; do not change strategy logic; do not commit artifacts/ or any WRDS raw exports.
- Acceptance criteria (optional): All WRDS docs consistently reference 2026-01-26T01-22-23Z-e76eb4d; project_state snapshot reflects same run_id; required run logs + ticket docs are tracked and make validate-runlogs passes; make check-data-policy passes with zero WRDS raw files staged; pytest -q tests/test_docs_links.py passes; branch merged to origin/main; git status clean on main; new gpt_bundle produced from main for this ticket.
- Test command (optional): make validate-runlogs && make check-data-policy && pytest -q tests/test_docs_links.py && make test-fast
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
   - Create `docs/tickets/TICKET-24d_ship-wrds-refresh-to-main.md` with: Goal, Scope, Acceptance Criteria, Plan, Notes.

3) Plan (brief):
   - 3–8 steps max. Include filenames you expect to touch.

4) Execute:
   - Implement the changes.
   - Run the best available tests:
     - If `make validate-runlogs && make check-data-policy && pytest -q tests/test_docs_links.py && make test-fast` is provided, run it.
     - Else use the canonical test command in `AGENTS.md` (or infer: `make test`, `cargo test`, `pytest`, etc.).
   - If a command fails, fix or explain what blocks you.

5) Update repo memory:
   - Append a factual bullet to `PROGRESS.md` under “Done”.
   - If you made a non-obvious choice, add a short entry to `docs/DECISIONS.md`.

6) Emit a GPT review bundle:
   - Prefer the installed skill **$gpt-bundle** OR run:
     - `python3 tools/agentic/gpt_bundle.py --zip --ticket TICKET-24d_ship-wrds-refresh-to-main`

## Output (single message)
- Summary of changes (files + what changed)
- Commands run + pass/fail
- Known risks / follow-ups
- The path to the generated `gpt_bundle.zip`

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
After a Codex ticket, produce a `gpt_bundle.zip` you can upload to GPT Prompt 3.

## Preferred execution
Run the repo-local script:
- `python3 tools/agentic/gpt_bundle.py --zip --ticket <TICKET_ID>`

If the repo-local script doesn't exist:
- Run `$repo-bootstrap` first.

## Output
Print the path to the created `gpt_bundle.zip`.
</skill>
