# Commands

```
date '+%Y%m%d_%H%M%S'
mkdir -p docs/agent_runs/20251221_173223_ticket-02_holdout-wfv-wrds-full
cat <<'EOF' > docs/agent_runs/20251221_173223_ticket-02_holdout-wfv-wrds-full/PROMPT.md
User request:

1) Run the full WRDS holdout walk-forward (WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make wfv-wrds or make wrds-flagship).
2) Run pytest -q.
EOF
WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make wfv-wrds
pytest -q
sed -n '1,200p' project_state/KNOWN_ISSUES.md
python3 tools/build_project_state.py
python3 tools/render_project_state_docs.py
python3 - <<'PY'
import subprocess, hashlib, sys
out = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True)
print(hashlib.sha256(out.encode()).hexdigest())
PY
python3 - <<'PY'
import hashlib, json, pathlib
path = 'configs/wfv_flagship_wrds.yaml'
data = pathlib.Path(path).read_bytes()
print(json.dumps({path: hashlib.sha256(data).hexdigest()}, indent=2))
PY
ls
git status -sb
ls docs/agent_runs/20251221_173223_ticket-02_holdout-wfv-wrds-full
cat docs/agent_runs/20251221_173223_ticket-02_holdout-wfv-wrds-full/COMMANDS.md
cat docs/agent_runs/20251221_173223_ticket-02_holdout-wfv-wrds-full/RESULTS.md
cat docs/agent_runs/20251221_173223_ticket-02_holdout-wfv-wrds-full/TESTS.md
cat docs/agent_runs/20251221_173223_ticket-02_holdout-wfv-wrds-full/META.json
python3 - <<'PY'
import hashlib, pathlib
path = pathlib.Path('configs/wfv_flagship_wrds.yaml')
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
rg -n "wrds_flagship" PROGRESS.md
tail -n 40 PROGRESS.md
rg -n "zero trades|zero-trade|wrds" project_state/KNOWN_ISSUES.md
git add PROGRESS.md project_state tools/render_project_state_docs.py docs/agent_runs/20251221_173223_ticket-02_holdout-wfv-wrds-full
git status -sb
git commit -m "ticket-02: run full WRDS holdout WFV" -m "Tests: WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make wfv-wrds; pytest -q" -m "Artifacts: artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7 (local only)" -m "Docs: PROGRESS.md, project_state/*, docs/agent_runs/20251221_173223_ticket-02_holdout-wfv-wrds-full/, tools/render_project_state_docs.py"
git rev-parse HEAD
```
