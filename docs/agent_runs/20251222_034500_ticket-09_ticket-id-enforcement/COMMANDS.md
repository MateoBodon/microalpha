Web research: disabled

ls
cat AGENTS.md
cat docs/PLAN_OF_RECORD.md
cat docs/DOCS_AND_LOGGING_SYSTEM.md
cat docs/CODEX_SPRINT_TICKETS.md
cat PROGRESS.md
sed -n '1,220p' tools/gpt_bundle.py
sed -n '220,520p' tools/gpt_bundle.py
cat project_state/KNOWN_ISSUES.md
cat docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/PROMPT.md
cat docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/META.json
cat CHANGELOG.md
git rev-parse HEAD
mkdir -p docs/agent_runs/20251222_034500_ticket-09_ticket-id-enforcement
cat <<'EOF' > docs/agent_runs/20251222_034500_ticket-09_ticket-id-enforcement/PROMPT.md
TICKET: ticket-09
RUN_NAME: 20251222_034500_ticket-09_ticket-id-enforcement  # update timestamp if needed

Read FIRST (do not skip):
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md
- PROGRESS.md

Stop-the-line:
- No fabricated results.
- No raw WRDS exports / credentials committed.
- Don’t “green by disabling.”

Goal:
Ticket-08 failed review because it was NOT defined in docs/CODEX_SPRINT_TICKETS.md, violating docs/DOCS_AND_LOGGING_SYSTEM.md (RUN_NAME ticket id must exist in sprint tickets). Fix the process so this cannot recur, and backfill a proper ticket-08 entry so it becomes reviewable.

Do NOT write a long upfront plan. Execute in this order:

1) Backfill ticket-08 into the sprint board
- Edit docs/CODEX_SPRINT_TICKETS.md:
  - Add a new section: "## ticket-08 — Unblock WRDS reporting: SPA edge cases + zero-activity invariants"
  - Include:
    - Goal (1 sentence)
    - Why (tie to PROGRESS.md + KNOWN_ISSUES.md about SPA blocking)
    - Acceptance criteria (objective):
      - Report must not crash on invalid/all-zero SPA comparator stats; must surface “SPA skipped: <reason>”.
      - Report must surface “Run is degenerate” for zero trades / flat equity (explicit reasons).
      - Invariant: if total_turnover > 0 then num_trades > 0 (or clearly distinguish desired vs executed).
      - Tests cover SPA-skip + degenerate warning + turnover/trade invariant.
    - Minimal tests/commands:
      - pytest -q
      - microalpha report --artifact-dir artifacts/sample_wfv_holdout/<RUN_ID>
      - microalpha report --artifact-dir artifacts/wrds_flagship/<RUN_ID>  (report-only; no WRDS exports)
  - Status: "Implemented (review pending)" and point to the existing run log folder:
    - docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/

2) Enforce the protocol in tooling (prevent recurrence)
- Update tools/gpt_bundle.py:
  - Read docs/agent_runs/<RUN_NAME>/META.json to get ticket_id (e.g., "ticket-08").
  - Assert that docs/CODEX_SPRINT_TICKETS.md contains a matching header like "## ticket-08".
  - If not found, fail fast with a clear error message explaining how to fix (add the ticket section first).
  - (Optional but helpful) also fail if META.json has git_sha_after == "HEAD" and suggest writing an immutable SHA.

3) Documentation update
- Update PROGRESS.md with a 2025-12-22 entry:
  - ticket-08 review FAIL (missing sprint ticket entry)
  - ticket-09 adds enforcement + backfills ticket-08

4) Tests (required by AGENTS.md)
- Run:
  - pytest -q
  - python3 -m compileall tools  (since tools/gpt_bundle.py changed)

5) Run logs (mandatory)
Create docs/agent_runs/<RUN_NAME>/ with:
- PROMPT.md (this prompt verbatim)
- COMMANDS.md (every command run)
- RESULTS.md (what changed; mention ticket-08 is now defined; mention bundler enforcement; include bundle path at end)
- TESTS.md (pytest + compileall outputs)
- META.json (git sha before/after as immutable SHAs; env notes)

6) Commit + bundle
- Branch: feat/ticket-09-ticket-id-enforcement
- Commit message: "ticket-09: enforce ticket ids + backfill ticket-08 definition"
- Commit body must include:
  - Tests: ...
  - Artifacts/logs: ...
  - Documentation updates: ...
- End by generating the bundle:
  - make gpt-bundle TICKET=ticket-09 RUN_NAME=<RUN_NAME>
  - Record the bundle path in docs/agent_runs/<RUN_NAME>/RESULTS.md

Suggested Codex invocation (safe):
- codex --profile safe --sandbox workspace-write --ask-for-approval on-request
(Do NOT use full-autonomy unless explicitly requested.)
