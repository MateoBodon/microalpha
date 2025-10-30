SAMPLE_CONFIG ?= configs/flagship_sample.yaml
SAMPLE_WFV_CONFIG ?= configs/wfv_flagship_sample.yaml
ARTIFACT_DIR ?= artifacts/sample_flagship
WFV_ARTIFACT_DIR ?= artifacts/sample_wfv
WRDS_CONFIG ?= configs/wfv_flagship_wrds.yaml
WRDS_ARTIFACT_DIR ?= artifacts/wrds_flagship

.PHONY: dev test sample wfv wrds report docs clean

dev:
	pip install -e '.[dev]'

test:
	pytest -q

sample:
	microalpha run --config $(SAMPLE_CONFIG) --out $(ARTIFACT_DIR)

wfv:
	microalpha wfv --config $(SAMPLE_WFV_CONFIG) --out $(WFV_ARTIFACT_DIR)

wrds:
	@if [ ! -f "$(WRDS_CONFIG)" ]; then echo "Missing $(WRDS_CONFIG)."; exit 1; fi
	@if grep -q 'WRDS_UNIVERSE_PLACEHOLDER' $(WRDS_CONFIG); then \
		echo "Update WRDS config placeholders before running (see $(WRDS_CONFIG))."; \
		exit 1; \
	fi
	microalpha wfv --config $(WRDS_CONFIG) --out $(WRDS_ARTIFACT_DIR)

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

docs:
	mkdocs build

clean:
	rm -rf artifacts/sample_flagship artifacts/sample_wfv reports/summaries/flagship_mom.md reports/summaries/flagship_mom_wfv.md
