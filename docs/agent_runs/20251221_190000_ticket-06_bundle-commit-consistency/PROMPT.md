TICKET: ticket-06
RUN_NAME: 20251221_190000_ticket-06_bundle-commit-consistency  # update timestamp if you want

Read FIRST (do not skip):
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Goal:
Ticket-01 is failing review because the Prompt-3 bundle includes living-doc updates that are NOT reflected in DIFF.patch (i.e., they were not committed). Fix the process: make bundling commit-consistent and commit the missing living-doc updates (scrub local paths). Keep the repo interview-grade (no fake results, no raw WRDS data).

Do NOT write a long plan. Execute in this order:

1) Inspect current repo state
- `git status` / `git status --porcelain` and identify any tracked files with local-only changes.
- Open the current ticket-01 run log folder in docs/agent_runs/ (if present locally) and confirm which files were patched but then left uncommitted.
- Open:
  - PROGRESS.md
  - project_state/CURRENT_RESULTS.md
  - project_state/KNOWN_ISSUES.md
  - docs/CODEX_SPRINT_TICKETS.md
  and identify:
  - any absolute local paths (e.g., /Volumes/... or /Users/...)
  - any “≈ metrics” without a traceable run id / summary artifact reference

2) Implement fixes (repo changes)
A) Enforce bundle/diff consistency
- Update tools/gpt_bundle.py so that it refuses to run if tracked files are dirty:
  - Use `git status --porcelain` and if any output exists (tracked modifications), exit non-zero with a clear message.
  - If you think refusing is too strict, instead write a `WORKTREE_STATUS.txt` inside the bundle that includes:
    - `git status --porcelain`
    - the current HEAD sha
    and include that file in the zip. (Prefer “refuse if dirty” for auditability.)
- Ensure the Makefile target `gpt-bundle` still works.

B) Commit the living-doc updates that ticket-01 should have shipped
- Update PROGRESS.md to mark ticket-01 DONE, but remove/scrub absolute local paths (use `$WRDS_DATA_ROOT` placeholders).
- Update project_state/KNOWN_ISSUES.md to include the survivorship/lookahead note about the WRDS smoke universe (keep it factual + explicit).
- Update project_state/CURRENT_RESULTS.md:
  - Include the WRDS smoke run note + run id if known.
  - Do not include unverified performance numbers; if you mention a metric, include a run id and reference the repo artifact/report path that was generated (even if artifacts are gitignored, cite the run id and report filename).
  - If these project_state files are supposed to be generated, prefer rerunning the generator (whatever the repo uses) so the header timestamps/git sha stay truthful; otherwise update headers so they are not lying.

C) Update the sprint board doc
- In docs/CODEX_SPRINT_TICKETS.md:
  - Under ticket-01 add `Status: FAIL (review) — docs/diff mismatch; fixed in ticket-06` (or similar).
  - Append ticket-06 definition (goal/why/files/acceptance/tests) at the bottom.

3) Minimal verification
- If you changed Python code (tools/gpt_bundle.py), run:
  - `python3 -m compileall tools`
- Ensure tracked working tree is clean:
  - `git status --porcelain` must be empty
- Run bundling end-to-end:
  - `make gpt-bundle TICKET=ticket-06 RUN_NAME=${RUN_NAME}`
- Then open the resulting zip and confirm:
  - DIFF.patch includes the committed living-doc updates
  - No raw WRDS files are present
  - (If you added WORKTREE_STATUS.txt) it shows clean

4) Run logs (mandatory)
Create a new run log folder:
- docs/agent_runs/${RUN_NAME}/
with:
- PROMPT.md (this prompt verbatim)
- COMMANDS.md (every command run, in order)
- RESULTS.md (what changed + why; include the bundle path)
- TESTS.md (commands + pass/fail)
- META.json (git sha before/after, branch, env notes)

5) Commit + branch policy
- Work on a branch: `feat/ticket-06-bundle-commit-consistency`
- Commit with body including:
  - `Tests: ...`
  - `Artifacts: ...`
  - `Docs: ...`
- No raw WRDS data or credentials in the diff. Stop if you see any.

6) Finish: generate the audit bundle
At the very end run:
- `make gpt-bundle TICKET=ticket-06 RUN_NAME=${RUN_NAME}`
Record the printed bundle path inside docs/agent_runs/${RUN_NAME}/RESULTS.md.

Suggested Codex invocations:
- Safe mode (recommended):
  - `codex --sandbox workspace-write --ask-for-approval untrusted "<paste this prompt>"`
- Full autonomy (ONLY if I explicitly request it later; otherwise do not use):
  - `codex --dangerously-bypass-approvals-and-sandbox "<paste prompt>"`
