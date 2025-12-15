# Changelog (summarised)

> This file summarises notable milestones; see root `CHANGELOG.md` for the authoritative log.

## 2025-12-15
- Added `project_state/` knowledge spine documenting architecture, modules, pipelines, configs, and current results.

## 2025-11-22
- Introduced `configs/wfv_flagship_wrds_smoke.yaml` for faster WRDS sanity runs; partial smoke run completed (2015–2019 window). Full rerun with tightened risk caps still pending.

## 2025-11-21
- Tightened WRDS flagship risk spec (gross 1.25x, DD halt 20%, turnover cap 180MM, ADV floor 50MM, price floor 12, sector cap 8) and documented in `docs/results_wrds.md`. Plan step S1 completed; S2 (drawdown reduction validation) opened.

## 2025-11-12
- Hardened WRDS exporter, SPA/FF5+MOM reporting, analytics plots; WRDS flagship run `2025-11-21T00-28-22Z-54912a8` published with docs assets and SPA/factor summaries. Added WRDS detection helpers and Makefile wiring for WRDS pipelines.

## 2025-10-30
- Generated deterministic sample artifacts (`artifacts/sample_flagship/...`, `artifacts/sample_wfv/...`) powering README and tests; README updated with sample metrics and factor regression table.

## Earlier (Unreleased section in root changelog)
- Added repository guardrails (pytest markers, ruff/mypy, detect‑secrets), WRDS export manifest, analytics/reporting enhancements, and CI/docs placeholders.
