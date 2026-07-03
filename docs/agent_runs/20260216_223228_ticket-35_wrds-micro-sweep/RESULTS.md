# Results

## Pre-registered sweep contract (fixed before execution)

- Holdout window fixed: `2018-01-02` to `2019-12-31`
- Winner rule fixed before running WFV:
  - Primary objective: maximize holdout `Sharpe_HAC`
  - Guardrails: holdout trades `>= 20`, holdout max drawdown `<= 15%`
  - Tie-breakers: lower holdout MaxDD, then higher holdout MAR
- Sweep knobs fixed with cap check:
  - `lookback_months`: `[9, 12, 18]`
  - `top_frac`: `[0.15, 0.20, 0.25]`
  - `skip_months`: `[1]`
  - `allocator_kwargs`: `[{risk_model: "risk_parity"}]`
  - Total combinations: `3 x 3 x 1 x 1 = 9` (`<=12` cap)

## Summary

- Added pre-registered sweep config: `configs/wfv_flagship_wrds_sweep35.yaml`.
- Executed WRDS WFV sweep locally and produced run:
  - `run_id=2026-02-16T22-33-46Z-8d90621`
  - `dataset_id=wrds_crsp_export_20251221_v1`
  - local artifacts: `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621/`
- Generated local report:
  - `reports/_runs/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship.md`
- Promoted tracked resume-safe artifacts:
  - `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/metrics.json`
  - `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/manifest_excerpt.json`
  - `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/snippet.md`
- Refreshed leaderboard outputs from artifact scan:
  - `docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
  - `docs/artifacts/resume/wrds/leaderboard/leaderboard.md`
  - `docs/artifacts/resume/wrds/leaderboard/resume_line_best.md`
- Validation gates:
  - `make check-data-policy`: pass
  - `make test-fast`: pass (`128 passed, 1 skipped`)

## Winner outcome under pre-registered rule

- New best eligible run: `2026-02-16T22-33-46Z-8d90621`
- Holdout metrics used for selection:
  - Sharpe_HAC: `0.5876`
  - MaxDD: `1.38%`
  - MAR: `0.6376`
  - Trades: `31`
  - RealityCheck p-value: `0.941`
  - SPA p-value: `n/a` (`spa.json` not emitted for this run)
- Prior best eligible run (`2026-01-27T04-47-22Z-31fe553`) remains in leaderboard as rank 2.

## Key outputs

- Sweep config: `configs/wfv_flagship_wrds_sweep35.yaml`
- Run log: `docs/agent_runs/20260216_223228_ticket-35_wrds-micro-sweep/`
- Prompt capture: `docs/prompts/20260216_223228_ticket-35_wrds-micro-sweep.md`
- Resume-safe artifact: `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/`
- Leaderboard artifacts: `docs/artifacts/resume/wrds/leaderboard/`
- Updated pointers: `project_state/CURRENT_RESULTS.md`, `PROGRESS.md`

## Notes

- Bulky WRDS outputs were kept local-only under `artifacts/_local/...` and `reports/_runs/...`.
- Only license-safe aggregates/snippets were committed under `docs/artifacts/resume/wrds/...`.
