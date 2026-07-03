# Results

## Pre-registered selection rule (set before running selection)

This rule was fixed before running `scripts/wrds_leaderboard.py`:

- Primary objective: maximize holdout `sharpe_hac`.
- Guardrails:
  - `dataset_id` must be present.
  - holdout `trades >= 20`.
  - holdout `maxdd_pct <= 15.0`.
- Tie-breakers (in order):
  - lower holdout `maxdd_pct`
  - higher holdout `mar`
  - stable lexical order of artifact path

## Summary
- Added deterministic scanner script: `scripts/wrds_leaderboard.py`.
- Built WRDS real-data leaderboard from existing artifact roots:
  - `artifacts/wrds_flagship/*/metrics.json`
  - `artifacts/_local/**/wrds_flagship/*/metrics.json`
- Produced tracked artifacts:
  - `docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
  - `docs/artifacts/resume/wrds/leaderboard/leaderboard.md`
  - `docs/artifacts/resume/wrds/leaderboard/resume_line_best.md`
- Scanner found 11 candidate runs and selected one best eligible row under the pre-registered rule:
  - `run_id=2026-01-27T04-47-22Z-31fe553`
  - `dataset_id=wrds_crsp_export_20251221_v1`
  - window label: `holdout-only` (`2018-01-02` to `2019-12-31`)
  - headline metrics: Sharpe_HAC `0.140`, CAGR `0.31%`, MaxDD `3.49%`, MAR `0.09`, turnover `$5.22MM`, trades `26`
- Updated pointers in `project_state/CURRENT_RESULTS.md` and living docs (`PROGRESS.md`, `CHANGELOG.md`, `docs/CODEX_SPRINT_TICKETS.md`, `project_state/KNOWN_ISSUES.md`).

## Key outputs
- Scanner script: `scripts/wrds_leaderboard.py`
- Leaderboard CSV: `docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
- Leaderboard MD: `docs/artifacts/resume/wrds/leaderboard/leaderboard.md`
- Best resume line: `docs/artifacts/resume/wrds/leaderboard/resume_line_best.md`
- Source prompt capture: `docs/prompts/20260216_033516_ticket-33_wrds-realdata-leaderboard.md`

## Notes
- Provenance policy applied: rows missing `dataset_id` remain visible in leaderboard but are excluded from best-line eligibility.
- No heavy WRDS rerun was performed; this ticket is artifact extraction/normalization only.
- `make test-fast` fails due pre-existing run-log schema errors in `docs/agent_runs/20260216_025221_ticket-ticket-32b/META.json`; ticket-33 run-log validation passes.
