# Results

- Added holdout diagnostics (order-flow + filter diagnostics) and a hard guardrail for zero-trade holdout runs in `src/microalpha/walkforward.py`.
- Added a regression test to ensure zero-trade holdout runs fail fast (`tests/test_walkforward.py`).
- Shifted WRDS flagship WFV/holdout windows to match available WRDS universe coverage (2013-01-02 → 2019-12-31).
- WRDS WFV + report rerun completed: `artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18/` (holdout trades: 26; non-degenerate).
- Updated resume summary with new holdout metrics in `docs/results_wrds_resume.md`.
- Refreshed project_state indices and rebuilt project_state docs (`project_state/_generated`, `project_state/CURRENT_RESULTS.md`).
- Project state bundle generated at `docs/_bundles/project_state_20260125_232239.zip`.
- Added ticket-23 entry in `docs/CODEX_SPRINT_TICKETS.md` and created ticket spec in `docs/tickets/`.
- GPT bundle generated at `docs/_bundles/gpt_bundle_20260125_232413_ticket-23_wrds_holdout_nonzero_trades.zip`.
