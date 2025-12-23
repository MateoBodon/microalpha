# Commands (in order)

1. `ls`
2. `cat AGENTS.md`
3. `cat docs/PLAN_OF_RECORD.md`
4. `cat docs/DOCS_AND_LOGGING_SYSTEM.md`
5. `cat project_state/CURRENT_RESULTS.md`
6. `cat docs/results_wrds.md`
7. `cat docs/results_wrds_smoke.md`
8. `cat docs/CODEX_SPRINT_TICKETS.md`
9. `rg -n "equity_curve|equity curve|equity_curve.csv|metrics.json|trades.jsonl|pnl|PnL|return series|returns" src | head`
10. `sed -n '1,240p' src/microalpha/portfolio.py`
11. `sed -n '240,520p' src/microalpha/portfolio.py`
12. `sed -n '1,260p' src/microalpha/execution.py`
13. `rg -n "slippage|commission|borrow|cost" src/microalpha | head -n 50`
14. `sed -n '1,260p' src/microalpha/runner.py`
15. `sed -n '260,560p' src/microalpha/runner.py`
16. `sed -n '1,260p' src/microalpha/metrics.py`
17. `sed -n '1,260p' src/microalpha/engine.py`
18. `sed -n '1,260p' src/microalpha/walkforward.py`
19. `rg -n "compute_metrics|equity_curve|returns" -n src/microalpha/walkforward.py`
20. `sed -n '380,520p' src/microalpha/walkforward.py`
21. `sed -n '520,820p' src/microalpha/walkforward.py`
22. `sed -n '820,1160p' src/microalpha/walkforward.py`
23. `sed -n '1,200p' src/microalpha/broker.py`
24. `ls artifacts`
25. `ls artifacts/wrds_flagship | tail`
26. `ls artifacts | rg wrds`
27. `ls artifacts/wrds_flagship_smoke | tail`
28. `python - <<'PY'
import pandas as pd
from pathlib import Path
path = Path('artifacts/wrds_flagship_smoke/2025-12-23T06-05-28Z-afe1765/equity_curve.csv')
print('exists', path.exists())
print(pd.read_csv(path).head())
print(pd.read_csv(path).tail())
PY`
29. `python3 - <<'PY'
import pandas as pd
from pathlib import Path
path = Path('artifacts/wrds_flagship_smoke/2025-12-23T06-05-28Z-afe1765/equity_curve.csv')
print('exists', path.exists())
if path.exists():
    df = pd.read_csv(path)
    print(df.head())
    print(df.tail())
    print('equity unique', df['equity'].nunique())
    print('returns unique', df['returns'].nunique())
    print('returns std', df['returns'].std(ddof=0))
PY`
30. `python3 - <<'PY'
import pandas as pd
from pathlib import Path
path = Path('artifacts/wrds_flagship_smoke/2025-12-23T06-05-28Z-afe1765/equity_curve.csv')
if path.exists():
    df = pd.read_csv(path)
    print('equity min', df['equity'].min())
    print('equity max', df['equity'].max())
    print('equity std', df['equity'].std(ddof=0))
    print('nonzero returns', (df['returns']!=0).sum())
    print('max drawdown computed', ((df['equity'].cummax()-df['equity'])/df['equity'].cummax()).max())
    print('avg return', df['returns'].mean())
PY`
31. `python3 - <<'PY'
import json
from pathlib import Path
path = Path('artifacts/wrds_flagship_smoke/2025-12-23T06-05-28Z-afe1765/metrics.json')
print('exists', path.exists())
if path.exists():
    data = json.loads(path.read_text())
    keys = ['sharpe_ratio','max_drawdown','total_turnover','num_trades','commission_total','borrow_cost_total','slippage_total']
    print({k: data.get(k) for k in keys})
PY`
32. `rg -n "zero variance|degenerate|variance" src/microalpha/reporting`
33. `sed -n '330,460p' src/microalpha/reporting/summary.py`
34. `rg -n "degenerate|zero variance|flat equity" reports/summaries/wrds_flagship_smoke.md`
35. `rg -n "Run is degenerate" -n reports/summaries/wrds_flagship_smoke.md`
36. `python3 - <<'PY'
import pandas as pd
from pathlib import Path
path = Path('artifacts/wrds_flagship_smoke/2025-12-23T06-05-28Z-afe1765/grid_returns.csv')
print('exists', path.exists())
if path.exists():
    df = pd.read_csv(path)
    print(df.head())
    print('columns', df.columns)
    print('returns sample', df['returns'].head() if 'returns' in df.columns else None)
    print('unique returns lengths', df['returns'].apply(lambda x: len(str(x))).head())
PY`
37. `python3 - <<'PY'
import pandas as pd
from pathlib import Path
path = Path('artifacts/wrds_flagship_smoke/2025-12-23T06-05-28Z-afe1765/grid_returns.csv')
if path.exists():
    df = pd.read_csv(path)
    print('value stats', df['value'].min(), df['value'].max(), df['value'].std(ddof=0))
    print('nonzero', (df['value']!=0).sum())
    grp = df.groupby('model')['value'].var(ddof=0)
    print('models', grp.head())
    print('all zero variance', (grp.fillna(0)==0).all())
    print('unique models', len(grp))
PY`
38. `rg -n "grid_returns.csv" -n .`
39. `sed -n '1160,1285p' src/microalpha/walkforward.py`
40. `sed -n '1,260p' src/microalpha/data.py`
41. `sed -n '260,520p' src/microalpha/data.py`
42. `rg -n "equity_curve.png|equity_curve" reports src/microalpha/reporting -g"*.py"`
43. `sed -n '1,160p' src/microalpha/reporting/tearsheet.py`
44. `rg -n "total_costs|costs" src/microalpha`
45. `rg -n "run_invalid|invalid|smoke" src/microalpha configs docs -g"*.yaml"`
46. `sed -n '1,220p' src/microalpha/manifest.py`
47. `cat configs/wfv_flagship_wrds_smoke.yaml`
48. `sed -n '1,240p' src/microalpha/config.py`
49. `ls tests`
50. `sed -n '1,200p' tests/test_metrics_invariant.py`
51. `sed -n '1,220p' tests/test_pnl_attribution.py`
52. `python3 - <<'PY'
import json
from pathlib import Path
path = Path('artifacts/wrds_flagship_smoke/2025-12-23T06-05-28Z-afe1765/folds.json')
if path.exists():
    folds = json.loads(path.read_text())
    for i, fold in enumerate(folds):
        test = fold.get('test_metrics', {})
        num_trades = test.get('num_trades')
        sharpe = test.get('sharpe_ratio')
        maxdd = test.get('max_drawdown')
        print(i, 'trades', num_trades, 'sharpe', sharpe, 'maxdd', maxdd)
PY`
53. `rg -n "BacktestCfg|parse_config|config schema|schema" tests | head -n 50`
54. `sed -n '1,120p' tests/test_cfg_unify.py`
55. `sed -n '1,200p' tests/test_manifest_written.py`
56. `rg -n "equity_curve" tests | head -n 50`
57. `sed -n '1,120p' tests/test_wrds_summary_render.py`
58. `sed -n '120,260p' tests/test_wrds_summary_render.py`
59. `rg -n "ticket-11" -n docs/CODEX_SPRINT_TICKETS.md`
60. `sed -n '320,420p' docs/CODEX_SPRINT_TICKETS.md`
61. `python3 - <<'PY'
from pathlib import Path
path = Path('docs/CODEX_SPRINT_TICKETS.md')
text = path.read_text(encoding='utf-8')
marker = '## File: docs/CODEX_SPRINT_TICKETS.md'
idx = text.find(marker)
if idx != -1:
    text = text[:idx].rstrip() + "\n\n"
else:
    text = text.rstrip() + "\n\n"

append = """---\n\n## ticket-12 — Fix WRDS PnL / flat-return integrity\n\n**Goal (1 sentence):** Ensure PnL, costs, and equity curves reconcile so WRDS smoke runs cannot show flat equity when trades/costs exist.\n\n**Why (ties to diagnosis):**\n- Recent WRDS smoke artifacts show nonzero turnover/costs alongside near-zero return variance; we need explicit invariants to catch any flat-equity-with-trades inconsistencies and enforce cost application.\n\n**Acceptance criteria (objective + falsifiable):**\n- New integrity checks assert:\n  - final_equity ≈ initial_equity + realized_pnl + unrealized_pnl − total_costs (with tolerance and explicit components).\n  - turnover > 0 implies num_trades > 0 (or explicit “desired vs executed” justification).\n  - if total_costs > 0 or num_trades > 0 then equity/returns are not exactly constant.\n- Runs that violate integrity are flagged invalid (smoke) or fail fast (headline).\n- A diagnostic script can reconcile `equity_curve.csv`, `metrics.json`, and `trades.jsonl`.\n- Unit tests cover the new invariants using synthetic data (no WRDS required).\n\n**Minimal tests/commands to run:**\n- `make test-fast` (or `pytest -q` if no alias)\n- `pytest -q tests/test_pnl_integrity.py`\n\n**End-of-ticket (must include these three lines):**\n- **Tests run:** …\n- **Artifacts/logs:** …\n- **Documentation updates:** …\n"""
text = text + append
path.write_text(text, encoding='utf-8')
PY`
62. `tail -n 60 docs/CODEX_SPRINT_TICKETS.md`
63. `rg -n "trade_logger = JsonlWriter" -n src/microalpha/walkforward.py`
64. `sed -n '180,220p' src/microalpha/walkforward.py`
65. `rg -n "total_turnover" -n src/microalpha/walkforward.py | head`
66. `sed -n '260,320p' src/microalpha/walkforward.py`
67. `sed -n '380,460p' src/microalpha/walkforward.py`
68. `sed -n '560,660p' src/microalpha/walkforward.py`
69. `rg -n "def _write_docs_results" -n src/microalpha/reporting/wrds_summary.py`
70. `sed -n '600,660p' src/microalpha/reporting/wrds_summary.py`
71. `rg -n "_write_docs_results" -n src/microalpha/reporting/wrds_summary.py`
72. `sed -n '900,980p' src/microalpha/reporting/wrds_summary.py`
73. `rg -n "degenerate_reasons" -n src/microalpha/reporting/wrds_summary.py`
74. `sed -n '810,870p' src/microalpha/reporting/wrds_summary.py`
75. `cat project_state/KNOWN_ISSUES.md`
76. `head -n 60 CHANGELOG.md`
77. `tail -n 40 PROGRESS.md`
78. `git checkout -b codex/ticket-12-fix-wrds-pnl-integrity`
79. `make test-fast`
80. `rg -n "_write_holdout_fixture" -n tests/test_walkforward.py`
81. `sed -n '70,130p' tests/test_walkforward.py`
82. `make test-fast`
83. `printenv WRDS_DATA_ROOT`
84. `make wfv`
85. `make report-wfv`
86. `git status -sb`
87. `git rev-parse HEAD`
88. `shasum -a 256 configs/wfv_flagship_sample.yaml configs/wfv_flagship_wrds_smoke.yaml`
89. `python3 --version`
90. `sw_vers -productVersion`
91. `date -u "+%Y-%m-%dT%H:%M:%SZ"`
92. `mkdir -p docs/agent_runs/20251223_080000_ticket-12_fix-wrds-pnl-integrity docs/prompts`
93. `cat <<'EOF' > docs/prompts/20251223_080000_ticket-12_fix-wrds-pnl-integrity.md` (prompt text)
94. `cp docs/prompts/20251223_080000_ticket-12_fix-wrds-pnl-integrity.md docs/agent_runs/20251223_080000_ticket-12_fix-wrds-pnl-integrity/PROMPT.md`
95. `make gpt-bundle TICKET=ticket-12 RUN_NAME=20251223_080000_ticket-12_fix-wrds-pnl-integrity` (failed: dirty worktree)
96. `git diff --stat`
