# Results

- Fixed same-day fill equity snapshots by refreshing after fills and collapsing per-timestamp entries so trades/costs can’t leave a flat equity curve at run end.
- Added PnL integrity checks (equity reconciliation, turnover/trade consistency, constant-equity guard) with `integrity.json` and manifest `run_invalid`; reports now surface invalid runs prominently.
- Added `scripts/diagnose_artifact_integrity.py`, `run_mode` config (smoke/dev), `make test-fast`, and regression tests for integrity.
- Cleaned `docs/CODEX_SPRINT_TICKETS.md` to a single list and added ticket-12; updated `PROGRESS.md`, `project_state/KNOWN_ISSUES.md`, and `CHANGELOG.md`.
- Added a safe WRDS_DATA_ROOT fallback that reads `docs/local/WRDS_DATA_ROOT.md` when the env var is unset (local-only).

Evidence / artifacts:
- Sample WFV run: `artifacts/sample_wfv/2025-12-23T18-39-59Z-82c14dc/` (includes `integrity.json`)
- Sample WFV report: `reports/summaries/flagship_mom_wfv.md`
- WRDS smoke run: `artifacts/wrds_flagship_smoke/2025-12-23T19-19-16Z-809607a/` (includes `integrity.json`)
- WRDS smoke report: `reports/summaries/wrds_flagship_smoke.md` (updates `docs/results_wrds_smoke.md`)
- WRDS flagship run: `artifacts/wrds_flagship/2025-12-23T19-40-24Z-ff2979d/` (includes `integrity.json`, zero-trade/flat-equity)
- WRDS flagship report: `reports/summaries/wrds_flagship.md` (updates `docs/results_wrds.md`)
- Bundle: `docs/gpt_bundles/2025-12-23T20-05-00Z_ticket-12_20251223_080000_ticket-12_fix-wrds-pnl-integrity.zip`

WRDS note:
- `WRDS_DATA_ROOT` is now documented in `docs/local/WRDS_DATA_ROOT.md` (local-only); WRDS smoke + flagship reruns executed using `$WRDS_DATA_ROOT`.
- Integrity diagnostics (`scripts/diagnose_artifact_integrity.py`) show: WRDS smoke has non-constant equity with trades/costs and integrity checks OK; WRDS flagship remains flat/zero-trade (integrity OK but degenerate).

## Human merge checklist
- Feature branch only; no main commits
- Tests pass; commands logged
- No raw WRDS data committed; no absolute local paths in docs
- Run log schema matches `docs/DOCS_AND_LOGGING_SYSTEM.md`
- Ticket file cleaned/deduped; ticket-12 added with acceptance criteria
