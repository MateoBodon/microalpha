You are Codex working in the microalpha repo. Follow repo rules exactly.

READ FIRST (binding):
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Ticket: ticket-11 — Data policy scan + automated guardrails
Run name: set RUN_NAME = YYYYMMDD_HHMMSS_ticket-11_data-policy-guardrails

Stop-the-line (from AGENTS.md):
- If you find raw WRDS exports, credential material, or license-risk datasets tracked in git: STOP, document, and fix before anything else.

Do NOT write a long upfront plan. Execute the steps below.

0) Branch + run-log setup
- Create branch: feat/ticket-11-data-policy-guardrails
- Export env vars (and record in COMMANDS.md):
  - export TICKET=ticket-11
  - export RUN_NAME="$(date +%Y%m%d_%H%M%S)_ticket-11_data-policy-guardrails"
- Create run log dir: docs/agent_runs/$RUN_NAME/
  - Write PROMPT.md with this prompt verbatim.
  - Create empty COMMANDS.md / RESULTS.md / TESTS.md / META.json placeholders (but DO NOT leave RESULTS.md as a placeholder at the end — bundling will fail).

1) Formalize the ticket in sprint board (required for gpt-bundle)
- Edit docs/CODEX_SPRINT_TICKETS.md:
  - Add a new section: "## ticket-11 — Data policy scan + automated guardrails"
  - Move the existing unstructured “license-risk artifacts / check_data_policy.py” block under ticket-11 (so it’s not floating text).
  - Update ticket-09 status from FAIL -> DONE (ticket-10 backfilled ticket-09 RESULTS.md).
- Keep diffs tight; do not rewrite unrelated tickets.

2) Data policy scan (must run before implementing guardrails)
Run these commands and paste outputs (or summarized counts + file lists) into RESULTS.md:
- git ls-files > /tmp/tracked_files.txt
- rg -n --hidden --no-ignore-vcs "(\\bsecid\\b|\\bmarket_iv\\b|\\bbest_bid\\b|\\bbest_ask\\b|\\bstrike\\b|optionmetrics|taq|wrds)" $(cat /tmp/tracked_files.txt) || true
- Identify any tracked *data-like* artifacts (csv/parquet/json/jsonl) under artifacts/, data/, reports/, notebooks/, etc that look like restricted exports.

If you find suspicious tracked files:
- Treat as stop-the-line.
- Remove them from HEAD (git rm) and add appropriate .gitignore rules.
- In RESULTS.md, explicitly note: removing from HEAD does NOT purge git history; recommend follow-up procedure (git filter-repo) but DO NOT rewrite history unless explicitly required by the ticket scope and you can do it safely.

3) Implement automated guardrail: scripts/check_data_policy.py
Create scripts/check_data_policy.py with these properties:
- Scans git-tracked files only (use git ls-files).
- Only inspects data-like extensions: .csv, .parquet, .json, .jsonl, .feather (skip .py/.md/.txt to avoid false positives).
- Flags likely restricted exports by:
  - keyword patterns (secid, market_iv, best_bid/best_ask, strike, optionmetrics, taq, wrds)
  - and/or path patterns (artifacts/heston/, quote_surface/, option_*, etc) if those exist.
- Exit code:
  - 0 if clean
  - non-zero if violations found (print a short actionable report: file path + matched pattern)
- Include an allowlist mechanism (e.g., comments or a small allowlist file) so we can exempt clearly synthetic/public sample files with documented provenance.

4) Wire it into the repo’s “fast” workflow
- Prefer Make target if present:
  - add make check-data-policy (if Makefile exists)
- Otherwise add a pytest test:
  - tests/test_data_policy.py runs scripts/check_data_policy.py and asserts exit code 0.
- Goal: this runs in the minimum test suite (make test-fast if present; otherwise pytest -q).

5) Documentation updates (required)
- Update PROGRESS.md: add a Ticket-11 line with run log path.
- Update project_state/KNOWN_ISSUES.md:
  - If you found & removed restricted artifacts: record what was removed and what remediation remains (history purge follow-up).
  - If clean: record that a data-policy checker was added and how to run it.

6) Tests (minimum) + record them
Run and record outputs in TESTS.md:
- If available: make test-fast
- Always: pytest -q
- python3 -m compileall scripts tools
- python scripts/check_data_policy.py (or equivalent invocation)

7) Commits (small, reviewable; REQUIRED commit body format)
Make small logical commits (at least 2):
- Commit 1: sprint ticket formalization + docs updates
- Commit 2: data policy checker + test integration
Each commit MUST include a body with:
- Tests: ...
- Artifacts: ... (or "none")
- Docs: ...

8) Run log hygiene (do not repeat ticket-10 mistakes)
- COMMANDS.md must be ONLY commands executed, in order (copy/pasteable).
- RESULTS.md must be concrete. Do not include placeholder strings like "[updated RESULTS", "PENDING", or "TODO" anywhere.
- META.json must include real SHAs:
  - git_sha_before = the SHA at start of work
  - git_sha_after  = output of git rev-parse HEAD after final commit
  - ticket_id = "ticket-11"
  - branch = current branch name
  - include a short env summary

9) Finish: generate the bundle and record its path
- make gpt-bundle TICKET=$TICKET RUN_NAME=$RUN_NAME
- In docs/agent_runs/$RUN_NAME/RESULTS.md, record the exact bundle path printed/created.

Suggested Codex invocations (pick one):
- Interactive (safer): codex --sandbox workspace-write --ask-for-approval on-request
- Safe autonomy: codex --full-auto
- Keep web search OFF unless necessary. If enabled, record sources in the run log.

Human merge checklist (include in RESULTS.md):
- No restricted data tracked in git (HEAD).
- scripts/check_data_policy.py works and is enforced by tests/make target.
- PROGRESS.md + KNOWN_ISSUES.md updated.
- Bundle generated and path recorded.
