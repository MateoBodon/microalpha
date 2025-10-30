SAMPLE_CONFIG ?= configs/flagship_sample.yaml
SAMPLE_WFV_CONFIG ?= configs/wfv_flagship_sample.yaml
ARTIFACT_DIR ?= artifacts/sample_flagship
WFV_ARTIFACT_DIR ?= artifacts/sample_wfv

.PHONY: dev test sample wfv report docs clean

dev:
	pip install -e '.[dev]'

test:
	pytest -q

sample:
	microalpha run --config $(SAMPLE_CONFIG) --out $(ARTIFACT_DIR)

wfv:
	microalpha wfv --config $(SAMPLE_WFV_CONFIG) --out $(WFV_ARTIFACT_DIR)

report:
	microalpha report --artifact-dir $(ARTIFACT_DIR)

report-wfv:
	microalpha report --artifact-dir $(WFV_ARTIFACT_DIR) --summary-out reports/summaries/flagship_mom_wfv.md --title "Flagship Walk-Forward"

docs:
	mkdocs build

clean:
	rm -rf artifacts/sample_flagship artifacts/sample_wfv reports/summaries/flagship_mom.md reports/summaries/flagship_mom_wfv.md
