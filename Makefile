SAMPLE_CONFIG ?= configs/flagship_sample.yaml
SAMPLE_WFV_CONFIG ?= configs/wfv_flagship_sample.yaml
ARTIFACT_DIR ?= artifacts/sample_flagship
WFV_ARTIFACT_DIR ?= artifacts/sample_wfv
WRDS_CONFIG ?= configs/wfv_flagship_wrds.yaml
WRDS_ARTIFACT_DIR ?= artifacts/wrds_flagship
WRDS_SMOKE_CONFIG ?= configs/wfv_flagship_wrds_smoke.yaml
WRDS_SMOKE_ARTIFACT_DIR ?= artifacts/wrds_flagship_smoke

.PHONY: dev test test-wrds sample wfv wfv-wrds wfv-wrds-smoke wrds wrds-flagship report report-wrds report-wrds-smoke docs clean export-wrds report-wfv gpt-bundle

dev:
	pip install -e '.[dev]'

test:
	pytest -vv --maxfail=1 --durations=25

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

gpt-bundle:
	@if [ -z "$(TICKET)" ] || [ -z "$(RUN_NAME)" ]; then echo "Set TICKET and RUN_NAME (e.g., make gpt-bundle TICKET=ticket-01 RUN_NAME=20251220_223500_ticket-01_wrds-tighten-caps)"; exit 1; fi
	@python3 - <<'PY'
import json
import os
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

ticket = os.environ.get("TICKET")
run_name = os.environ.get("RUN_NAME")
if not ticket or not run_name:
    raise SystemExit("TICKET and RUN_NAME must be set.")

timestamp = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
bundle_dir = Path("docs/gpt_bundles")
bundle_dir.mkdir(parents=True, exist_ok=True)
stage = bundle_dir / f".staging_{timestamp}_{ticket}_{run_name}"
if stage.exists():
    shutil.rmtree(stage)
stage.mkdir(parents=True, exist_ok=True)

missing = []

def copy_path(src: str) -> None:
    path = Path(src)
    if not path.exists():
        missing.append(src)
        return
    dest = stage / path
    if path.is_dir():
        shutil.copytree(path, dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)

required = [
    "AGENTS.md",
    "docs/PLAN_OF_RECORD.md",
    "docs/DOCS_AND_LOGGING_SYSTEM.md",
    "docs/CODEX_SPRINT_TICKETS.md",
    "PROGRESS.md",
    "project_state/CURRENT_RESULTS.md",
    "project_state/KNOWN_ISSUES.md",
    "project_state/CONFIG_REFERENCE.md",
    f"docs/agent_runs/{run_name}",
]

for item in required:
    copy_path(item)

diff_path = stage / "DIFF.patch"
last_commit_path = stage / "LAST_COMMIT.txt"

meta_path = Path(f"docs/agent_runs/{run_name}/META.json")
sha_before = None
sha_after = None
if meta_path.exists():
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        sha_before = meta.get("git_sha_before")
        sha_after = meta.get("git_sha_after")
    except json.JSONDecodeError:
        pass

diff_cmd = ["git", "diff"]
if sha_before and sha_after:
    diff_cmd += [f"{sha_before}..{sha_after}"]
else:
    diff_cmd += ["HEAD~1..HEAD"]

diff_text = subprocess.check_output(diff_cmd, text=True, stderr=subprocess.STDOUT)
diff_path.write_text(diff_text, encoding="utf-8")

last_commit = subprocess.check_output(
    ["git", "log", "-1", "--pretty=format:%H%n%an%n%ad%n%s"],
    text=True,
)
last_commit_path.write_text(last_commit + "\n", encoding="utf-8")

bundle_path = bundle_dir / f"{timestamp}_{ticket}_{run_name}.zip"
with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for file in stage.rglob("*"):
        if file.is_file():
            zf.write(file, file.relative_to(stage))

shutil.rmtree(stage)

print(bundle_path)
if missing:
    print("Missing bundle items:", ", ".join(missing))
PY

docs:
	mkdocs build

clean:
	rm -rf artifacts/sample_flagship artifacts/sample_wfv reports/summaries/flagship_mom.md reports/summaries/flagship_mom_wfv.md
