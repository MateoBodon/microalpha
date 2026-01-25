You are executing a single ticket in the current repository.

Inputs:
- Ticket id: ticket-23_wrds_holdout_nonzero_trades
- Goal: Fix WRDS final-holdout degeneracy (zero trades) and produce resume-credible real-data holdout metrics with a committed run log + summary doc
- Scope/constraints (optional): Diagnose where trades disappear in WRDS final-holdout (data coverage vs universe filters vs sizing/risk caps vs execution); add minimal diagnostics and a hard guardrail for n_trades==0; adjust only what’s necessary to get nonzero trades (no strategy redesign); rerun WRDS holdout + report; commit only license-safe artifacts (no raw WRDS exports)
- Acceptance criteria (optional): WRDS final-holdout run produces n_trades>0 and non-NaN Sharpe/CAGR/MaxDD; docs/results_wrds_resume.md includes run_id/date-range/universe/net-of-costs note and headline metrics; docs/agent_runs/<run>/ contains commands + stdout/stderr + artifact pointers and is committed; make test-fast passes; make check-data-policy passes; WRDS_DATA_ROOT handling is consistent (either documented as /srv/data/wrds/wrds or auto-detected)
- Test command (optional): make test-fast && make check-data-policy && WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make wfv-wrds && WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make report-wrds
- Risk (optional): high

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
   - Create docs/tickets/ticket-23_wrds_holdout_nonzero_trades.md with: Goal, Scope, Acceptance Criteria, Plan, Notes.

3) Plan (brief):
   - 3–8 steps max. Include filenames you expect to touch.

4) Execute:
   - Implement the changes.
   - Run the best available tests:
     - If make test-fast && make check-data-policy && WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make wfv-wrds && WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make report-wrds is provided, run it.
     - Else use the canonical test command in AGENTS.md (or infer: make test, cargo test, pytest, etc.).
   - If a command fails, fix or explain what blocks you.

5) Update repo memory:
   - Append a factual bullet to PROGRESS.md under “Done”.
   - If you made a non-obvious choice, add a short entry to docs/DECISIONS.md.

6) Emit a GPT review bundle:
   - Prefer the installed skill $gpt-bundle OR run:
     - python3 tools/agentic/gpt_bundle.py --zip --ticket ticket-23_wrds_holdout_nonzero_trades

## Output (single message)
- Summary of changes (files + what changed)
- Commands run + pass/fail
- Known risks / follow-ups
- The path to the generated gpt_bundle.zip
