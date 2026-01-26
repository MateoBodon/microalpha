# Prompt

You are executing a single ticket in the current repository.

Inputs:
- Ticket id: TICKET-24c_ship-wrds-refresh
- Goal: Stage, commit, and push the WRDS refresh outputs (docs + run logs + images) so resume metrics are auditably current.
- Scope/constraints (optional): In microalpha repo: stage and commit the modified docs/project_state files plus untracked required deliverables: docs/agent_runs/20260126_000243_ticket-00_project-state-refresh/, docs/agent_runs/20260126_011723_ticket-24_wrds-resume-metrics-refresh/, docs/agent_runs/20260126_023947_ticket-24b_finalize-wrds-refresh/, docs/img/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d/, docs/tickets/TICKET-24_wrds-resume-metrics-refresh.md, docs/tickets/TICKET-24b_finalize-wrds-refresh.md (and any referenced docs/img files); ensure run logs contain commands/env notes/run_id/test outputs; do NOT add artifacts/ or any WRDS raw exports; push to origin/main; generate a new gpt_bundle for this ticket.
- Acceptance criteria (optional): git status clean on main; required docs/agent_runs directories tracked and validate; docs/img/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d images tracked and all doc links resolve; docs/results_wrds*.md and reports/summaries/wrds_flagship.md reference the new run_id; make check-data-policy passes; make validate-runlogs passes; pytest -q tests/test_docs_links.py passes; no WRDS raw/export files staged; commit pushed to origin/main; gpt_bundle zip produced for TICKET-24c.
- Test command (optional): cd ~/repos/microalpha && make test-fast && make check-data-policy && pytest -q tests/test_docs_links.py && make validate-runlogs && git status -sb && git diff --stat
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
   - Create `docs/tickets/TICKET-24c_ship-wrds-refresh.md` with: Goal, Scope, Acceptance Criteria, Plan, Notes.

3) Plan (brief):
   - 3–8 steps max. Include filenames you expect to touch.

4) Execute:
   - Implement the changes.
   - Run the best available tests:
     - If `cd ~/repos/microalpha && make test-fast && make check-data-policy && pytest -q tests/test_docs_links.py && make validate-runlogs && git status -sb && git diff --stat` is provided, run it.
     - Else use the canonical test command in `AGENTS.md` (or infer: `make test`, `cargo test`, `pytest`, etc.).
   - If a command fails, fix or explain what blocks you.

5) Update repo memory:
   - Append a factual bullet to `PROGRESS.md` under “Done”.
   - If you made a non-obvious choice, add a short entry to `docs/DECISIONS.md`.

6) Emit a GPT review bundle:
   - Prefer the installed skill **$gpt-bundle** OR run:
     - `python3 tools/agentic/gpt_bundle.py --zip --ticket TICKET-24c_ship-wrds-refresh`

## Output (single message)
- Summary of changes (files + what changed)
- Commands run + pass/fail
- Known risks / follow-ups
- The path to the generated `gpt_bundle.zip`
