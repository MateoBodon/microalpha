# Prompt

Source prompt captured at:
- `docs/prompts/20260216_033516_ticket-33_wrds-realdata-leaderboard.md`

## Ticket
- Ticket: `ticket-33`
- Run name: `20260216_033516_ticket-33_wrds-realdata-leaderboard`
- Summary: Build WRDS leaderboard and pick best resume line from existing artifacts.

## Verbatim task summary
Identify the best currently available WRDS real-data resume metrics from existing artifacts (no heavy reruns), produce a tracked leaderboard (`leaderboard.csv` + `leaderboard.md`), publish a tracked best resume line (`resume_line_best.md`) with explicit window label plus `run_id` and `dataset_id`, and update `project_state/CURRENT_RESULTS.md` to point to those artifacts.

Required scan roots:
- `artifacts/wrds_flagship/**/metrics.json`
- `artifacts/_local/**/wrds_flagship/**/metrics.json`

Pre-registered best rule required in run log before selection:
- Primary: maximize holdout Sharpe_HAC
- Guardrails: trades >= 20, maxdd_pct <= 15%, dataset_id present
- Tie-breakers: lower MaxDD, higher MAR

Required tests:
- `python3 tools/agentic/validate_runlog.py --run-name <RUN_NAME>`
- `python3 scripts/wrds_leaderboard.py --help`
- `python3 scripts/wrds_leaderboard.py --out docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
- `make test-fast` (or documented justification/blocker)
