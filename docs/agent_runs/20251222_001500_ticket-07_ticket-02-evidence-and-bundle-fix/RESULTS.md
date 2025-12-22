Summary:
- Added a holdout-isolation test that contrasts selection with and without a holdout window using a deterministic toy series.
- Hardened gpt-bundle to record commit ranges (COMMITS.txt) and verify DIFF.patch reproduces bundled PROGRESS/run-log files; verification now applies per-file patches.
- Note: initial gpt-bundle verification failed due to include-filter mismatch; fixed by applying per-file diffs.
- Updated progress and sprint docs to reflect ticket-02 review failure and ticket-07 scope; refreshed sample holdout run entry.

Code/doc changes:
- `tests/test_walkforward.py` (holdout isolation test now compares holdout vs no-holdout selection)
- `tools/gpt_bundle.py` (deterministic diff range + COMMITS.txt + patch verification)
- `PROGRESS.md`, `docs/CODEX_SPRINT_TICKETS.md`, `project_state/CURRENT_RESULTS.md`, `CHANGELOG.md`

Artifacts (sample holdout run):
- Run dir: `artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/`
- OOS returns: `artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/oos_returns.csv`
- Holdout metrics: `artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/holdout_metrics.json`

WRDS holdout smoke:
- SKIPPED (blocked: WRDS_DATA_ROOT not set)

Bundle:
- `docs/gpt_bundles/2025-12-22T00-52-52Z_ticket-07_20251222_001500_ticket-07_ticket-02-evidence-and-bundle-fix.zip`
