# CODEX SPRINT TICKETS — microalpha (Next Sprint)

**Sprint objective (1–2 weeks):** Produce one *resume-credible* real-data demo run pipeline: tightened risk/cost caps, baseline comparison, and auditable artifacts/logs.

**Ground-truth diagnosis input:** see `docs/gpt_outputs/` (Prompt‑1 output) — validity first.

---

## ticket-24 — WRDS resume metrics refresh (flagship rerun)

**Goal (1 sentence):** Rerun WRDS flagship on codex-worker (AX162-S) and refresh resume-facing real-data metrics docs from the new artifacts.

**Status:** Done.

**Why (ties to diagnosis):**
- Resume-facing metrics must reflect the latest real-data flagship run with auditable artifacts.

**Acceptance criteria (objective + falsifiable):**
- New artifacts exist at `artifacts/wrds_flagship/<RUN_ID>/`.
- `docs/results_wrds_resume.md` references `<RUN_ID>`, git SHA, exact commands, and headline metrics with clear labeling.
- `project_state/CURRENT_RESULTS.md` updated to the same `<RUN_ID>` and snapshot.
- Run log exists under `docs/agent_runs/<RUN_NAME>/` with required files and recorded artifact/report paths.
- `make check-data-policy` and `make validate-runlogs` pass.
- No WRDS raw files staged/committed.

**Minimal tests/commands to run:**
- `make test-fast`
- `make check-data-policy`
- `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds make wrds-flagship`
- `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds make report-wrds`
- `make validate-runlogs`
- `python3 tools/agentic/project_state_refresh.py --zip`

**End-of-ticket:**
- **Tests run:** `make test-fast`; `make check-data-policy`; `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make wrds-flagship`; `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make report-wrds`; `make validate-runlogs`; `pytest -q tests/test_docs_links.py`; `python3 tools/agentic/project_state_refresh.py --zip`.
- **Artifacts/logs:** `artifacts/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d/`; `docs/agent_runs/20260126_011723_ticket-24_wrds-resume-metrics-refresh/`; `docs/_bundles/project_state_20260126_013606.zip`; `docs/_bundles/gpt_bundle_20260126_014244_TICKET-24_wrds-resume-metrics-refresh.zip`.
- **Documentation updates:** `docs/results_wrds.md`, `docs/results_wrds_resume.md`, `reports/summaries/wrds_flagship.md`, `project_state/CURRENT_RESULTS.md`, `PROGRESS.md`, `docs/agent_runs/20260126_011723_ticket-24_wrds-resume-metrics-refresh/`, `docs/img/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d/`.

---

## ticket-24c — Ship WRDS refresh outputs (docs/logs/images)

**Goal (1 sentence):** Stage, commit, and push the WRDS refresh outputs so resume metrics remain auditably current.

**Status:** Done.

**Why (ties to diagnosis):**
- Ensure the latest WRDS refresh outputs are fully tracked and verifiable.

**Acceptance criteria (objective + falsifiable):**
- Docs/results and project_state references consistently point to `2026-01-26T01-22-23Z-e76eb4d`.
- Required run logs and WRDS images are tracked and pass run-log/data-policy/link validation.
- `gpt_bundle.zip` generated for ticket-24c.
- Git status clean on `main` after commit and push.

**Minimal tests/commands to run:**
- `make test-fast`
- `make check-data-policy`
- `pytest -q tests/test_docs_links.py`
- `make validate-runlogs`

**End-of-ticket:**
- **Tests run:** `source .venv/bin/activate && make test-fast`; `make check-data-policy`; `pytest -q tests/test_docs_links.py`; `make validate-runlogs`.
- **Artifacts/logs:** `docs/agent_runs/20260126_034509_ticket-24c_ship-wrds-refresh/`; `docs/agent_runs/20260126_000243_ticket-00_project-state-refresh/`; `docs/agent_runs/20260126_011723_ticket-24_wrds-resume-metrics-refresh/`; `docs/agent_runs/20260126_023947_ticket-24b_finalize-wrds-refresh/`; `docs/img/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d/`; `docs/_bundles/gpt_bundle_20260126_035231_TICKET-24c_ship-wrds-refresh.zip`.
- **Documentation updates:** `docs/results_wrds.md`, `docs/results_wrds_resume.md`, `reports/summaries/wrds_flagship.md`, `reports/summaries/wrds_flagship_metrics.json`, `project_state/BACKLOG.md`, `project_state/CURRENT_RESULTS.md`, `project_state/KNOWN_ISSUES.md`, `project_state/OPEN_QUESTIONS.md`, `project_state/ROADMAP.md`, `project_state/RUNBOOK.md`, `project_state/_generated/git_branch.txt`, `project_state/_generated/git_diff.patch`, `project_state/_generated/git_head.txt`, `project_state/_generated/git_log.txt`, `project_state/_generated/git_ls_files.txt`, `project_state/_generated/git_status.txt`, `PROGRESS.md`, `CHANGELOG.md`, `docs/DECISIONS.md`, `docs/tickets/TICKET-24c_ship-wrds-refresh.md`, `docs/prompts/20260126_034509_ticket-24c_ship-wrds-refresh.md`, `docs/gpt_outputs/mi01-25-26prompt1-diagnosis.md`.

---



## ticket-24d — Ship WRDS refresh to main (docs/logs/images)

**Goal (1 sentence):** Complete ticket-24c by committing any remaining WRDS refresh docs/run logs/images, merging to main, and pushing a clean audited state.

**Status:** Done.

**Why (ties to diagnosis):**
- Ensure the latest WRDS refresh outputs are fully tracked and audit-ready on main.

**Acceptance criteria (objective + falsifiable):**
- WRDS docs consistently reference run `2026-01-26T01-22-23Z-e76eb4d`.
- `project_state` snapshot reflects the same run_id.
- Required run logs + ticket docs are tracked and `make validate-runlogs` passes.
- `make check-data-policy` passes with zero WRDS raw files staged.
- `pytest -q tests/test_docs_links.py` passes.
- Branch merged to `origin/main`; git status clean on main.
- `gpt_bundle.zip` produced for ticket-24d.

**Minimal tests/commands to run:**
- `make validate-runlogs`
- `make check-data-policy`
- `pytest -q tests/test_docs_links.py`
- `make test-fast`

**End-of-ticket:**
- **Tests run:** `source .venv/bin/activate && make validate-runlogs && make check-data-policy && pytest -q tests/test_docs_links.py && make test-fast`.
- **Artifacts/logs:** `docs/agent_runs/20260126_151214_ticket-24d_ship-wrds-refresh-to-main/`; `docs/img/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d/`; `docs/_bundles/gpt_bundle_20260126_151835_TICKET-24d_ship-wrds-refresh-to-main.zip`.
- **Documentation updates:** `docs/CODEX_SPRINT_TICKETS.md`, `PROGRESS.md`, `CHANGELOG.md`, `docs/DECISIONS.md`, `docs/tickets/TICKET-24d_ship-wrds-refresh-to-main.md`, `docs/prompts/20260126_151214_ticket-24d_ship-wrds-refresh-to-main.md`, `docs/agent_runs/20260126_151214_ticket-24d_ship-wrds-refresh-to-main/`.

---

## ticket-23 — WRDS holdout nonzero trades (final holdout)

**Goal (1 sentence):** Fix WRDS final-holdout degeneracy (zero trades) and produce resume-credible real-data holdout metrics with a committed run log + summary doc.

**Status:** Done.

**Why (ties to diagnosis):**
- Current WRDS holdout window has zero trades; resume claims need a locked, non-degenerate holdout run.

**Acceptance criteria (objective + falsifiable):**
- WRDS final-holdout run produces `num_trades > 0` and non-NaN Sharpe/CAGR/MaxDD.
- `docs/results_wrds_resume.md` includes run_id, date range, universe, net-of-costs note, and headline metrics.
- Run log exists under `docs/agent_runs/<RUN_NAME>/` with required files and recorded artifact/report paths.
- `make test-fast`, `make check-data-policy`, `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make wfv-wrds`, and `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make report-wrds` succeed.
- WRDS_DATA_ROOT handling is consistent and documented.

**Minimal tests/commands to run:**
- `make test-fast`
- `make check-data-policy`
- `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make wfv-wrds`
- `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make report-wrds`

**End-of-ticket:**
- **Tests run:** `make check-data-policy`; `make test-fast`.
- **Artifacts/logs:** `artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18/`; `docs/agent_runs/20260125_224419_ticket-23_wrds-holdout-nonzero-trades/`.
- **Documentation updates:** `docs/results_wrds_resume.md`, `PROGRESS.md`, `CHANGELOG.md`, `project_state/KNOWN_ISSUES.md`, `project_state/CURRENT_RESULTS.md`, `docs/DECISIONS.md`.

---

## ticket-22 — WRDS resume metrics (holdout WFV + summary doc)

**Goal (1 sentence):** Produce resume-credible WRDS/CRSP holdout metrics with an auditable run log and clean summary doc (no licensed data).

**Status:** Planned.

**Why (ties to diagnosis):**
- Resume claims must be backed by a single, locked holdout run with reproducible artifacts and inference fields.

**Acceptance criteria (objective + falsifiable):**
- A new WRDS holdout WFV + report run completes using `$WRDS_DATA_ROOT`.
- Run log exists under `docs/agent_runs/<RUN_NAME>/` with required files.
- Summary doc (`docs/results_wrds_resume.md` or `docs/results_wrds.md`) includes: run_id, date range, universe, net-of-costs note, Sharpe_HAC, MaxDD, CAGR (if available), turnover, RealityCheck p, SPA p/status.
- `make check-data-policy` and `make test-fast` pass.

**Minimal tests/commands to run:**
- `make test-fast`
- `make check-data-policy`
- `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds make wfv-wrds`
- `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds make report-wrds`

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

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

## ticket-00 — Project state rebuild (doc regeneration)

**Goal (1 sentence):** Rebuild `project_state/` docs and indices with a traceable run log.

**Status:** Done.

**Why (ties to diagnosis):**
- Keep project state summaries current and auditable for interviews/reviews.

**Files/modules likely touched:**
- `tools/build_project_state.py`
- `tools/render_project_state_docs.py`
- `project_state/*`
- `PROGRESS.md`

**Acceptance criteria (objective + falsifiable):**
- `project_state/` docs are regenerated and include the latest run summaries.
- Run log exists under `docs/agent_runs/<RUN_NAME>/` with required metadata.

**Minimal tests/commands to run:**
- `python3 tools/build_project_state.py`
- `python3 tools/render_project_state_docs.py`

**Expected artifacts/logs to produce:**
- `docs/agent_runs/<RUN_NAME>/...`

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

---

## ticket-17 — Baseline suite + comparison reporting

**Goal (1 sentence):** Add baseline suite computation and baseline comparison reporting for headline runs, using the same calendar + universe rules.

**Why (ties to diagnosis):**
- Headline results must be contextualized with baseline performance to avoid cherry-picking.

**Acceptance criteria (objective + falsifiable):**
- Baselines computed on the same calendar and universe rules as the evaluated run.
- `artifacts/<run_id>/baselines.csv` exists with stable schema:
  - `date, flagship_net, eqw_universe, market_proxy, mom_12_1, cash_rf`
- Report includes baseline comparison table (Sharpe_HAC, MaxDD, CAGR, turnover) and overlay plot.
- Missing baselines are labeled with explicit reason (e.g., “missing market proxy: …”).
- Tests include:
  - synthetic lookahead guard for momentum formation window
  - deterministic baselines.csv schema/order check
- `make test-fast` is green and a baseline-enabled sample report is produced.
- If `WRDS_DATA_ROOT` is available, a WRDS baseline smoke report runs without committing raw data.

**Minimal tests/commands to run:**
- `make test-fast`
- `pytest -q tests/test_baselines.py`
- `make report` (or `make report-wfv` if sample report requires WFV artifacts)

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

---

## ticket-16 — Run-log META.json integrity + validator

**Goal (1 sentence):** Repair corrupted run-log META.json files and enforce validation via a dedicated script + Make target.

**Why (ties to diagnosis):**
- Run logs are the audit trail; broken META.json files undermine traceability and review integrity.

**Files/modules likely touched:**
- `scripts/validate_run_logs.py`
- `Makefile`
- `docs/agent_runs/*/META.json`
- `docs/CODEX_SPRINT_TICKETS.md`
- `PROGRESS.md`
- `project_state/KNOWN_ISSUES.md`
- `CHANGELOG.md`

**Acceptance criteria (objective + falsifiable):**
- All `docs/agent_runs/*/META.json` files parse as valid JSON and include required keys.
- `scripts/validate_run_logs.py` exits non-zero on any missing file/field or invalid SHA.
- `make validate-runlogs` runs the validator successfully.
- `make test-fast` includes run-log validation or documentation explicitly states it is a merge gate.
- Ticket IDs in run logs are validated against `docs/CODEX_SPRINT_TICKETS.md`.

**Minimal tests/commands to run:**
- `make test-fast`
- `make validate-runlogs`
- `python3 -m compileall tools scripts`

**Expected artifacts/logs to produce:**
- `docs/agent_runs/<RUN_NAME>/...`

**End-of-ticket:**
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

## ticket-18 — Agentic system scaffold bootstrap

**Goal (1 sentence):** Install the Agentic System Kit scaffold, preserve repo-specific docs, and generate the initial `project_state.zip`.

**Why (ties to diagnosis):**
- Future Codex/GPT runs need consistent run logs, prompts, and project-state bundles.

**Acceptance criteria (objective + falsifiable):**
- `AGENTS.md`, `PROJECT.md`, and `PROGRESS.md` updated with repo-specific info.
- `tools/agentic/` scripts present and usable.
- `python3 tools/agentic/project_state_refresh.py --zip` produces a zip bundle.
- Run log exists under `docs/agent_runs/<RUN_NAME>/` with required files.

**Minimal tests/commands to run:**
- `python3 tools/agentic/project_state_refresh.py --zip`
- `make test-fast`

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

---

## ticket-19 — Finish agentic scaffold cleanup

**Goal (1 sentence):** Remove bootstrap residue, track agentic scaffold files, and keep run logs + project_state indices visible to git.

**Why (ties to diagnosis):**
- Audit artifacts and scaffold files must be versioned to keep runs reproducible.

**Acceptance criteria (objective + falsifiable):**
- No stray `.bak` or `.append` files remain.
- `.gitignore` does not ignore `docs/agent_runs/**` or `project_state/_generated/**`.
- `tools/agentic/`, `PROJECT.md`, and `project_state/{README,RUNBOOK,BACKLOG}.md` are tracked.
- `python3 tools/agentic/project_state_refresh.py --zip` succeeds.
- `make test-fast` passes.

**Minimal tests/commands to run:**
- `python3 tools/agentic/project_state_refresh.py --zip`
- `make test-fast`

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

---

## ticket-03 — Fix factor regression alignment + document true factor frequency

**Goal (1 sentence):** Make factor regression frequency-safe (no silent misalignment) and ensure docs match reality.

**Status:** DONE. Run log: `docs/agent_runs/20251230_082853_ticket-03_factor-regression-alignment/`.

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

**Status:** DONE. Run log: `docs/agent_runs/20251229_173759_ticket-05_runs-index-registry/`.

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

**Status:** DONE. Run log: `docs/agent_runs/20251222_034500_ticket-09_ticket-id-enforcement/`.

**Why (ties to process failure):**
- Ticket-08 failed review because it was not defined in `docs/CODEX_SPRINT_TICKETS.md` even though a run log existed.

**Acceptance criteria:**
- `tools/gpt_bundle.py` reads `docs/agent_runs/<RUN_NAME>/META.json` and fails fast if `ticket_id` is missing from the sprint tickets headers.
- Error message clearly explains how to fix the issue (add the missing ticket section).

**Minimal tests/commands:**
- `pytest -q`
- `python3 -m compileall tools`

---

## ticket-10 — Block placeholder run logs in gpt-bundle

**Goal (1 sentence):** Prevent bundling with placeholder RESULTS.md and backfill ticket-09 results.

**Status:** Done. Run log: `docs/agent_runs/20251222_051500_ticket-10_block-placeholder-runlogs/`.

**Acceptance criteria:**
- Ticket-09 RESULTS.md is a concrete summary and includes the bundle path.
- `tools/gpt_bundle.py` blocks bundling if RESULTS.md contains placeholder markers.
- `tools/gpt_bundle.py` fails when env `TICKET` mismatches META.json ticket_id.
- Bundle generated for ticket-10 and path recorded in the run log.

**Minimal tests/commands:**
- `pytest -q`
- `python3 -m compileall tools`

---

## ticket-11 — Data policy scan + automated guardrails

**Goal (1 sentence):** Remove/quarantine license-risk artifacts and enforce data policy automatically.

**Acceptance criteria (objective):**
- `git ls-files | rg -n "strike,.*market_iv|\bsecid\b|best_bid|best_ask|best_offer" -S` returns no matches in tracked CSV/parquet-like artifacts (hits in code/docs allowed).
- Any existing `artifacts/heston/fit_*.csv` / similar quote-surface shaped files are either:
  - removed from HEAD (preferred), or
  - replaced with clearly synthetic/public-source inputs and provenance documented.
- A new script `scripts/check_data_policy.py` (or equivalent) exits non-zero on violations and is run in FAST (or at least documented as mandatory).
- `project_state/KNOWN_ISSUES.md` updated to reflect resolution (or narrowed scope with provenance).

---

## ticket-12 — Fix WRDS PnL / flat-return integrity

**Goal (1 sentence):** Ensure PnL, costs, and equity curves reconcile so WRDS smoke runs cannot show flat equity when trades/costs exist.

**Why (ties to diagnosis):**
- Recent WRDS smoke artifacts show nonzero turnover/costs alongside near-zero return variance; we need explicit invariants to catch any flat-equity-with-trades inconsistencies and enforce cost application.

**Acceptance criteria (objective + falsifiable):**
- New integrity checks assert:
  - final_equity ≈ initial_equity + realized_pnl + unrealized_pnl − total_costs (with tolerance and explicit components).
  - turnover > 0 implies num_trades > 0 (or explicit “desired vs executed” justification).
  - if total_costs > 0 or num_trades > 0 then equity/returns are not exactly constant.
- Runs that violate integrity are flagged invalid (smoke) or fail fast (headline).
- A diagnostic script can reconcile `equity_curve.csv`, `metrics.json`, and `trades.jsonl`.
- Unit tests cover the new invariants using synthetic data (no WRDS required).

**Minimal tests/commands to run:**
- `make test-fast` (or `pytest -q` if no alias)
- `pytest -q tests/test_pnl_integrity.py`

**End-of-ticket (must include these three lines):**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

## ticket-13 — Fix WRDS flagship degeneracy (0 trades) without p-hacking

**Goal (1 sentence):** Ensure walk-forward selection cannot accept zero-trade configurations by enforcing explicit non-degeneracy constraints and surfacing failures clearly.

**Status:** Done (diagnostics complete; root-cause fix tracked under ticket-14).

**Why (ties to diagnosis):**
- `project_state/KNOWN_ISSUES.md` flags the WRDS flagship run as degenerate (zero trades) even after integrity fixes.
- A zero-trade run must not be treated as a valid selection/holdout result.

**Files/modules likely touched:**
- `src/microalpha/config_wfv.py` (non-degenerate config schema)
- `src/microalpha/walkforward.py` (selection filtering + manifest metadata)
- `configs/wfv_flagship_wrds.yaml` (set non-degenerate thresholds)
- `configs/wfv_flagship_wrds_smoke.yaml` (keep smoke consistent)
- `src/microalpha/reporting/summary.py` and/or `src/microalpha/reporting/wrds_summary.py` (surface constraints)
- `tests/test_degeneracy_constraints.py` (new regression test)

**Acceptance criteria (objective + falsifiable):**
- WFV config supports `non_degenerate` thresholds (`min_trades`, optional `min_turnover`).
- Walk-forward selection excludes candidates that fail non-degenerate criteria and records exclusions in `folds.json` plus `manifest.json`.
- If non-degenerate is required and no candidates pass, the run fails with a clear error (no silent degenerate acceptance).
- Unit test proves zero-trade configurations are rejected when non-degeneracy is required (synthetic data only).
- WRDS flagship config includes `non_degenerate: {min_trades: 1}` (or equivalent).

**Minimal tests/commands to run:**
- `make test-fast`
- `pytest -q tests/test_degeneracy_constraints.py`

**Expected artifacts/logs to produce:**
- `docs/agent_runs/<RUN_NAME>/...` (required run log files)
- Updated `manifest.json` / `folds.json` in the affected run artifacts with non-degenerate metadata

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

## ticket-14 — Trace post-signal order pipeline to explain WRDS zero-trade degeneracy (no p-hacking)

**Goal (1 sentence):** Add order-flow diagnostics from signals through fills, explain zero-trade collapses, and fix the first real bug without loosening thresholds.

**Status:** FAIL (review) — WRDS flagship report still had SPA KeyError/degenerate inference and audit hygiene regressions (META git_sha_after recorded as HEAD) that invalidate the headline claim.

**Why (ties to diagnosis):**
- Ticket-13 showed selections exist yet trades remained zero; downstream sizing/caps needed explicit tracing.

**Files/modules likely touched:**
- `src/microalpha/order_flow.py` (new diagnostics payload + summaries)
- `src/microalpha/engine.py` (hook diagnostics into signal/order/fill flow)
- `src/microalpha/portfolio.py` (drop/clip reasons + weight sizing fix)
- `src/microalpha/execution.py` (broker reject reason tracking)
- `src/microalpha/runner.py` / `src/microalpha/walkforward.py` (persist diagnostics, attach to folds/exclusions)
- `tests/test_order_flow_diagnostics.py`, `tests/test_portfolio_risk_caps.py`

**Acceptance criteria (objective + falsifiable):**
- Per-rebalance order-flow diagnostics capture target weights, orders created/dropped, broker accepts/rejects, and fills.
- Single backtest runs emit `order_flow_diagnostics.json` plus manifest summary.
- WFV `folds.json` records `order_flow_diagnostics` for fold tests and candidate exclusions, with `diagnostic_reason` for non-degenerate rejects.
- Weight-based sizing no longer falls back to default qty when target weight rounds to zero; cap breaches clip weight-based orders (counted in diagnostics) instead of dropping.
- Unit tests cover diagnostics population, drop buckets, optional-field safety, and cap clipping.

**Minimal tests/commands to run:**
- `make test-fast`
- `pytest -q tests/test_order_flow_diagnostics.py`

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …

## ticket-15 — Fix SPA KeyError on WRDS flagship + block headline when inference failed

**Goal (1 sentence):** Prevent SPA KeyErrors in WRDS flagship reports and block headline/inference when SPA fails.

**Status:** DONE (reviewed PASS) — SPA KeyError fix verified with report-only rerun and logged evidence.

**Acceptance criteria (objective + falsifiable):**
- SPA bootstrapping loads grid returns without `KeyError` on `artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/`.
- SPA outputs include `spa_status` plus `spa_error` when an exception occurs; degenerate cases report a real reason.
- If `spa_status != ok`, `docs/results_wrds.md` and `reports/summaries/wrds_flagship.md` show an explicit “INFERENCE FAILED” banner and block headline phrasing.
- Regression test covers the missing-panel-id grid scenario and validates schema (spa_status, p_value bounds).
- Report-only rerun updates `reports/summaries/wrds_flagship_spa.json` without `KeyError ... not in index`.

**Minimal tests/commands to run:**
- `make test-fast`
- `pytest -q tests/test_spa_regression_keyerror.py`
- `PYTHONPATH=src:$PYTHONPATH python3 reports/spa.py --grid artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/grid_returns.csv --output-json artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/spa.json --output-md artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/spa.md --bootstrap 2000 --avg-block 63`
- `PYTHONPATH=src:$PYTHONPATH python3 reports/render_wrds_flagship.py artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8 --output reports/summaries/wrds_flagship.md --factors-md artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/factors_ff5_mom.md --docs-results docs/results_wrds.md --docs-image-root docs/img/wrds_flagship --analytics-plots artifacts/plots --metrics-json-out reports/summaries/wrds_flagship_metrics.json --spa-json-out reports/summaries/wrds_flagship_spa.json --spa-md-out reports/summaries/wrds_flagship_spa.md`

**End-of-ticket:**
- **Tests run:** …
- **Artifacts/logs:** …
- **Documentation updates:** …
