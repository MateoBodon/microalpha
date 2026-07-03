# Commands

Log commands that materially change state or produce results.

1. `ls`
2. `rg --files -g 'AGENTS.md'`
3. `sed -n '1,200p' docs/tickets/TICKET-31_wrds_best-real-data-resume-line_from_spa.md` (failed: file missing)
4. `rg --files -g 'TICKET-31*' docs`
5. `rg -n "TICKET-31" -S docs`
6. `sed -n '1,200p' docs/tickets/TICKET-31_wrds_best-possible-metrics_push.md` (failed: file missing)
7. `ls docs`
8. `ls docs/tickets`
9. `sed -n '1,200p' docs/DOCS_AND_LOGGING_SYSTEM.md`
10. `sed -n '1,200p' /home/codex/.codex/skills/runlog-init/SKILL.md`
11. `date -u +%Y%m%d_%H%M%S`
12. `rg -n "ticket-31|TICKET-31" -S docs/CODEX_SPRINT_TICKETS.md`
13. `sed -n '1,200p' docs/CODEX_SPRINT_TICKETS.md`
14. `rg --files -g 'spa.json' -g 'grid_returns.csv' artifacts docs reports`
15. `rg --files -g 'spa.json' -g 'grid_returns.csv'`
16. `rg -n "spa.json" -S`
17. `ls artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553 | head`
18. `ls artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553 | rg -n "spa.json|grid_returns.csv"`
19. `python3 - <<'PY'
import json
from pathlib import Path
path = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/spa.json')
print(path.exists())
spa = json.loads(path.read_text())
print(spa.keys())
print('status', spa.get('status'))
print('p_value', spa.get('p_value'))
print('candidate_stats len', len(spa.get('candidate_stats') or []))
print('candidate_stats keys', spa.get('candidate_stats')[0].keys())
PY`
20. `ls artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553 | rg -n "metrics"`
21. `python3 - <<'PY'
import json
from pathlib import Path
base = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553')
for name in ['metrics.json','holdout_metrics.json']:
    path = base / name
    data = json.loads(path.read_text())
    print('\n', name, 'keys', data.keys())
    print('sample', list(data.items())[:2])
PY`
22. `python3 - <<'PY'
import json
from pathlib import Path
path = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/selection_summary.json')
print(path.exists())
if path.exists():
    data = json.loads(path.read_text())
    print(data.keys())
    print('top keys', list(data.keys())[:10])
    for k in list(data.keys())[:5]:
        print(k, type(data[k]))
PY` (failed: selection_summary is a list)
23. `python3 - <<'PY'
import json
from pathlib import Path
path = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/selection_summary.json')
items = json.loads(path.read_text())
print(type(items), len(items))
print(items[0].keys())
print(items[0])
PY`
24. `python3 - <<'PY'
import json
from pathlib import Path
spa = json.loads(Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/spa.json').read_text())
print(spa['best_model'])
PY`
25. `python3 - <<'PY'
import json
from pathlib import Path
path = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/holdout_manifest.json')
print(path.exists())
if path.exists():
    data = json.loads(path.read_text())
    print(data.keys())
    for k in ['best_model','model','selected_model','config_id']:
        if k in data:
            print(k, data[k])
PY`
26. `python3 - <<'PY'
import pandas as pd
from pathlib import Path
path = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/grid_returns.csv')
print(path.exists())
print(pd.read_csv(path, nrows=5).columns)
PY` (failed: pandas not installed)
27. `head -n 1 artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/grid_returns.csv`
28. `python3 - <<'PY'
import csv
from collections import Counter
from pathlib import Path
path = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/grid_returns.csv')
phases = Counter()
models = Counter()
with path.open() as f:
    reader = csv.DictReader(f)
    for i,row in enumerate(reader):
        if i<10000:
            phases[row['phase']] += 1
            models[row['model']] += 1
        else:
            break
print('phases sample', phases)
print('models sample', list(models.keys())[:3])
PY`
29. `python3 - <<'PY'
import csv
from pathlib import Path
path = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/grid_returns.csv')
phases = set()
rows = 0
with path.open() as f:
    reader = csv.DictReader(f)
    for row in reader:
        phases.add(row['phase'])
        rows += 1
print('rows', rows)
print('phases', sorted(phases))
PY`
30. `python3 - <<'PY'
import json
from pathlib import Path
path = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/reality_check.json')
print(path.exists())
if path.exists():
    data = json.loads(path.read_text())
    print(data.keys())
    print('p_value', data.get('p_value'))
    print('best_model', data.get('best_model'))
    print('candidate_stats sample', data.get('candidate_stats', [])[:2])
PY`
31. `python3 - <<'PY'
import json
from pathlib import Path
path = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/manifest.json')
manifest = json.loads(path.read_text())
print(manifest.keys())
print('dataset_id', manifest.get('dataset_id'))
PY`
32. `python3 - <<'PY'
import json
from pathlib import Path
manifest = json.loads(Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/manifest.json').read_text())
print(manifest.get('wrds'))
PY`
33. `sed -n '1,200p' docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/metrics.json`
34. `ls docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553`
35. `sed -n '1,200p' docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/snippet.md`
36. `python3 - <<'PY'
import json
from pathlib import Path
base = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553')
metrics = json.loads((base/'metrics.json').read_text())
print(metrics.get('reality_check_p_value'))
PY`
37. `python3 - <<'PY'
import json
from pathlib import Path
holdout = json.loads(Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/holdout_metrics.json').read_text())
print('sharpe', holdout['sharpe_ratio'])
print('max_drawdown', holdout['max_drawdown'])
print('calmar_ratio', holdout['calmar_ratio'])
print('cagr', holdout['cagr'])
print('total_turnover', holdout['total_turnover'])
print('turnover_per_day', holdout['turnover_per_day'])
PY`
38. `python3 - <<'PY'
import json
from pathlib import Path
base = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553')
spa = json.loads((base/'spa.json').read_text())
manifest = json.loads((base/'holdout_manifest.json').read_text())
print('spa best', spa['best_model'])
print('holdout selected', manifest['selected_model'])
print('match', spa['best_model'] == manifest['selected_model'])
PY`
39. `python3 tools/agentic/runlog_init.py --ticket "ticket-31" --summary "Extract best-model holdout metrics from spa/grid outputs for resume line" --run-name "20260128_000243_ticket-31_wrds-best-model-resume-line"`
40. `python3 - <<'PY'
import json
from pathlib import Path

run_id = "2026-01-27T04-47-22Z-31fe553"
base = Path('artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship') / run_id
spa = json.loads((base / 'spa.json').read_text())
metrics = json.loads((base / 'metrics.json').read_text())
holdout = json.loads((base / 'holdout_metrics.json').read_text())
manifest = json.loads((base / 'manifest.json').read_text())
holdout_manifest = json.loads((base / 'holdout_manifest.json').read_text())

best_model = spa.get('best_model')
selected_model = holdout_manifest.get('selected_model')
if best_model and selected_model and best_model != selected_model:
    raise SystemExit(f"best_model mismatch: spa={best_model} holdout={selected_model}")

wrds = manifest.get('wrds') or {}
dataset_id = wrds.get('dataset_id')

max_dd = float(holdout['max_drawdown'])
output = {
    "run_id": run_id,
    "dataset_id": dataset_id,
    "best_model_id": best_model,
    "metrics": {
        "sharpe_hac": holdout.get('sharpe_ratio'),
        "max_drawdown": max_dd,
        "max_drawdown_pct": round(max_dd * 100, 2),
        "mar": holdout.get('calmar_ratio'),
        "turnover": holdout.get('total_turnover'),
        "turnover_per_day": holdout.get('turnover_per_day'),
        "reality_check_p_value": metrics.get('reality_check_p_value'),
        "spa_p_value": spa.get('p_value'),
        "spa_status": spa.get('status') or spa.get('spa_status'),
    },
    "sources": {
        "manifest": str(base / 'manifest.json'),
        "holdout_manifest": str(base / 'holdout_manifest.json'),
        "holdout_metrics": str(base / 'holdout_metrics.json'),
        "metrics": str(base / 'metrics.json'),
        "spa": str(base / 'spa.json')
    }
}

out_dir = Path('docs/artifacts/resume/wrds') / run_id
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / 'best_model_metrics.json').write_text(json.dumps(output, indent=2) + "\n", encoding='utf-8')

# Resume snippet
sharpe = output['metrics']['sharpe_hac']
max_dd_pct = output['metrics']['max_drawdown_pct']
mar = output['metrics']['mar']
turnover_m = output['metrics']['turnover'] / 1_000_000
rc_p = output['metrics']['reality_check_p_value']
spa_p = output['metrics']['spa_p_value']

snippet = (
    f"WRDS/CRSP flagship momentum (best-model holdout 2018-2019): "
    f"Sharpe_HAC {sharpe:.3f}, MaxDD {max_dd_pct:.2f}%, MAR {mar:.2f}, "
    f"turnover ${turnover_m:.2f}MM; RealityCheck p={rc_p:.3f}, "
    f"SPA p={spa_p:.3f}. Dataset {dataset_id} (run {run_id})."
)
(out_dir / 'best_model_snippet.md').write_text(snippet + "\n", encoding='utf-8')
print('wrote', out_dir / 'best_model_metrics.json')
print('wrote', out_dir / 'best_model_snippet.md')
PY`
41. `cat <<'EOF' > docs/tickets/TICKET-31_wrds_best-real-data-resume-line_from_spa.md` (create ticket doc)
42. `cat <<'EOF' > docs/prompts/20260128_000243_ticket-31_wrds-best-model-resume-line.md` (prompt capture)
43. `cp docs/prompts/20260128_000243_ticket-31_wrds-best-model-resume-line.md docs/agent_runs/20260128_000243_ticket-31_wrds-best-model-resume-line/PROMPT.md`
44. `git rev-parse HEAD`
45. `git rev-parse --abbrev-ref HEAD`
46. `python3 - <<'PY'
import platform
print(platform.platform())
print(platform.python_version())
PY`
47. `python3 - <<'PY'
import hashlib
from pathlib import Path
path = Path('configs/wfv_flagship_wrds.yaml')
sha = hashlib.sha256(path.read_bytes()).hexdigest()
print(sha)
PY`
48. `cat <<'EOF' > docs/agent_runs/20260128_000243_ticket-31_wrds-best-model-resume-line/RESULTS.md` (write run results)
49. `cat <<'EOF' > docs/agent_runs/20260128_000243_ticket-31_wrds-best-model-resume-line/TESTS.md` (write test log)
50. `date -u +%Y-%m-%dT%H:%M:%SZ`
51. `cat <<'EOF' > docs/agent_runs/20260128_000243_ticket-31_wrds-best-model-resume-line/META.json` (write run metadata)
52. `rg -n "### Added" -n CHANGELOG.md`
53. `sed -n '1,80p' CHANGELOG.md`
54. `cat docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/best_model_metrics.json`
55. `cat docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/best_model_snippet.md`
56. `git status -sb`
57. `cat <<'EOF' > docs/agent_runs/20260128_000243_ticket-31_wrds-best-model-resume-line/RESULTS.md` (update results summary)
58. `python3 tools/agentic/gpt_bundle.py --ticket "ticket-31" --run-name "20260128_000243_ticket-31_wrds-best-model-resume-line"`
59. `python3 - <<'PY' ...` (append gpt bundle path to META.json artifact_paths)
60. `date -u +%Y-%m-%dT%H:%M:%SZ`
61. `python3 - <<'PY' ...` (update META.json finished_at_utc after bundle)
