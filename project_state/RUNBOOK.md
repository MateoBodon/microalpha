# Runbook

## Setup
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e '.[dev]'`
- Optional: `make dev` (same as the editable install)

## Build
- `mkdocs build` (or `make docs`)

## Test
- `make test-fast` (run-log validation + `pytest -q`)
- `pytest -q` (full suite)
- `make test-wrds` (requires local WRDS exports)
- `make check-data-policy` (guardrails against licensed data)

## Run (sample/public)
- `make sample && make report` (single run + summary)
- `make wfv && make report-wfv` (walk-forward + summary)
- `microalpha wfv --config configs/wfv_flagship_public.yaml --out artifacts/public_wfv`
- `microalpha report --artifact-dir artifacts/public_wfv/<RUN_ID>`

## Run (WRDS, local only)
- `WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds && make report-wrds`
- Smoke: `WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds-smoke && make report-wrds-smoke`
- Combined: `WRDS_DATA_ROOT=/path/to/wrds make wrds-flagship`

## Results live here
- Artifacts: `artifacts/<run_id>/` (manifest, metrics, trades, plots)
- Reports: `reports/summaries/` (Markdown summaries)
- WRDS summaries: `docs/results_wrds*.md`
- Run logs: `docs/agent_runs/<RUN_NAME>/`

## Debug
- `microalpha info` (env + package metadata)
- Inspect `artifacts/<run_id>/manifest.json` for config + invariants
- `python3 scripts/validate_run_logs.py` to validate run logs
