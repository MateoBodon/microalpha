# Commands

```
sed -n '1,200p' docs/results_wrds_smoke.md
sed -n '1,240p' Makefile
ls /Volumes/Storage/Data
ls /Volumes/Storage/Data/wrds
ls /Volumes/Storage/Data/wrds/crsp
ls /Volumes/Storage/Data/wrds/meta
ls /Volumes/Storage/Data/wrds/universes
date '+%Y%m%d_%H%M%S'
mkdir -p docs/agent_runs/20251221_162711_ticket-02_holdout-wfv-wrds
cat <<'EOF' > docs/agent_runs/20251221_162711_ticket-02_holdout-wfv-wrds/PROMPT.md
User request:

WRDS is available, i keep all WRDS raw data at /Volumes/Storage/Data ,look through, find, then continue
EOF
WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make wfv-wrds-smoke
WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make report-wrds-smoke
ls artifacts/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a | rg holdout
rg -n "Latest run" -n docs/results_wrds_smoke.md
python3 tools/build_project_state.py
python3 tools/render_project_state_docs.py
sed -n '1,200p' PROGRESS.md
git status -sb
git status -sb -uall | head -n 120
git status -sb -uall | rg -n "wrds_flagship_smoke_spa"
ls reports/summaries | rg wrds_flagship_smoke
rg -n "WRDS smoke" -n project_state/CURRENT_RESULTS.md -A6
git rev-parse HEAD
python3 - <<'PY'
import subprocess, hashlib, sys
try:
    out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
except Exception:
    print("")
else:
    print(hashlib.sha256(out.encode()).hexdigest())
PY
python3 - <<'PY'
import hashlib, json, pathlib
paths = [
    'configs/wfv_flagship_wrds_smoke.yaml',
]
result = {}
for path in paths:
    data = pathlib.Path(path).read_bytes()
    result[path] = hashlib.sha256(data).hexdigest()
print(json.dumps(result, indent=2))
PY
cat <<'EOF' > docs/agent_runs/20251221_162711_ticket-02_holdout-wfv-wrds/RESULTS.md
# Results

Summary:
- Located WRDS exports under `/Volumes/Storage/Data/wrds` with expected `crsp`, `meta`, and `universes` paths.
- Ran WRDS holdout-capable smoke WFV; holdout artifacts were written alongside WFV outputs.
- Rendered WRDS smoke report outputs and updated `docs/results_wrds_smoke.md` plus summary assets; regenerated project_state docs.

WRDS run:
- WFV smoke run: `artifacts/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a/`
- Holdout artifacts: `holdout_metrics.json`, `holdout_manifest.json`, `holdout_equity_curve.csv`, `holdout_returns.csv`
- Selection summary: `artifacts/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a/selection_summary.json`
- OOS returns: `artifacts/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a/oos_returns.csv`

Docs/report updates:
- `docs/results_wrds_smoke.md`
- `reports/summaries/wrds_flagship_smoke.md`
- `reports/summaries/wrds_flagship_smoke_factors.md`
- `reports/summaries/wrds_flagship_smoke_metrics.json`
- `docs/img/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a/*`

Notes:
- WRDS raw exports remain local; only derived summaries/images updated.
- No new bundle generated for this follow-up run.
EOF
cat <<'EOF' > docs/agent_runs/20251221_162711_ticket-02_holdout-wfv-wrds/TESTS.md
# Tests

- `WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make wfv-wrds-smoke` (pass)
- `WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make report-wrds-smoke` (pass; warnings about pandas fillna and matplotlib tight_layout)
- `pytest -q` (not run in this follow-up)
EOF
python3 - <<'PY'
import json
from pathlib import Path

meta = {
    "run_name": "20251221_162711_ticket-02_holdout-wfv-wrds",
    "ticket_id": "ticket-02",
    "git_sha_before": "33c9c2a0bab056c4296a66ee652af49cc646f7df",
    "git_sha_after": "HEAD",
    "branch": "feat/ticket-02-holdout-wfv",
    "timestamp_local": "2025-12-21T16:27:11",
    "env": {
        "os": "macOS-26.0.1-arm64-arm-64bit",
        "python": "3.12.2",
        "pip_freeze_hash": "d155c3d7c2b41ef4ce242bfec462edd0db5be747333f4495a1e96c8a0252e525",
        "notes": "WRDS exports located under /Volumes/Storage/Data/wrds",
    },
    "data": {
        "mode": "wrds",
        "dataset_id": "wrds_smoke",
        "wrds_data_root": "/Volumes/Storage/Data/wrds",
        "license_notes": "No raw WRDS data committed.",
    },
    "config": {
        "config_paths": ["configs/wfv_flagship_wrds_smoke.yaml"],
        "config_hashes": {
            "configs/wfv_flagship_wrds_smoke.yaml": "3544c267fb31387d4f24f0d4034b9d97a69cdde4e32a73c68e95cd4edee445b3"
        },
    },
    "artifacts": {
        "artifact_dirs": [
            "artifacts/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a"
        ],
        "reports": [
            "reports/summaries/wrds_flagship_smoke.md",
            "reports/summaries/wrds_flagship_smoke_factors.md",
            "reports/summaries/wrds_flagship_smoke_metrics.json",
            "docs/results_wrds_smoke.md",
        ],
    },
    "web_research": {"enabled": False, "sources": []},
}

Path("docs/agent_runs/20251221_162711_ticket-02_holdout-wfv-wrds/META.json").write_text(
    json.dumps(meta, indent=2), encoding="utf-8"
)
PY
git add PROGRESS.md docs/results_wrds_smoke.md reports/summaries/wrds_flagship_smoke.md reports/summaries/wrds_flagship_smoke_factors.md reports/summaries/wrds_flagship_smoke_metrics.json docs/img/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a project_state docs/agent_runs/20251221_162711_ticket-02_holdout-wfv-wrds
git commit -m "ticket-02: run WRDS holdout smoke" -m "Tests: WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make wfv-wrds-smoke; WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make report-wrds-smoke" -m "Artifacts: artifacts/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a/ (local only)" -m "Docs: PROGRESS.md, docs/results_wrds_smoke.md, reports/summaries/wrds_flagship_smoke*, docs/img/wrds_flagship_smoke/2025-12-21T21-28-14Z-33c9c2a/, docs/agent_runs/20251221_162711_ticket-02_holdout-wfv-wrds/"
git status -sb
```
