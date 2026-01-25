<!--
generated_at: 2026-01-25T23:23:20Z
git_sha: 4d08d18202a411cd831efce739cd5cb37e6deb1e
branch: codex/ticket-22-wrds-resume-metrics
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Pipeline Flow

## Primary entrypoints

- `microalpha run --config <cfg> --out <dir>` (single backtest)
- `microalpha wfv --config <cfg> --out <dir>` (walk-forward)
- `microalpha report --artifact-dir <dir>` (summaries + plots)
- Wrappers: `run.py` and `walk_forward.py`

## Makefile targets

- `check-data-policy`
- `clean`
- `dev`
- `docs`
- `export-wrds`
- `gpt-bundle`
- `report`
- `report-wfv`
- `report-wrds`
- `report-wrds-smoke`
- `runs-index`
- `sample`
- `test`
- `test-fast`
- `test-wrds`
- `validate-runlogs`
- `wfv`
- `wfv-wrds`
- `wfv-wrds-smoke`
- `wrds`
- `wrds-flagship`

## Typical flows

### Sample flagship

```
make sample
make report
```

### Sample walk-forward

```
make wfv
make report-wfv
```

### WRDS (guarded)

```
WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds
WRDS_DATA_ROOT=/path/to/wrds make report-wrds
```

## Report pipeline

- `microalpha report` calls `src/microalpha/reporting/summary.py` and `tearsheet.py`.
- WRDS reporting chains through `reports/analytics.py`, `reports/factors.py`, `reports/spa.py`, `reports/render_wrds_flagship.py` (see Makefile).
