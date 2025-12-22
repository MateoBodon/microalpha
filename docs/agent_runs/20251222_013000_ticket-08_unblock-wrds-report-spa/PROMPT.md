TICKET: ticket-08
RUN_NAME: 20251222_013000_ticket-08_unblock-wrds-report-spa  # update timestamp if needed

Read FIRST (do not skip):
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md
- PROGRESS.md
- project_state/KNOWN_ISSUES.md
- project_state/CURRENT_RESULTS.md

Stop-the-line rules (AGENTS.md):
- No fabricated results.
- No raw WRDS exports or credentials committed.
- No “green by disabling.” If a statistic is invalid, report it explicitly and truthfully; do not silently skip without logging.

Goal:
Unblock WRDS reporting by making the SPA step and report pipeline robust to degenerate cases (all-zero comparator t-stats, empty/flat return series, zero trades). The report must complete while clearly flagging “not interpretable” conditions.

Do NOT write a long plan. Execute in this order:

1) Reproduce the failure (from logs / existing artifacts)
- From PROGRESS.md and CURRENT_RESULTS.md, identify the most recent WRDS artifact dir mentioned (example: artifacts/wrds_flagship/<RUN_ID>).
- Attempt report-only runs (these should not require WRDS exports):
  - If WRDS artifact dir exists locally: `microalpha report --artifact-dir artifacts/wrds_flagship/<RUN_ID>`
  - Always: `microalpha report --artifact-dir artifacts/sample_wfv_holdout/<RUN_ID>`
- Capture the exact error and stack trace in docs/agent_runs/<RUN_NAME>/TESTS.md.

2) Inspect the reporting + inference code paths
Look for where SPA is computed and where it fails:
- Likely modules (inspect, don’t assume):
  - src/microalpha/reporting/summary.py
  - src/microalpha/reporting/tearsheet.py
  - src/microalpha/risk_stats.py (SPA / reality check)
  - src/microalpha/metrics.py (return series / trade counts)
  - src/microalpha/reporting/* (rendering helpers)
- Locate the exact condition: “SPA comparator t-stats are all zero” (grep for that message).

3) Implement robust behavior (no hiding)
A) SPA edge-case handling
- If SPA inputs are invalid (empty list, all zeros, all NaNs, insufficient sample), do:
  - Return a structured “skipped” result with a reason string.
  - In the report summary, render a visible section:
    - “SPA: skipped — <reason>”
  - In artifacts/manifest (or report JSON), record `spa_status: skipped` and `spa_skip_reason: ...`.

B) Zero-activity / flat-series handling
- Detect and report (do not crash) when:
  - num_trades == 0
  - returns variance == 0 (flat equity)
- Add a clear “Run is degenerate” warning section in the report output.
- Fix/clarify turnover vs trade count:
  - If current code can produce turnover > 0 with 0 trades, either:
    - correct the metric (executed turnover should be 0), OR
    - rename to “desired_turnover” vs “executed_turnover” and update docs/report labels.

4) Add tests that would catch regressions (must be falsifiable)
- Add unit tests for:
  - SPA skip path: feed all-zero comparator stats and assert report completes and includes explicit “skipped” marker.
  - Zero-trade path: create a minimal artifact fixture with zero trades and assert report completes and flags degeneracy.
  - Turnover/trade invariant (or metric naming): enforce consistency.
- Run: `pytest -q` and record output.

5) Minimal end-to-end verification
- Re-run:
  - `microalpha report --artifact-dir artifacts/sample_wfv_holdout/<RUN_ID>`
  - If WRDS artifact dir exists: `microalpha report --artifact-dir artifacts/wrds_flagship/<RUN_ID>`
- Ensure reports are generated and the SPA section is either valid or explicitly skipped with reason.

6) Documentation updates (required)
- Update PROGRESS.md with ticket-08 status + run log path.
- Update project_state/KNOWN_ISSUES.md if the SPA/report blocker is resolved or recharacterized.
- Update CHANGELOG.md with a short entry (“reporting: SPA edge-case handling; degenerate-run warnings”).

7) Run logs (required)
Create docs/agent_runs/<RUN_NAME>/ with:
- PROMPT.md (this prompt)
- COMMANDS.md (every command run, in order)
- RESULTS.md (what changed; what reports now succeed; exact report paths)
- TESTS.md (pytest + report commands; pass/fail; key outputs)
- META.json (immutable git shas before/after; env; data mode; artifacts referenced)

8) Commit + bundle (required)
- Branch: feat/ticket-08-unblock-wrds-report
- Commit message: "ticket-08: make reporting robust to SPA/degenerate cases"
- Commit body MUST include:
  - Tests: ...
  - Artifacts: ...
  - Docs: ...
- End: `make gpt-bundle TICKET=ticket-08 RUN_NAME=<RUN_NAME>`
  - Record the bundle path in RESULTS.md.

Suggested Codex invocation (safe):
- codex --profile safe --sandbox workspace-write --ask-for-approval on-request
(Do NOT use full-autonomy unless the user explicitly asks.)
