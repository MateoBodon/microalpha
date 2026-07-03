# Changelog

All notable changes to this project will be documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com) and the project adheres to [Semantic Versioning](https://semver.org).

## [Unreleased]
### Added
- Agentic System Kit v2 tracking policy (`TRACKING_POLICY.md`) plus helper scripts (`runlog_init.py`, `ticket_new.py`, `validate_runlog.py`).
- Repository guardrails: pytest marker config, WRDS detection helpers, log fan-out to `artifacts/logs/`.
- Pre-commit automation (black, isort, ruff, detect-secrets) plus tightened `.gitignore`.
- WRDS-focused Makefile targets, CHANGELOG bootstrap, and CI/docs placeholders for analytics & reporting.
- Hardened WRDS exporter (dlret merge, Parquet partitions, metadata, manifests) and signal-builder CLI for analytics.
- Dedicated WRDS summary renderer + docs integration, Hansen SPA/FF factors wiring, and regression tests for summaries/markers.
- Daily FF5+MOM factor bundle from Ken French data plus WRDS image assets under `docs/img/wrds_flagship/`.
- ticket-01: WRDS smoke Makefile targets and smoke report outputs.
- ticket-11: data policy checker script + allowlist, Make target, and pytest enforcement.
- ticket-12: PnL integrity checks with `integrity.json`, diagnostic script, and `run_mode` support for smoke/dev runs.
- ticket-12: `make test-fast` alias for a fast deterministic pytest run.
- ticket-12: WRDS_DATA_ROOT local-doc fallback (reads `docs/local/WRDS_DATA_ROOT.md` when env var is unset).
- ticket-04: explicit unsafe execution opt-in with manifest flags (`unsafe_execution`, `unsafe_reasons`, `execution_alignment`) and report banners.
- ticket-04: red-team leakage tests for future-dated signals and unsafe execution configs.
- ticket-13: non-degenerate WFV selection constraints (min_trades/min_turnover) with manifest/report surfacing and WRDS configs updated.
- ticket-13: flagship momentum filter diagnostics added to WFV grid exclusions/folds for per-rebalance coverage counts.
- ticket-14: order-flow diagnostics capturing post-signal sizing/orders/broker/fills with per-rebalance payloads and WFV fold attachments.
- ticket-16: run-log validator script + `make validate-runlogs` target to enforce META.json integrity.
- ticket-05: deterministic runs index registry builder, Make target, and run registry documentation.
- ticket-17: baseline suite computation with `baselines.csv`/status plus baseline comparison table + overlay plot in summary reports.
- ticket-18: agentic system scaffold (PROJECT.md, agentic tools, and run-log templates).
- ticket-22: WRDS resume metrics summary (`docs/results_wrds_resume.md`) for run `2026-01-25T21-01-51Z-4d08d18`.
- ticket-23: holdout order-flow + filter diagnostics and a hard guardrail for zero-trade holdout runs.
- ticket-28: WRDS dataset_id provenance recorded in manifests + run logs, with canonical export documented in `docs/wrds.md`.
- ticket-31: best-model WRDS resume metrics snippet + JSON extracted from SPA/holdout outputs for run `2026-01-27T04-47-22Z-31fe553`.
- ticket-32: single-window WRDS resume snippet with explicit holdout-only labeling (`resume_line_holdout.md`) for run `2026-01-27T04-47-22Z-31fe553`.
- ticket-33: WRDS real-data leaderboard artifacts (`leaderboard.csv`, `leaderboard.md`) and best-line snippet (`resume_line_best.md`) with explicit holdout window and run_id/dataset_id provenance.
- ticket-34: shipped ticket-33 leaderboard deliverables (script + artifacts + prompt/run logs) so they are reviewable in `DIFF.patch`.
- ticket-35: WRDS micro-sweep config `configs/wfv_flagship_wrds_sweep35.yaml` and promoted resume-safe artifact set for run `2026-02-16T22-33-46Z-8d90621` (`metrics.json`, `manifest_excerpt.json`, `snippet.md`).


### Changed
- Refreshed agentic tooling and .gitignore scaffold via tools-only bootstrap.
- Walk-forward WRDS config aligned to available universe coverage (2013–2019) to restore non-degenerate holdout metrics.
- WRDS flagship run now uses 3y/9m folds (21 folds), trimmed grid (top_frac × turnover only), higher turnover cap, and produces reproducible signals/analytics/factors/SPA assets for run `2025-11-12T18-50-58Z-b2eaf50` with docs, plots, and summaries updated in lockstep.
- ticket-01: WRDS configs now surface gross leverage/single-name caps and borrow model; reporting now includes net/gross exposure + cost breakdown.
- WRDS smoke report tolerates zero SPA comparator t-stats (smoke-only) to keep validation runs unblocked.
- WRDS summary now reports the actual docs image root used for the run.
- ticket-08: reporting now skips invalid SPA inputs with explicit reasons and flags degenerate runs (zero trades/flat returns).
- ticket-01: WRDS summary now auto-generates degenerate SPA outputs when SPA artifacts are missing/invalid and validates SPA p-value bounds so reports never crash on SPA inputs.
- ticket-12: equity snapshots refresh after same-day fills, and reports now display an invalid-run banner when integrity checks fail.
- ticket-06: gpt-bundle now refuses dirty worktrees to keep bundles commit-consistent.
- ticket-06: stop ignoring `project_state/` and `docs/agent_runs/` so audit artifacts are tracked.
- ticket-06: gpt-bundle honors `BUNDLE_TIMESTAMP` for deterministic bundle paths.
- ticket-02: Walk-forward runs now support explicit holdout ranges with separate holdout artifacts, selection summaries, and OOS returns; WRDS/sample configs updated for holdout evaluation.
- ticket-07: gpt-bundle now records commit ranges and verifies DIFF.patch against bundled files; holdout test now proves selection excludes holdout data.
- ticket-09: gpt-bundle now validates META.json ticket ids against sprint tickets before bundling.
- ticket-03: factor regression now enforces index alignment, requires explicit resampling for frequency mismatches, and reports frequency + sample size metadata (CLI includes resample flags).
- ticket-04: engine rejects signals with timestamps that do not match the current market event.
- ticket-14: weight-based sizing no longer falls back to default qty when weight rounds to zero; cap breaches clip weight-based orders instead of dropping, and diagnostics track clip counts.
- ticket-15: SPA grid-returns loading reindexed to avoid KeyErrors; SPA outputs now include `spa_status`/`spa_error`, and WRDS summaries gate headline language when SPA fails.
- gpt-bundle: allow optional `git_sha_after_ref` in META.json to derive diff ranges while keeping concrete git SHA metadata.
- ticket-26: gpt-bundle now stashes/restores dirty worktrees when bundling and includes a dirty-tree pytest guard.
- test-fast now includes run-log validation before pytest.
- Cost sensitivity note now clarifies borrow costs are logged separately and not scaled.
- ticket-19: cleaned scaffold residue and tracked agentic run logs + project_state indices.
- ticket-19a: pandas 3 compatibility fixes for multi-asset timestamps and analytics timestamp filling.
- ticket-19a: refreshed project_state indices, validated scaffold state, and recorded commit/run logs.
- ticket-24c: shipped WRDS refresh outputs so resume metrics/docs/report images reference run `2026-01-26T01-22-23Z-e76eb4d`.
- ticket-24d: finalized WRDS refresh audit docs/run logs and bundle for run `2026-01-26T01-22-23Z-e76eb4d`.
- ticket-28: pinned WRDS export metadata in `configs/wfv_flagship_wrds.yaml` and generated resume artifacts under `docs/artifacts/resume/wrds/<RUN_ID>/`.
- ticket-34: repaired `docs/agent_runs/20260216_025221_ticket-ticket-32b/META.json` to satisfy run-log schema validation and updated data-policy allowlist for license-safe resume aggregates so `make test-fast` passes.
- ticket-35: refreshed WRDS leaderboard outputs with a new best eligible holdout row (`run_id=2026-02-16T22-33-46Z-8d90621`, Sharpe_HAC `0.588`) and generalized data-policy allowlist globs for resume aggregate JSON files.
- ticket-36: shipped ticket-35 deliverables into tracked state, added ticket-36 shipping run logs/prompt capture, and corrected `project_state/CURRENT_RESULTS.md` header metadata for current branch/SHA consistency.
