# Prompt

You are executing a single ticket in the current repository.

Inputs:
- Ticket id: TICKET-24b_finalize-wrds-refresh
- Goal: Finalize Ticket-24 by tracking run logs + WRDS report images, marking sprint ticket done, and verifying policy/link/runlog gates
- Scope/constraints (optional): In microalpha: git-add + commit docs/agent_runs/20260126_000243_ticket-00_project-state-refresh and docs/agent_runs/20260126_011723_ticket-24_wrds-resume-metrics-refresh (ensure RESULTS.md documents commands+env+artifact path+tests); git-add + commit docs/img/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d/ PNGs referenced by docs/results_wrds.md and reports/summaries/wrds_flagship.md; git-add + commit docs/tickets/TICKET-24_wrds-resume-metrics-refresh.md; update docs/CODEX_SPRINT_TICKETS.md to set ticket-24 Status=Done and replace placeholder 'Tests run/Artifacts/Documentation updates' with real values; do not change strategy logic; do not add WRDS raw exports or artifacts/ directories
- Acceptance criteria (optional): docs/agent_runs/20260126_011723_ticket-24_wrds-resume-metrics-refresh/RESULTS.md tracked and includes run_id 2026-01-26T01-22-23Z-e76eb4d + commands + env notes + artifact/report paths + tests run; docs/agent_runs/20260126_000243_ticket-00_project-state-refresh/RESULTS.md tracked; docs/img/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d/ tracked and satisfies all image links in docs/results_wrds.md and reports/summaries/wrds_flagship.md; docs/CODEX_SPRINT_TICKETS.md ticket-24 marked Done and has no placeholders; make check-data-policy passes; make validate-runlogs passes; pytest -q tests/test_docs_links.py passes; no WRDS raw files staged/committed
- Test command (optional): cd /home/codex/repos/microalpha && make test-fast && make check-data-policy && pytest -q tests/test_docs_links.py && make validate-runlogs && git status -sb
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
   - Create `docs/tickets/TICKET-24b_finalize-wrds-refresh.md` with: Goal, Scope, Acceptance Criteria, Plan, Notes.

3) Plan (brief):
   - 3–8 steps max. Include filenames you expect to touch.

4) Execute:
   - Implement the changes.
   - Run the best available tests:
     - If `cd /home/codex/repos/microalpha && make test-fast && make check-data-policy && pytest -q tests/test_docs_links.py && make validate-runlogs && git status -sb` is provided, run it.
     - Else use the canonical test command in `AGENTS.md` (or infer: `make test`, `cargo test`, `pytest`, etc.).
   - If a command fails, fix or explain what blocks you.

5) Update repo memory:
   - Append a factual bullet to `PROGRESS.md` under “Done”.
   - If you made a non-obvious choice, add a short entry to `docs/DECISIONS.md`.

6) Emit a GPT review bundle:
   - Prefer the installed skill **$gpt-bundle** OR run:
     - `python3 tools/agentic/gpt_bundle.py --zip --ticket TICKET-24b_finalize-wrds-refresh`

## Output (single message)
- Summary of changes (files + what changed)
- Commands run + pass/fail
- Known risks / follow-ups
- The path to the generated `gpt_bundle.zip`
