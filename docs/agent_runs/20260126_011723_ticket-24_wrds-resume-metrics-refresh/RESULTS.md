# Results

## Summary
- Reran WRDS flagship WFV + report with `WRDS_DATA_ROOT=/srv/data/wrds/wrds` and captured new artifacts under `artifacts/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d/`.
- Refreshed resume-facing metrics in `docs/results_wrds_resume.md` and updated `project_state/CURRENT_RESULTS.md` to the new run id.
- Generated a new project_state bundle: `docs/_bundles/project_state_20260126_013606.zip`.

## Notes
- Initial attempt with `WRDS_DATA_ROOT=/srv/data/wrds` failed because the universe file lives under `/srv/data/wrds/wrds/universes/`; reran with the nested root.
- `make test-fast` required `.venv/bin/pytest` (system `pytest` missing).

## Commands + environment
- `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make wrds-flagship`
- `WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make report-wrds`
- `make test-fast`
- `make check-data-policy`
- `make validate-runlogs`
- `python3 tools/agentic/project_state_refresh.py --zip`

## Metrics comparison (previous vs new)

Previous run: `2026-01-25T22-58-24Z-4d08d18`
New run: `2026-01-26T01-22-23Z-e76eb4d`

| Metric | Previous | New |
| --- | ---: | ---: |
| Holdout Sharpe_HAC (lags=10) | 0.140 | 0.140 |
| Holdout Max Drawdown | 3.49% | 3.49% |
| Holdout CAGR | 0.307% | 0.307% |
| Holdout Turnover | $5.22MM | $5.22MM |
| Holdout Trades | 26 | 26 |
| WFV Sharpe_HAC (lags=10) | 0.272 | 0.272 |
| WFV Max Drawdown | 3.41% | 3.41% |
| WFV CAGR | 0.718% | 0.718% |
| WFV Turnover | $14.75MM | $14.75MM |
| WFV Trades | 64 | 64 |

## Artifacts and reports
- Artifacts: `artifacts/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d/`
- Reports: `reports/summaries/wrds_flagship.md`, `reports/summaries/wrds_flagship_metrics.json`, `reports/summaries/wrds_flagship_spa.json`, `reports/summaries/wrds_flagship_spa.md`, `reports/summaries/wrds_flagship_factors.md`
- GPT bundle: `docs/_bundles/gpt_bundle_20260126_014244_TICKET-24_wrds-resume-metrics-refresh.zip`

## Tests
- `make test-fast` (via `.venv/bin/pytest`)
- `make check-data-policy`
- `make validate-runlogs`
