# Ticket 31 — WRDS best-model resume line from SPA outputs

## Goal
Produce the best-model WRDS resume line by extracting holdout metrics from existing SPA/grid outputs (no rerun).

## Scope
- Use existing artifacts from run `2026-01-27T04-47-22Z-31fe553`.
- Confirm SPA best-model id matches holdout selection.
- Write resume artifacts under `docs/artifacts/resume/wrds/<RUN_ID>/`:
  - `best_model_metrics.json`
  - `best_model_snippet.md`
- Record extraction steps in a new run log.

## Acceptance Criteria
- New run log under `docs/agent_runs/<RUN_NAME>/` with required files.
- New artifacts under `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/`:
  - `best_model_metrics.json` (best config id + Sharpe/MaxDD/MAR/turnover + SPA/RC p-values + dataset_id)
  - `best_model_snippet.md` (resume line)
- No bulky files committed; parsing scratch stays in `artifacts/_local/<RUN_NAME>/` or `reports/_runs/<RUN_NAME>/`.

## Notes
- Do not re-run WFV or SPA; extract from existing outputs only.
