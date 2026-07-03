Filename: docs/tickets/TICKET-31_wrds_best-real-data-resume-line_from_spa.md
Goal: Produce the best defensible WRDS resume line by extracting the best model’s holdout metrics from the existing spa.json/grid_returns.csv outputs (and reporting them alongside SPA/RealityCheck), without re-running the full backtest.
Acceptance criteria:

A new run log under docs/agent_runs/<RUN_NAME>/ documenting extraction steps/commands.

A new tracked artifact under docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/ (or a new run_id folder if regenerated) containing:

best_model_metrics.json (best config id + Sharpe/MaxDD/MAR/turnover + SPA/RC p-values + dataset_id)

best_model_snippet.md (copy-paste resume line)

No bulky files committed; any parsing scratch stays in artifacts/_local/<RUN_NAME>/ or reports/_runs/<RUN_NAME>/.
