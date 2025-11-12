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

### Changed
- Walk-forward WRDS config aligned to universe coverage (2012–2024) and report pipeline now emits WRDS signals before analytics.
- WRDS flagship run now uses 3y/9m folds (21 folds), trimmed grid (top_frac × turnover only), higher turnover cap, and produces tearsheet/SPAs/factors for run `2025-11-12T08-51-11Z-65187e4` with docs populated accordingly.
