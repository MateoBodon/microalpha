# ticket-23_wrds_holdout_nonzero_trades

## Goal
Fix WRDS final-holdout degeneracy (zero trades) and produce resume-credible real-data holdout metrics with a committed run log + summary doc.

## Scope
- Diagnose where holdout trades disappear (data coverage, universe filters, sizing/risk caps, execution).
- Add minimal diagnostics plus a hard guardrail for holdout `num_trades == 0`.
- Adjust only what is necessary (no strategy redesign) to get nonzero trades.
- Rerun WRDS holdout WFV + report; commit only license-safe artifacts.

## Acceptance Criteria
- WRDS final-holdout run produces `num_trades > 0` and non-NaN Sharpe/CAGR/MaxDD.
- `docs/results_wrds_resume.md` includes run_id, date range, universe, net-of-costs note, and headline metrics.
- Run log exists at `docs/agent_runs/<RUN_NAME>/` with required files and recorded artifact/report paths.
- `make test-fast`, `make check-data-policy`, `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make wfv-wrds`, and `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make report-wrds` succeed.
- WRDS_DATA_ROOT handling is consistent and documented (auto-detect or `/srv/data/wrds/wrds`).

## Plan
1. Capture run prompt + create run log scaffold (`docs/prompts/`, `docs/agent_runs/<RUN_NAME>/`).
2. Diagnose WRDS holdout coverage vs config windows; add holdout diagnostics + zero-trade guardrail in `src/microalpha/walkforward.py`.
3. Adjust WRDS flagship config date windows to match available WRDS coverage (`configs/wfv_flagship_wrds.yaml`).
4. Run WRDS WFV + report and extract metrics into `docs/results_wrds_resume.md`.
5. Run tests (`make test-fast`, `make check-data-policy`) and record outputs in the run log.
6. Update living docs (`PROGRESS.md`, `CHANGELOG.md`, `project_state/KNOWN_ISSUES.md`, `docs/DECISIONS.md` if needed).
7. Generate `gpt_bundle.zip` for the ticket.

## Notes
- Do not commit raw WRDS exports; only commit run logs and summary docs.
- Use `$WRDS_DATA_ROOT` in docs unless a fixed path is required for reproducibility.
