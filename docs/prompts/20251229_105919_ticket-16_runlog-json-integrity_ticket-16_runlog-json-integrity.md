You are Codex running in the microalpha repo. Follow AGENTS.md exactly (stop-the-line rules, doc protocol, data policy, branch/commit policy). Do not do a long upfront plan.

TICKET: ticket-16
RUN_NAME: YYYYMMDD_HHMMSS_ticket-16_runlog-json-integrity  (use UTC timestamp)
BRANCH: codex/ticket-16-runlog-json-integrity

Goal: Repair any corrupted docs/agent_runs/*/META.json files (must be valid JSON + required keys) and add a validator script + Make target so this can’t happen again. This is process integrity work, not “better metrics”.

Hard constraints:
- Do NOT fabricate results. Do NOT claim you ran anything you didn’t run.
- Do NOT commit any WRDS data. No network/web needed for this ticket.
- Keep changes minimal and reviewable; small logical commits.
- Do NOT merge to main unless the user explicitly tells you to.

Required workflow:
1) Create feature branch:
   - git checkout -b codex/ticket-16-runlog-json-integrity

2) Create run log directory and prompt file:
   - mkdir -p docs/agent_runs/<RUN_NAME>/
   - Save this exact prompt text to:
     - docs/prompts/<RUN_NAME>_ticket-16_runlog-json-integrity.md
     - docs/agent_runs/<RUN_NAME>/PROMPT.md
   - Initialize docs/agent_runs/<RUN_NAME>/{COMMANDS.md,RESULTS.md,TESTS.md,META.json}

3) Inspect (no long plan):
   - Read AGENTS.md and docs/DOCS_AND_LOGGING_SYSTEM.md.
   - Find META.json issues:
     - Attempt to JSON-parse every docs/agent_runs/*/META.json.
     - Identify any that fail JSON parsing or are missing required keys.
   - IMPORTANT: We already have evidence that docs/agent_runs/20251224_051508_ticket-04_wrds-smoke-check/META.json may be broken (missing the "git_sha_after" key). Verify.

4) Implement fixes:
   A) Repair corrupted META.json files
      - Fix JSON syntax so every META.json loads cleanly.
      - Ensure required keys exist per docs/DOCS_AND_LOGGING_SYSTEM.md.
      - Ensure git_sha_before and git_sha_after are immutable 40-hex SHAs (NOT "HEAD", NOT "refs/heads/...").
      - Keep existing content when possible; only edit what's needed.

   B) Add run-log validator script (new)
      - Create: scripts/validate_run_logs.py (or scripts/check_run_logs.py)
      - Behavior:
        - Iterate docs/agent_runs/* (directories).
        - For each, enforce presence of:
          PROMPT.md, COMMANDS.md, RESULTS.md, TESTS.md, META.json.
        - Load META.json and validate:
          - JSON parses
          - run_name matches directory name
          - ticket_id matches "ticket-XX" pattern
          - git_sha_before/git_sha_after are 40-hex SHAs
          - started_at_utc/finished_at_utc exist (string)
          - dataset_id exists (string)
        - Also validate ticket_id exists in docs/CODEX_SPRINT_TICKETS.md (scan ticket headers).
        - Exit non-zero on any violation with an actionable error message.
      - Add a small pytest-style unit test if appropriate OR keep it as a script but ensure it is executed by Make.

   C) Make integration
      - Add a Make target:
        - make validate-runlogs  (runs the validator script)
      - Add it to make test-fast if that’s the established “minimum gate”.
        - If test-fast must stay lightweight, at least document in Makefile help or PROGRESS.md that validate-runlogs is mandatory for merges.

   D) Sprint ticket file update
      - Append a new ticket section to docs/CODEX_SPRINT_TICKETS.md:
        - ticket-16 — Run-log META.json integrity + validator
        - include: goal, why, files likely touched, acceptance criteria, minimal tests/commands, expected artifacts/logs
      - Update ticket-15 status to DONE (reviewed PASS) with a one-line explanation.

   E) Documentation updates
      - Update PROGRESS.md with a dated entry for ticket-16.
      - If you classify the META.json corruption as a known issue, add/update project_state/KNOWN_ISSUES.md with:
        - what broke, impact, how detected, how fixed, and how prevented.

5) Tests / commands (must run and record):
   - make test-fast
   - make validate-runlogs
   - python3 -m compileall tools scripts  (only if you touched python tooling/scripts)

Record every command in docs/agent_runs/<RUN_NAME>/COMMANDS.md and summarize outputs in TESTS.md.

6) Commits:
   - Use small logical commits (example):
     1) "ticket-16: add run-log validator + Make target"
     2) "ticket-16: repair broken META.json entries"
     3) "ticket-16: docs/progress updates"
   - Each commit body MUST include:
     - Tests: ...
     - Artifacts: ... (or "none")
     - Docs: ...

7) Run log finalization:
   - Fill docs/agent_runs/<RUN_NAME>/RESULTS.md with:
     - What META.json files were fixed (list paths)
     - What validator enforces
     - Any remaining known limitations
   - Fill META.json with required fields + config/artifact/report paths as applicable (artifact_paths may be empty for this process-only ticket).

8) Bundle (required end step):
   - Ensure git status is clean.
   - Run:
     make gpt-bundle TICKET=ticket-16 RUN_NAME=<RUN_NAME>
   - Record the produced bundle path in docs/agent_runs/<RUN_NAME>/RESULTS.md.

Finish by printing:
- A short summary of changes
- Commands/tests you ran
- The bundle path
- A human merge checklist (3–8 bullets)
