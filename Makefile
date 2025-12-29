SAMPLE_CONFIG ?= configs/flagship_sample.yaml
SAMPLE_WFV_CONFIG ?= configs/wfv_flagship_sample.yaml
ARTIFACT_DIR ?= artifacts/sample_flagship
WFV_ARTIFACT_DIR ?= artifacts/sample_wfv
WRDS_CONFIG ?= configs/wfv_flagship_wrds.yaml
WRDS_ARTIFACT_DIR ?= artifacts/wrds_flagship
WRDS_SMOKE_CONFIG ?= configs/wfv_flagship_wrds_smoke.yaml
WRDS_SMOKE_ARTIFACT_DIR ?= artifacts/wrds_flagship_smoke

.PHONY: dev test test-fast test-wrds sample wfv wfv-wrds wfv-wrds-smoke wrds wrds-flagship report report-wrds report-wrds-smoke docs clean export-wrds report-wfv gpt-bundle check-data-policy validate-runlogs

dev:
	pip install -e '.[dev]'

test:
	pytest -vv --maxfail=1 --durations=25

test-fast:
	python3 scripts/validate_run_logs.py
	pytest -q

test-wrds:
	pytest -m wrds -vv --maxfail=1 --durations=25

sample:
	microalpha run --config $(SAMPLE_CONFIG) --out $(ARTIFACT_DIR)

wfv:
	microalpha wfv --config $(SAMPLE_WFV_CONFIG) --out $(WFV_ARTIFACT_DIR)

wfv-wrds:
	@if [ -z "$$WRDS_DATA_ROOT" ]; then echo "Set WRDS_DATA_ROOT before running wfv-wrds."; exit 1; fi
	@if [ ! -f "$(WRDS_CONFIG)" ]; then echo "Missing $(WRDS_CONFIG)."; exit 1; fi
	@if grep -q 'WRDS_UNIVERSE_PLACEHOLDER' $(WRDS_CONFIG); then \
		echo "Update WRDS config placeholders before running (see $(WRDS_CONFIG))."; \
		exit 1; \
	fi
	WRDS_DATA_ROOT="$$WRDS_DATA_ROOT" microalpha wfv --config $(WRDS_CONFIG) --out $(WRDS_ARTIFACT_DIR)

wfv-wrds-smoke:
	WRDS_CONFIG=$(WRDS_SMOKE_CONFIG) WRDS_ARTIFACT_DIR=$(WRDS_SMOKE_ARTIFACT_DIR) $(MAKE) wfv-wrds

wrds: wfv-wrds

# Full WRDS flagship pipeline: run walk-forward and render summaries/plots
wrds-flagship: wfv-wrds report-wrds

export-wrds:
	@if [ -z "$$WRDS_DATA_ROOT" ]; then echo "Set WRDS_DATA_ROOT before running export-wrds."; exit 1; fi
	@if [ ! -f "$$HOME/.pgpass" ]; then echo "Missing $$HOME/.pgpass for WRDS access."; exit 1; fi
	@python -c 'from pathlib import Path; import sys; path = Path.home() / ".pgpass"; mode = path.stat().st_mode & 0o777; (mode == 0o600) or (print(f"{path} must have 600 permissions (found {oct(mode)})"), sys.exit(1))'
	PYTHONPATH=src:$$PYTHONPATH python scripts/export_wrds_flagship.py

report:
	@if [ ! -d "$(ARTIFACT_DIR)" ]; then echo "No artifacts at $(ARTIFACT_DIR)"; exit 1; fi
	@latest=$$(ls -td $(ARTIFACT_DIR)/* 2>/dev/null | head -1); \
	if [ -z "$$latest" ]; then echo "No run directories under $(ARTIFACT_DIR)"; exit 1; fi; \
	microalpha report --artifact-dir $$latest

report-wfv:
	@if [ ! -d "$(WFV_ARTIFACT_DIR)" ]; then echo "No artifacts at $(WFV_ARTIFACT_DIR)"; exit 1; fi
	@latest=$$(ls -td $(WFV_ARTIFACT_DIR)/* 2>/dev/null | head -1); \
	if [ -z "$$latest" ]; then echo "No run directories under $(WFV_ARTIFACT_DIR)"; exit 1; fi; \
	microalpha report --artifact-dir $$latest --summary-out reports/summaries/flagship_mom_wfv.md --title "Flagship Walk-Forward"

report-wrds:
	@if [ ! -d "$(WRDS_ARTIFACT_DIR)" ]; then echo "No artifacts at $(WRDS_ARTIFACT_DIR)"; exit 1; fi
	@if [ -z "$$WRDS_DATA_ROOT" ]; then echo "Set WRDS_DATA_ROOT before running report-wrds."; exit 1; fi
	@latest=$$(ls -td $(WRDS_ARTIFACT_DIR)/*/metrics.json 2>/dev/null | head -1 | xargs -I{} dirname {}); \
	if [ -z "$$latest" ]; then echo "No run directories under $(WRDS_ARTIFACT_DIR)"; exit 1; fi; \
	echo "Using WRDS run $$latest"; \
	img_root=docs/img/wrds_flagship; \
	PYTHONPATH=src:$$PYTHONPATH WRDS_DATA_ROOT="$$WRDS_DATA_ROOT" python3 scripts/build_wrds_signals.py --output $$latest/signals.csv --lookback-months 12 --skip-months 1 --min-adv 30000000; \
	PYTHONPATH=src:$$PYTHONPATH python3 reports/analytics.py $$latest --factors data/factors/ff5_mom_daily.csv; \
	PYTHONPATH=src:$$PYTHONPATH python3 reports/factors.py $$latest --factors data/factors/ff5_mom_daily.csv --model ff5_mom --hac-lags 5 --output $$latest/factors_ff5_mom.md; \
	cp $$latest/factors_ff5_mom.md reports/summaries/wrds_flagship_factors.md; \
	PYTHONPATH=src:$$PYTHONPATH python3 reports/tearsheet.py $$latest/equity_curve.csv --bootstrap $$latest/bootstrap.json --metrics $$latest/metrics.json --output $$latest/equity_curve.png --bootstrap-output $$latest/bootstrap_hist.png --title "WRDS Flagship Walk-Forward"; \
	PYTHONPATH=src:$$PYTHONPATH python3 reports/spa.py --grid $$latest/grid_returns.csv --output-json $$latest/spa.json --output-md $$latest/spa.md --bootstrap 2000 --avg-block 63; \
	PYTHONPATH=src:$$PYTHONPATH python3 reports/render_wrds_flagship.py $$latest --output reports/summaries/wrds_flagship.md --factors-md $$latest/factors_ff5_mom.md --docs-results docs/results_wrds.md --docs-image-root $$img_root --analytics-plots artifacts/plots --metrics-json-out reports/summaries/wrds_flagship_metrics.json --spa-json-out reports/summaries/wrds_flagship_spa.json --spa-md-out reports/summaries/wrds_flagship_spa.md

report-wrds-smoke:
	@if [ ! -d "$(WRDS_SMOKE_ARTIFACT_DIR)" ]; then echo "No artifacts at $(WRDS_SMOKE_ARTIFACT_DIR)"; exit 1; fi
	@if [ -z "$$WRDS_DATA_ROOT" ]; then echo "Set WRDS_DATA_ROOT before running report-wrds-smoke."; exit 1; fi
	@latest=$$(ls -td $(WRDS_SMOKE_ARTIFACT_DIR)/*/metrics.json 2>/dev/null | head -1 | xargs -I{} dirname {}); \
	if [ -z "$$latest" ]; then echo "No run directories under $(WRDS_SMOKE_ARTIFACT_DIR)"; exit 1; fi; \
	echo "Using WRDS smoke run $$latest"; \
	img_root=docs/img/wrds_flagship_smoke; \
	PYTHONPATH=src:$$PYTHONPATH WRDS_DATA_ROOT="$$WRDS_DATA_ROOT" python3 scripts/build_wrds_signals.py --output $$latest/signals.csv --lookback-months 12 --skip-months 1 --min-adv 30000000; \
	PYTHONPATH=src:$$PYTHONPATH python3 reports/analytics.py $$latest --factors data/factors/ff5_mom_daily.csv; \
	PYTHONPATH=src:$$PYTHONPATH python3 reports/factors.py $$latest --factors data/factors/ff5_mom_daily.csv --model ff5_mom --hac-lags 5 --output $$latest/factors_ff5_mom.md; \
	cp $$latest/factors_ff5_mom.md reports/summaries/wrds_flagship_smoke_factors.md; \
	PYTHONPATH=src:$$PYTHONPATH python3 reports/tearsheet.py $$latest/equity_curve.csv --bootstrap $$latest/bootstrap.json --metrics $$latest/metrics.json --output $$latest/equity_curve.png --bootstrap-output $$latest/bootstrap_hist.png --title "WRDS Flagship Walk-Forward (Smoke)"; \
	PYTHONPATH=src:$$PYTHONPATH python3 reports/spa.py --grid $$latest/grid_returns.csv --output-json $$latest/spa.json --output-md $$latest/spa.md --bootstrap 500 --avg-block 63; \
	PYTHONPATH=src:$$PYTHONPATH python3 reports/render_wrds_flagship.py $$latest --output reports/summaries/wrds_flagship_smoke.md --factors-md $$latest/factors_ff5_mom.md --docs-results docs/results_wrds_smoke.md --docs-image-root $$img_root --analytics-plots artifacts/plots --metrics-json-out reports/summaries/wrds_flagship_smoke_metrics.json --spa-json-out reports/summaries/wrds_flagship_smoke_spa.json --spa-md-out reports/summaries/wrds_flagship_smoke_spa.md --allow-zero-spa

check-data-policy:
	python3 scripts/check_data_policy.py

validate-runlogs:
	python3 scripts/validate_run_logs.py

gpt-bundle:
	@if [ -z "$(TICKET)" ] || [ -z "$(RUN_NAME)" ]; then echo "Set TICKET and RUN_NAME (e.g., make gpt-bundle TICKET=ticket-01 RUN_NAME=20251220_223500_ticket-01_wrds-tighten-caps)"; exit 1; fi
	@TICKET="$(TICKET)" RUN_NAME="$(RUN_NAME)" python3 tools/gpt_bundle.py

docs:
	mkdocs build

clean:
	rm -rf artifacts/sample_flagship artifacts/sample_wfv reports/summaries/flagship_mom.md reports/summaries/flagship_mom_wfv.md
