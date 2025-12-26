# Changelog

All notable changes to this project will be documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com) and the project adheres to [Semantic Versioning](https://semver.org).

## [Unreleased]
### Added
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

### Changed
- Walk-forward WRDS config aligned to universe coverage (2012–2024) and report pipeline now emits WRDS signals before analytics.
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
- ticket-04: engine rejects signals with timestamps that do not match the current market event.
