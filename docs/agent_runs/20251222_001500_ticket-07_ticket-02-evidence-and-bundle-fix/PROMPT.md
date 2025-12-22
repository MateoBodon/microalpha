TICKET: ticket-07
RUN_NAME: 20251222_001500_ticket-07_ticket-02-evidence-and-bundle-fix  # update timestamp if needed

Read FIRST (do not skip):
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Stop-the-line:
- No fabricated results.
- No WRDS raw exports committed.
- No “green by disabling” (don’t weaken tests to pass).
- If holdout selection can see holdout data, stop and fix.

Goal:
Ticket-02 failed review because the bundle did NOT contain evidence of holdout implementation/tests/artifacts and the bundle itself is internally inconsistent (DIFF.patch != bundled run-log contents).
Fix this by producing a reviewable, integrity-correct bundle that satisfies ticket-02 acceptance criteria.

Do NOT write a long plan. Execute in this order:

1) Inspect current state
- Locate holdout config schema + implementation:
  - src/microalpha/config_wfv.py
  - src/microalpha/walkforward.py
  - tests/test_walkforward.py
- Confirm configs exist:
  - configs/wfv_flagship_sample_holdout.yaml (or equivalent)
  - configs/wfv_flagship_wrds.yaml includes holdout fields
- Check current bundle tool behavior:
  - tools/gpt_bundle.py (how DIFF.patch is generated; what commit range is used)

2) Implement/repair holdout acceptance criteria (ticket-02)
If anything is missing or not provably correct, implement it now:
- WFV config must support an explicit holdout window excluded from optimization.
- Artifacts must include:
  - oos_returns.csv (concatenated OOS test windows)
  - holdout_metrics.json (computed only on holdout)
- Add/ensure a test that FAILS if holdout data affects selection:
  - Construct a toy dataset where the “best param” differs if holdout is included.
  - Assert selected param matches selection-only optimum.

3) Fix bundle integrity mismatch (DIFF.patch must match bundled files)
- Update tools/gpt_bundle.py so that DIFF.patch corresponds exactly to the bundled tree state.
  Options (pick one, but make it deterministic):
  A) Bundle a commit range file (COMMITS.txt) and generate DIFF.patch from that exact range.
  B) Generate DIFF.patch from the merge-base with main/master to HEAD (document which base).
- Add a self-check in gpt_bundle.py:
  - After writing DIFF.patch, verify that the patched file versions match the actual bundled files for the files included in the bundle (at least the run log folder and PROGRESS.md). If mismatch, fail.

4) Doc hygiene
- Update PROGRESS.md:
  - Replace any absolute local paths like /Volumes/... with $WRDS_DATA_ROOT.
  - Do NOT mark ticket-02 “Done” until the acceptance criteria tests + sample artifacts are produced in this run.
- Update docs/CODEX_SPRINT_TICKETS.md:
  - Mark ticket-02 FAIL (review) with reason.
  - Add ticket-07 at bottom with acceptance criteria.

5) Run minimal verification (required)
- Tests:
  - pytest -q tests/test_walkforward.py
- Sample holdout run (must produce artifacts):
  - microalpha wfv --config configs/wfv_flagship_sample_holdout.yaml --out artifacts/sample_wfv_holdout
  - Verify oos_returns.csv and holdout_metrics.json exist; record exact paths in RESULTS.md.
- Optional real-data smoke:
  - If WRDS_DATA_ROOT is set and exports exist, run the smallest WRDS holdout-smoke end-to-end.
  - If not available, log "SKIPPED (blocked)" (do NOT fake).

6) Run logs (mandatory)
Create: docs/agent_runs/<RUN_NAME>/
- PROMPT.md (this prompt verbatim)
- COMMANDS.md (every command run)
- RESULTS.md (what changed, why, and exact artifact paths; include bundle path at end)
- TESTS.md (commands + pass/fail)
- META.json (git sha before/after as immutable SHAs; env; config hashes; data mode)

7) Commit on feature branch
- Branch: feat/ticket-07-ticket-02-evidence-and-bundle-fix
- Commit message: "ticket-07: finalize ticket-02 evidence + bundle integrity"
- Commit body MUST include:
  - Tests: ...
  - Artifacts: ...
  - Docs: ...

8) Generate the review bundle (required)
At the very end:
- make gpt-bundle TICKET=ticket-07 RUN_NAME=<RUN_NAME>
Record the bundle path in docs/agent_runs/<RUN_NAME>/RESULTS.md

Suggested Codex invocation (safe):
- codex --profile safe --sandbox workspace-write --ask-for-approval on-request
(Do NOT use full-autonomy unless explicitly requested by the user.)

Human merge checklist (short):
- pytest passes and includes a holdout-leakage-catching test
- sample holdout artifacts exist (oos_returns.csv + holdout_metrics.json)
- DIFF.patch matches bundled files (no mismatch)
- no /Users/ or /Volumes/ paths in committed docs
- bundle generated and path recorded
