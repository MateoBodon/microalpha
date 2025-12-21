<!--
generated_at: 2025-12-21T21:29:21Z
git_sha: 33c9c2a0bab056c4296a66ee652af49cc646f7df
branch: feat/ticket-02-holdout-wfv
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Changelog (repo root)

Source: `CHANGELOG.md`.

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

### Changed
- Walk-forward WRDS config aligned to universe coverage (2012–2024) and report pipeline now emits WRDS signals before analytics.
- WRDS flagship run now uses 3y/9m folds (21 folds), trimmed grid (top_frac × turnover only), higher turnover cap, and produces reproducible signals/analytics/factors/SPA assets for run `2025-11-12T18-50-58Z-b2eaf50` with docs, plots, and summaries updated in lockstep.
- ticket-01: WRDS configs now surface gross leverage/single-name caps and borrow model; reporting now includes net/gross exposure + cost breakdown.
- WRDS smoke report tolerates zero SPA comparator t-stats (smoke-only) to keep validation runs unblocked.
- WRDS summary now reports the actual docs image root used for the run.
- ticket-06: gpt-bundle now refuses dirty worktrees to keep bundles commit-consistent.
- ticket-06: stop ignoring `project_state/` and `docs/agent_runs/` so audit artifacts are tracked.
- ticket-06: gpt-bundle honors `BUNDLE_TIMESTAMP` for deterministic bundle paths.
- ticket-02: Walk-forward runs now support explicit holdout ranges with separate holdout artifacts, selection summaries, and OOS returns; WRDS/sample configs updated for holdout evaluation.
