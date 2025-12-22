TICKET: ticket-10
RUN_NAME: 20251222_051500_ticket-10_block-placeholder-runlogs  # update timestamp if needed

Read FIRST (do not skip):
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md
- PROGRESS.md

Stop-the-line:
- No fabricated results.
- No raw WRDS exports / credentials committed.
- No “green by disabling.”

Goal:
Ticket-09 failed review because docs/agent_runs/.../RESULTS.md is a placeholder and does not record the bundle path. Fix the existing ticket-09 RESULTS.md and add a guardrail in tools/gpt_bundle.py that blocks bundling when RESULTS.md is still a placeholder (or marked PENDING).

Do NOT write a long plan. Execute:

1) Inspect current state
- Open:
  - docs/agent_runs/20251222_034500_ticket-09_ticket-id-enforcement/RESULTS.md
  - docs/DOCS_AND_LOGGING_SYSTEM.md (required RESULTS.md contents)
  - tools/gpt_bundle.py (current pre-bundle checks)
  - docs/CODEX_SPRINT_TICKETS.md (ticket-09 status line)

2) Repair ticket-09 RESULTS.md (doc-only fix)
- Replace the placeholder with a short, concrete summary:
  - What changed:
    - ticket-08 entry added to sprint tickets
    - gpt-bundle enforces META.json ticket_id exists as a sprint-ticket header
  - Tests:
    - pytest -q (include outcome)
    - python3 -m compileall tools (include outcome)
  - Bundle:
    - include the correct relative bundle path that was produced for ticket-09
      (docs/gpt_bundles/2025-12-22T04-33-45Z_ticket-09_20251222_034500_ticket-09_ticket-id-enforcement.zip)

3) Add bundler guardrail: block placeholder RESULTS.md
- In tools/gpt_bundle.py:
  - Before bundling, read docs/agent_runs/<RUN_NAME>/RESULTS.md
  - If it contains placeholder markers like:
    - "[updated RESULTS"
    - "PENDING"
    - "TODO"
    then fail fast with a clear error explaining to write real results before bundling.
  - Also add a consistency check:
    - env TICKET must match META.json ticket_id (fail if mismatch).

4) Sprint board + progress docs
- Update docs/CODEX_SPRINT_TICKETS.md:
  - Mark ticket-09 as FAIL (review) with reason (placeholder RESULTS.md)
  - Add ticket-10 with acceptance criteria and tests.
- Update PROGRESS.md with a 2025-12-22 entry for ticket-10.

5) Tests (required)
- Run:
  - pytest -q
  - python3 -m compileall tools
Record outputs in docs/agent_runs/<RUN_NAME>/TESTS.md.

6) Run logs (required)
Create docs/agent_runs/<RUN_NAME>/ with:
- PROMPT.md (this prompt verbatim)
- COMMANDS.md (every command run)
- RESULTS.md (what changed + bundle path at end)
- TESTS.md (commands + outcomes)
- META.json (immutable git SHA before/after if possible; ticket_id; branch; notes)

7) Commit + bundle (required)
- Branch: feat/ticket-10-block-placeholder-runlogs
- Commit message: "ticket-10: block placeholder run logs + fix ticket-09 RESULTS"
- Commit body MUST include:
  - Tests: ...
  - Artifacts: ...
  - Docs: ...
- End:
  - make gpt-bundle TICKET=ticket-10 RUN_NAME=<RUN_NAME>
  - Record the bundle path in docs/agent_runs/<RUN_NAME>/RESULTS.md

Suggested Codex invocation (safe):
- codex --profile safe --sandbox workspace-write --ask-for-approval on-request
(Do NOT use full-autonomy unless explicitly requested.)

Human merge checklist (short):
- ticket-09 RESULTS.md no longer placeholder + includes bundle path
- gpt-bundle fails on placeholder RESULTS.md
- pytest + compileall pass
- bundle generated and path recorded
