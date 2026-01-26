<environment_context>
  <cwd>/home/codex/repos/microalpha</cwd>
  <shell>bash</shell>
</environment_context>

You are executing a single ticket in the current repository.

Inputs:
- Ticket id: TICKET-24_wrds-resume-metrics-refresh
- Goal: Rerun WRDS flagship on codex-worker (AX162-S) and refresh resume-facing real-data metrics docs from the new artifacts
- Scope/constraints (optional): In microalpha: run WRDS flagship using local exports at /srv/data/wrds; regenerate WRDS report; update docs/results_wrds_resume.md + project_state/CURRENT_RESULTS.md + docs/agent_runs/<run>/RESULTS.md; do not change strategy logic or candidate grids; do not add/commit raw WRDS data
- Acceptance criteria (optional): New artifacts/wrds_flagship/<RUN_ID>/ exists; docs/results_wrds_resume.md references <RUN_ID> + git sha + exact commands + headline metrics with clear labeling; project_state/CURRENT_RESULTS.md updated to same <RUN_ID> and snapshot; docs/agent_runs/<RUN_NAME>/RESULTS.md exists and records commands+env notes+artifact path; make check-data-policy passes; make validate-runlogs passes; no WRDS raw files staged/committed
- Test command (optional): cd /home/codex/repos/microalpha && make test-fast && make check-data-policy && WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds make wrds-flagship && make report-wrds && make validate-runlogs && python3 tools/agentic/project_state_refresh.py --zip
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
   - Create `docs/tickets/TICKET-24_wrds-resume-metrics-refresh.md` with: Goal, Scope, Acceptance Criteria, Plan, Notes.

3) Plan (brief):
   - 3–8 steps max. Include filenames you expect to touch.

4) Execute:
   - Implement the changes.
   - Run the best available tests:
     - If `cd /home/codex/repos/microalpha && make test-fast && make check-data-policy && WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds make wrds-flagship && make report-wrds && make validate-runlogs && python3 tools/agentic/project_state_refresh.py --zip` is provided, run it.
     - Else use the canonical test command in `AGENTS.md` (or infer: `make test`, `cargo test`, `pytest`, etc.).
   - If a command fails, fix or explain what blocks you.

5) Update repo memory:
   - Append a factual bullet to `PROGRESS.md` under “Done”.
   - If you made a non-obvious choice, add a short entry to `docs/DECISIONS.md`.

6) Emit a GPT review bundle:
   - Prefer the installed skill **$gpt-bundle** OR run:
     - `python3 tools/agentic/gpt_bundle.py --zip --ticket TICKET-24_wrds-resume-metrics-refresh`

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
