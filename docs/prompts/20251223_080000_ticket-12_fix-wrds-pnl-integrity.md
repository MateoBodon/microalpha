# Codex CLI Prompt — microalpha — ticket-12 (Fix WRDS PnL / flat-return integrity)

You are Codex working in the `microalpha` repo.

Ticket: **ticket-12 — Fix PnL/metrics integrity for WRDS smoke (no more flat equity with trades/costs)**

## Stop-the-line rules (AGENTS.md is binding)
- Do NOT fabricate results or claim outputs you didn’t produce.
- Do NOT weaken evaluation validity (no lookahead shortcuts, no “disable checks to go green”).
- Do NOT commit to or push directly to `main`. Work on a feature branch only.
- Do NOT commit raw WRDS exports or license-restricted data. Aggregated metrics/reports are okay if license-safe.
- If you find the current metrics are inconsistent (e.g., trades/costs but flat equity), treat that as a correctness bug and fix it (do not paper over with reporting).

## Run identity (required)
Set:
- RUN_NAME = `20251223_080000_ticket-12_fix-wrds-pnl-integrity`
- TICKET_ID = `ticket-12`

Create: `docs/agent_runs/${RUN_NAME}/` containing:
- `PROMPT.md` (this prompt verbatim)
- `COMMANDS.md` (every command run, in order)
- `RESULTS.md` (what changed, why, before/after evidence)
- `TESTS.md` (tests run + outcomes)
- `META.json` matching `docs/DOCS_AND_LOGGING_SYSTEM.md` (use the required keys; include real git SHAs, started/finished UTC, branch_name, dataset_id, config paths + sha256, artifact/report paths; NO absolute local paths)

## Step 0 — Fix sprint ticket source-of-truth (required, minimal)
The current `docs/CODEX_SPRINT_TICKETS.md` appears to contain duplicated/conflicting content (including an embedded “## File: … ```md” block).
- Clean it so there is exactly ONE authoritative ticket list.
- Add a proper `ticket-12` section with: goal, why, acceptance criteria, minimal tests/commands.
Keep this edit small and obvious (no rewrites).

## Step 1 — Inspect and reproduce the inconsistency (no long plan)
Immediately inspect:
- `AGENTS.md`
- `docs/PLAN_OF_RECORD.md`
- `docs/DOCS_AND_LOGGING_SYSTEM.md`
- `project_state/CURRENT_RESULTS.md` and the latest WRDS smoke/flagship notes

Then focus on the known bad symptom:
- WRDS smoke run has nonzero turnover/trades/costs but report says returns are “zero variance” / equity effectively flat.

Find where this is coming from:
- Locate where equity curve is generated and where returns are computed.
- Identify how costs (commission/slippage/borrow) flow into cash/equity.
Likely files (confirm in repo, don’t assume):
- `src/microalpha/portfolio.py`, `src/microalpha/broker.py`, `src/microalpha/execution.py`
- `src/microalpha/reporting/analytics.py` / `src/microalpha/risk_stats.py` / metrics code
- any artifact writer for `equity_curve.csv` / `metrics.json`

Add a short diagnostic script if helpful:
- `scripts/diagnose_artifact_integrity.py --artifact-dir <dir>`
It should load `equity_curve.csv`, `metrics.json`, and `trades.jsonl` and print reconciliation checks.

## Step 2 — Implement the fix (correctness first)
Goal: If `num_trades > 0` OR `total_costs > 0`, the equity curve / return series must not be exactly constant, and PnL must reconcile.

Implement:
1) **PnL reconciliation / invariants**
Add a function that checks (with tolerance):
- final_equity ≈ initial_equity + realized_pnl + unrealized_pnl - total_costs (and any other accounted components)
- If turnover > 0 then executed trades exist (or explicitly explain “desired vs executed” if model supports that)
- If costs > 0 then equity must reflect them (cannot remain exactly unchanged)

Where to enforce:
- Ideally at the end of a run before writing metrics/report (fail fast for headline runs; for smoke runs you can emit `run_invalid=true` in manifest + loud report banner, but do NOT silently pass).

2) **Fix the root cause**
Based on your diagnosis, fix the actual bug (common culprits):
- costs computed but never applied to cash/equity
- equity curve writer uses the wrong series (e.g., gross exposure instead of equity)
- returns computed from a series that is accidentally all zeros (e.g., wrong column, wrong dtype, rounding/truncation)

## Step 3 — Add objective regression tests (must be falsifiable)
Add unit tests that do NOT require WRDS:
- Build a tiny synthetic price series and force a simple trade + cost.
- Assert:
  - equity changes when a cost is applied (even if price doesn’t move)
  - the reconciliation check passes for a known scenario
- Add a test that would have caught the current symptom:
  - if trades/costs exist AND equity series is constant -> must raise or mark invalid explicitly.

If the repo has a `make test-fast` target, use it; if it doesn’t, add it as an alias for the fastest deterministic pytest command (documented).

## Step 4 — Run minimal sufficient tests + record them
Run and record in `TESTS.md`:
- `make test-fast` (minimum)
- `pytest -q` (if test-fast is not the full suite; at least include the new tests)

## Step 5 — Real-data smoke (required when WRDS available)
If `WRDS_DATA_ROOT` is set and points to a real path:
- Re-run the WRDS smoke pipeline and report:
  - `WRDS_DATA_ROOT=... make wfv-wrds-smoke`
  - `WRDS_DATA_ROOT=... make report-wrds-smoke`
- Then run your new diagnostic script on the produced artifact dir and confirm:
  - equity_curve variance > 0 OR (if truly no trades) trades/costs are 0
  - reconciliation check passes (or the run is explicitly flagged invalid with a loud reason)

If WRDS is not available:
- Run the sample pipeline and render a report:
  - `make wfv` and `make report-wfv` (or the repo’s equivalent)

Record exact commands in `COMMANDS.md` and the artifact/report paths in `RESULTS.md` + `META.json`.

## Step 6 — Update living docs
Always:
- `PROGRESS.md` (dated bullet for ticket-12: what changed + what’s next)

If you materially changed correctness/validity or results interpretation:
- `project_state/KNOWN_ISSUES.md` (update/remove “flat equity with trades/costs” if fixed; otherwise make it sharper)
- `project_state/CURRENT_RESULTS.md` (only if you ran new public-facing results; keep disclaimers)

## Step 7 — Git workflow (required)
- Create feature branch: `codex/ticket-12-fix-wrds-pnl-integrity`
- Make small logical commits.
- Commit message format:
  - Subject: `ticket-12: fix PnL/equity integrity checks`
  - Body must include:
    - `Tests: ...`
    - `Artifacts: ...` (paths; use `$WRDS_DATA_ROOT` placeholder, no absolute paths)
    - `Docs: ...`

Do NOT merge to main.

## Step 8 — Bundle for review (required)
Finish by generating a new review bundle and record its path in `docs/agent_runs/${RUN_NAME}/RESULTS.md`:
- `make gpt-bundle TICKET=ticket-12 RUN_NAME=${RUN_NAME}`

## Suggested Codex invocations
Interactive approvals:
- `codex --sandbox workspace-write --ask-for-approval on-request`
Non-interactive, more autonomous (still sandboxed):
- `cat docs/prompts/<PROMPT_FILE>.md | codex exec --full-auto --cd . -`

## Human merge checklist (brief; include in RESULTS.md)
- Feature branch only; no main commits
- Tests pass; commands logged
- No raw WRDS data committed; no absolute local paths in docs
- Run log schema matches docs/DOCS_AND_LOGGING_SYSTEM.md
- Ticket file cleaned/deduped; ticket-12 added with acceptance criteria
