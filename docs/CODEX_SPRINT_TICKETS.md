# CODEX SPRINT TICKETS — microalpha (Next Sprint)

**Sprint objective (1–2 weeks):** Produce one *resume-credible* real-data demo run pipeline: tightened risk/cost caps, baseline comparison, and auditable artifacts/logs.

**Ground-truth diagnosis input:** see `docs/gpt_outputs/` (Prompt‑1 output) — validity first.

---

## ticket-01 — Tighten WRDS flagship risk/cost caps + add WRDS smoke run + publish result skeleton

**Goal (1 sentence):** Make the WRDS pipeline produce audit-grade artifacts under explicit risk/cost caps, with a required WRDS “smoke” run and report outputs.

**Status:** FAIL (review) — docs/diff mismatch; fixed in ticket-06.

**Why (ties to diagnosis):**
- Current real-data evidence is *not resume-credible* (drawdown/turnover/inference). Before chasing “better metrics,” we need **explicit caps + cost reporting + reproducible real-data smoke**.

**Files/modules likely touched:**
- `configs/wfv_flagship_wrds.yaml`
- `configs/wfv_flagship_wrds_smoke.yaml` *(new)*
- `src/microalpha/portfolio.py` / risk control modules (where caps live)
- `src/microalpha/metrics.py` and/or reporting section that shows net/gross + cost breakdown
- `Makefile` (add `wfv-wrds-smoke`, `report-wrds-smoke` targets if missing)
- `.gitignore` (ensure WRDS exports never get committed)

**Acceptance criteria (objective + falsifiable):**
- A WRDS smoke config exists and runs end-to-end when `WRDS_DATA_ROOT` is set:
  - `microalpha wfv --config configs/wfv_flagship_wrds_smoke.yaml --out artifacts/...` completes without error
- Risk/cost caps are explicit in config and recorded in artifacts (`manifest.json`):
  - max gross leverage, max single-name weight, turnover clamp, borrow model parameters
- Report output includes:
  - net vs gross metrics
  - cost breakdown summary
  - exposures (gross/net) time series (or at minimum: summary stats)
- No WRDS raw data is added to git (verify clean `git status` + `.gitignore` coverage).

**Minimal tests/commands to run:**
- `pytest -q`
- `make sample && make report`
- `WRDS_DATA_ROOT=/abs/path/to/wrds make wfv-wrds-smoke` *(or direct CLI if Make target absent)*
- `WRDS_DATA_ROOT=/abs/path/to/wrds make report-wrds-smoke`

**Expected artifacts/logs to produce:**
- `docs/agent_runs/<RUN_NAME>/{PROMPT.md,COMMANDS.md,RESULTS.md,TESTS.md,META.json}`
- `artifacts/<wrds_smoke_run_id>/manifest.json`
- `artifacts/<wrds_smoke_run_id>/metrics.json`
- `artifacts/<wrds_smoke_run_id>/report/*` (summary + tearsheet figures)

**Documentation updates required:**
- `PROGRESS.md` (always)
- `project_state/KNOWN_ISSUES.md` if any new validity risk is found
- `CHANGELOG.md` if user-visible config/behavior changes

**End-of-ticket (must include these three lines):**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

---

## ticket-02 — Add holdout evaluation mode (WFV selection ≠ final test)

**Goal (1 sentence):** Separate parameter selection (WFV) from final reporting (holdout) to prevent p-hacking.

**Status:** FAIL (review) — bundle missing holdout evidence + DIFF.patch mismatch (address in ticket-07).

**Why (ties to diagnosis):**
- Without a locked holdout, repeated WFV reruns can still become p-hacking. We need a hard boundary.

**Files/modules likely touched:**
- `src/microalpha/walkforward.py`
- `src/microalpha/config_wfv.py`
- `configs/wfv_flagship_wrds.yaml` (add holdout date range)
- `tests/test_walkforward.py`

**Acceptance criteria:**
- WFV config supports an explicit holdout range that is excluded from optimization.
- Artifacts explicitly include:
  - `oos_returns.csv` (concatenated OOS test windows)
  - `holdout_metrics.json` (computed only on holdout)
- Test proves optimizer never sees holdout returns (fails if violated).

**Minimal tests/commands to run:**
- `pytest -q tests/test_walkforward.py`
- `microalpha wfv --config configs/wfv_flagship_sample.yaml --out artifacts/sample_wfv_holdout`

**Expected artifacts/logs to produce:**
- `docs/agent_runs/<RUN_NAME>/...`
- `artifacts/sample_wfv_holdout/*` (including holdout artifacts)

**Documentation updates required:**
- `PROGRESS.md`
- Update any protocol docs that describe evaluation (this sprint may add `docs/PLAN_OF_RECORD.md` references)

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

---

## ticket-03 — Fix factor regression alignment + document true factor frequency

**Goal (1 sentence):** Make factor regression frequency-safe (no silent misalignment) and ensure docs match reality.

**Why (ties to diagnosis):**
- A daily vs weekly mismatch (or any alignment bug) is an interview trust-killer.

**Files/modules likely touched:**
- `reports/factors_ff.py`
- `src/microalpha/reporting/summary.py`
- factor sample data under `data/factors/` (doc only; do not change WRDS-derived)
- `tests/test_reporting_analytics.py`

**Acceptance criteria:**
- Regression utility detects / enforces alignment (explicit resampling if needed) and logs frequency.
- A test fails if factor and return indexes are misaligned or if sample length changes silently.
- Docs explicitly state the factor sample frequency + alignment rules.

**Minimal tests/commands to run:**
- `pytest -q tests/test_reporting_analytics.py`
- `python reports/factors_ff.py --help` (and one run on a sample artifact dir)

**Expected artifacts/logs:**
- `docs/agent_runs/<RUN_NAME>/...`
- updated factor regression output table in report (if applicable)

**Documentation updates required:**
- `PROGRESS.md`
- update any factor page/source docs

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

---

## ticket-04 — Add red-team leakage tests + “unsafe execution” manifest flag

**Goal (1 sentence):** Make common leakage failure modes impossible to hide.

**Why (ties to diagnosis):**
- Interviewers will probe same-tick fills, signal timing, and any mode that can accidentally allow lookahead.

**Files/modules likely touched:**
- `tests/test_no_lookahead.py` *(new)*
- `src/microalpha/engine.py`
- `src/microalpha/portfolio.py`
- `src/microalpha/manifest.py` (or wherever manifest fields are built)

**Acceptance criteria:**
- Test 1: future-return-derived signal triggers an error / invariant violation.
- Test 2: any same-tick fill mode requires explicit config opt-in; manifest records `unsafe_execution: true`.

**Minimal tests/commands to run:**
- `pytest -q tests/test_no_lookahead.py`

**Expected artifacts/logs:**
- `docs/agent_runs/<RUN_NAME>/...`
- updated manifest schema documentation (if present)

**Documentation updates required:**
- `PROGRESS.md`
- `project_state/KNOWN_ISSUES.md` if a leakage bug is found and fixed

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

---

## ticket-05 — Add experiment registry (manifest index) + “no cherry-pick” reporting

**Goal (1 sentence):** Make it easy to show *all* runs and prevent cherry-picking.

**Why (ties to diagnosis):**
- Without a runs ledger, good-looking artifacts can be accused of being selected after many failures.

**Files/modules likely touched:**
- `reports/generate_summary.py` (or new `reports/runs_index.py`)
- `src/microalpha/manifest.py`
- docs describing how to interpret the run registry

**Acceptance criteria:**
- A script can scan `artifacts/*/manifest.json` and output `reports/summaries/runs_index.csv` deterministically.
- For sample runs in CI/local, the index is stable.
- Docs explain “do not cherry-pick”: include criteria for what gets reported as headline.

**Minimal tests/commands to run:**
- `pytest -q`
- `python reports/runs_index.py --artifacts-root artifacts --out reports/summaries/runs_index.csv` *(or equivalent)*

**Expected artifacts/logs:**
- `docs/agent_runs/<RUN_NAME>/...`
- `reports/summaries/runs_index.csv`

**Documentation updates required:**
- `PROGRESS.md`
- update reproducibility/reporting docs

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

---

## ticket-06 — Make bundles commit-consistent + commit living-doc updates for ticket-01

**Goal (1 sentence):** Ensure `make gpt-bundle` produces a bundle whose included tracked files exactly match `DIFF.patch` (no dirty worktree), and commit the missing living-doc updates from ticket-01.

**Why (ties to diagnosis):**
- Current bundle shows evidence that’s not in git; this breaks auditability and fails the repo’s own protocol.

**Files/modules likely touched:**
- `tools/gpt_bundle.py`
- `Makefile`
- `PROGRESS.md`
- `project_state/CURRENT_RESULTS.md`
- `project_state/KNOWN_ISSUES.md`
- `docs/CODEX_SPRINT_TICKETS.md`

**Acceptance criteria (objective + falsifiable):**
- `git status --porcelain` is clean before bundling.
- `make gpt-bundle ...` succeeds and the resulting `DIFF.patch` includes the living-doc edits (or the bundle explicitly contains a clean worktree status).
- No absolute local machine paths leak into committed docs (use placeholders like `$WRDS_DATA_ROOT`).

**Minimal tests/commands to run:**
- `python3 -m compileall tools`
- `make gpt-bundle TICKET=ticket-06 RUN_NAME=<RUN_NAME>`

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

---

## ticket-07 — Fix ticket-02 evidence + bundle integrity

**Goal (1 sentence):** Produce a reviewable bundle that proves holdout selection is isolated and the required artifacts/tests exist; fix DIFF.patch↔bundle mismatch.

**Status:** Done.

**Acceptance criteria:**
- `pytest -q tests/test_walkforward.py` passes and includes a test that fails if holdout data influences selection.
- Sample holdout run produces and logs paths to:
  - `oos_returns.csv`
  - `holdout_metrics.json`
- Bundle integrity: `DIFF.patch` matches bundled run-log contents (no mismatches).
- `PROGRESS.md` uses `$WRDS_DATA_ROOT` placeholder (no `/Volumes/...`).

**Minimal tests/commands to run:**
- `pytest -q tests/test_walkforward.py`
- `microalpha wfv --config configs/wfv_flagship_sample_holdout.yaml --out artifacts/sample_wfv_holdout`
- `make gpt-bundle TICKET=ticket-07 RUN_NAME=<RUN_NAME>`

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

---

## ticket-08 — Unblock WRDS reporting: SPA edge cases + zero-activity invariants

**Goal (1 sentence):** Make reporting resilient to SPA edge cases and degenerate runs so WRDS reports never crash on zero-activity or invalid comparator stats.

**Status:** Implemented (review pending). Run log: `docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/`.

**Why (ties to PROGRESS + KNOWN_ISSUES):**
- `PROGRESS.md` (2025-12-21) notes the WRDS report failed at the SPA step.
- `project_state/KNOWN_ISSUES.md` flags zero-trade/flat SPA comparator t-stats as a report-blocking degenerate case.

**Acceptance criteria (objective):**
- Report must not crash on invalid/all-zero SPA comparator stats; must surface “SPA skipped: <reason>”.
- Report must surface “Run is degenerate” for zero trades / flat equity (explicit reasons).
- Invariant: if total_turnover > 0 then num_trades > 0 (or clearly distinguish desired vs executed).
- Tests cover SPA-skip + degenerate warning + turnover/trade invariant.

**Minimal tests/commands:**
- `pytest -q`
- `microalpha report --artifact-dir artifacts/sample_wfv_holdout/<RUN_ID>`
- `microalpha report --artifact-dir artifacts/wrds_flagship/<RUN_ID>`  *(report-only; no WRDS exports)*

---

## ticket-09 — Enforce sprint ticket ids in gpt-bundle

**Goal (1 sentence):** Prevent bundling when a run’s ticket id is missing from the sprint tickets file.

**Status:** Done. Run log: `docs/agent_runs/20251222_034500_ticket-09_ticket-id-enforcement/`.

**Why (ties to process failure):**
- Ticket-08 failed review because it was not defined in `docs/CODEX_SPRINT_TICKETS.md` even though a run log existed.

**Acceptance criteria:**
- `tools/gpt_bundle.py` reads `docs/agent_runs/<RUN_NAME>/META.json` and fails fast if `ticket_id` is missing from the sprint tickets headers.
- Error message clearly explains how to fix the issue (add the missing ticket section).

**Minimal tests/commands:**
- `pytest -q`
- `python3 -m compileall tools`
