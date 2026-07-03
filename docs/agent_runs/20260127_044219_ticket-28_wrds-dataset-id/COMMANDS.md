# Commands

Log commands that materially change state or produce results.

- 2026-01-27T04:42:28Z `python3 tools/agentic/runlog_init.py --run-name "20260127_044219_ticket-28_wrds-dataset-id" --ticket "ticket-28" --summary "Pin WRDS dataset_id + refresh WRDS flagship metrics"`
  - Created `docs/agent_runs/20260127_044219_ticket-28_wrds-dataset-id/`.
- 2026-01-27T04:42:31Z `cp docs/prompts/20260127_044219_ticket-28_wrds-dataset-id_ticket-28_wrds-dataset-id.md docs/agent_runs/20260127_044219_ticket-28_wrds-dataset-id/PROMPT.md`
- 2026-01-27T04:43:02Z `mkdir -p artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship reports/_runs/20260127_044219_ticket-28_wrds-dataset-id`
- 2026-01-27T04:43:15Z `WRDS_DATA_ROOT=/srv/data/wrds/wrds WRDS_DATASET_ID=wrds_crsp_export_20251221_v1 PYTHONPATH=src python -m microalpha.cli wfv --config configs/wfv_flagship_wrds.yaml --out artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship`
  - Failed: `ModuleNotFoundError: No module named 'numpy'` (venv not active).
- 2026-01-27T04:44:12Z `source .venv/bin/activate && WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds WRDS_DATASET_ID=wrds_crsp_export_20251221_v1 PYTHONPATH=src python -m microalpha.cli wfv --config configs/wfv_flagship_wrds.yaml --out artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship`
  - Success; run_id `2026-01-27T04-47-22Z-31fe553` written under `artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/` (stdout manifest JSON emitted).
- 2026-01-27T06:00:45Z `source .venv/bin/activate && WRDS_DATA_ROOT=/srv/data/wrds/wrds PYTHONPATH=src python3 scripts/build_wrds_signals.py --output artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/signals.csv --lookback-months 12 --skip-months 1 --min-adv 30000000`
- 2026-01-27T06:01:05Z `source .venv/bin/activate && PYTHONPATH=src python3 reports/analytics.py artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553 --factors data/factors/ff5_mom_daily.csv --plots-dir artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/analytics/plots --analytics-dir artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/analytics/csv`
- 2026-01-27T06:01:15Z `source .venv/bin/activate && PYTHONPATH=src python3 reports/factors.py artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553 --factors data/factors/ff5_mom_daily.csv --model ff5_mom --hac-lags 5 --output artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/factors_ff5_mom.md`
  - Printed factor table to stdout.
- 2026-01-27T06:01:24Z `source .venv/bin/activate && PYTHONPATH=src python3 reports/tearsheet.py artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/equity_curve.csv --bootstrap artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/bootstrap.json --metrics artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/metrics.json --output artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/equity_curve.png --bootstrap-output artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/bootstrap_hist.png --title "WRDS Flagship Walk-Forward"`
  - Warning: matplotlib `tight_layout` compatibility note.
- 2026-01-27T06:01:34Z `source .venv/bin/activate && PYTHONPATH=src python3 reports/spa.py --grid artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/grid_returns.csv --output-json artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/spa.json --output-md artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/spa.md --bootstrap 2000 --avg-block 63`
- 2026-01-27T06:01:50Z `source .venv/bin/activate && PYTHONPATH=src python3 reports/render_wrds_flagship.py artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553 --output reports/_runs/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship.md --factors-md artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/factors_ff5_mom.md --analytics-plots artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/analytics/plots --metrics-json-out reports/_runs/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship_metrics.json --spa-json-out reports/_runs/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship_spa.json --spa-md-out reports/_runs/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship_spa.md`
- 2026-01-27T06:02:12Z `python - <<'PY' ...` (generate `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/metrics.json` + `snippet.md`)
- 2026-01-27T06:02:17Z `sed -i 's/2018–2019/2018-2019/' docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/snippet.md`
- 2026-01-27T06:10:20Z `source .venv/bin/activate && make test-fast`
  - Result: pass (128 passed, 1 skipped).
- 2026-01-27T06:11:10Z `source .venv/bin/activate && make check-data-policy`
  - Result: pass.
- 2026-01-27T06:11:25Z `source .venv/bin/activate && make validate-runlogs`
  - Result: pass.
- 2026-01-27T06:11:40Z `source .venv/bin/activate && WRDS_DATA_ROOT=/srv/data/wrds/wrds make test-wrds`
  - Result: pass (1 selected).
