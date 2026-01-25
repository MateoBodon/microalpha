# ticket-22_wrds_resume_metrics

## Goal
Produce up-to-date, resume-credible real-data (WRDS/CRSP) holdout metrics and a clean summary artifact (no licensed data) so the resume bullet can be updated confidently.

## Scope
- Use existing WRDS pipeline + configs (no strategy logic refactors).
- Run a single locked WRDS holdout WFV + report using `/srv/data/wrds`.
- Commit only license-safe artifacts (run logs + summary doc + optional resume snippet).

## Acceptance Criteria
- New run log under `docs/agent_runs/<RUN_NAME>/` with required files and recorded artifact/report paths.
- Summary doc (`docs/results_wrds_resume.md` or updated `docs/results_wrds.md`) includes run_id, headline metrics (Sharpe_HAC, MaxDD, CAGR if available, turnover, RealityCheck p, SPA p/status), and notes net-of-costs, universe, and date range.
- `make test-fast`, `make check-data-policy`, and `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds make report-wrds` succeed.
- No licensed/raw WRDS data added to git.

## Plan
1. Record prompt + create run log scaffold in `docs/agent_runs/<RUN_NAME>/` and `docs/prompts/`.
2. Run WRDS holdout WFV + report (`make wfv-wrds`, `make report-wrds`) with `WRDS_DATA_ROOT=/srv/data/wrds`.
3. Extract headline metrics from artifacts and write `docs/results_wrds_resume.md` (plus optional resume snippet).
4. Run `make test-fast` and `make check-data-policy`; capture outputs in run log.
5. Update `PROGRESS.md` (and `docs/DECISIONS.md` if any non-obvious choices).
6. Generate `gpt_bundle.zip` for the ticket.

## Notes
- Holdout dates are defined in `configs/wfv_flagship_wrds.yaml`.
- Do not commit raw WRDS exports or per-bar outputs.
