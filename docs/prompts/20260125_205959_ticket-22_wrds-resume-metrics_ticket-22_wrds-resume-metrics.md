You are executing a single ticket in the current repository.

Inputs:
- Ticket id: ticket-22_wrds_resume_metrics
- Goal: Produce up-to-date, resume-credible real-data (WRDS/CRSP) holdout metrics and a clean summary artifact (no licensed data) so the resume bullet can be updated confidently.
- Scope/constraints (optional): No strategy logic refactors. Use existing WRDS pipeline + configs; run a single locked WRDS holdout WFV + report on the codex-worker dataset root (/srv/data/wrds). Commit only license-safe artifacts: run log under docs/agent_runs/..., an updated docs/results_wrds.md (or new docs/results_wrds_resume.md) containing run_id + headline metrics (Sharpe_HAC, MaxDD, CAGR if available, turnover, RealityCheck p, SPA p/status), and (optional) a RESUME_METRICS.md snippet. Do NOT commit raw WRDS exports or large per-bar outputs.
- Acceptance criteria (optional): A new run log exists with commands + key outputs; WRDS run artifacts directory path is recorded; summary doc includes holdout headline metrics + inference fields and states net-of-costs + universe + date range; make check-data-policy passes; make test-fast passes; no licensed/raw WRDS data is added to git.
- Test command (optional): make test-fast && make check-data-policy && WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds make report-wrds
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
   - Create docs/tickets/ticket-22_wrds_resume_metrics.md with: Goal, Scope, Acceptance Criteria, Plan, Notes.

3) Plan (brief):
   - 3–8 steps max. Include filenames you expect to touch.

4) Execute:
   - Implement the changes.
   - Run the best available tests:
     - If make test-fast && make check-data-policy && WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds make report-wrds is provided, run it.
     - Else use the canonical test command in AGENTS.md (or infer: make test, cargo test, pytest, etc.).
   - If a command fails, fix or explain what blocks you.

5) Update repo memory:
   - Append a factual bullet to PROGRESS.md under “Done”.
   - If you made a non-obvious choice, add a short entry to docs/DECISIONS.md.

6) Emit a GPT review bundle:
   - Prefer the installed skill $gpt-bundle OR run:
     - python3 tools/agentic/gpt_bundle.py --zip --ticket ticket-22_wrds_resume_metrics

## Output (single message)
- Summary of changes (files + what changed)
- Commands run + pass/fail
- Known risks / follow-ups
- The path to the generated gpt_bundle.zip
