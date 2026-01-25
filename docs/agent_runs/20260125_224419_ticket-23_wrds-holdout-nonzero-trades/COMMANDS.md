# Commands

1. `ls`
2. `cat AGENTS.md`
3. `rg --files -g 'AGENTS.md'`
4. `cat PROJECT.md`
5. `cat docs/DOCS_AND_LOGGING_SYSTEM.md`
6. `cat PROGRESS.md`
7. `cat docs/CODEX_SPRINT_TICKETS.md`
8. `ls docs`
9. `ls docs/tickets`
10. `cat docs/tickets/ticket-22_wrds_resume_metrics.md`
11. `sed -n '1,220p' configs/wfv_flagship_wrds.yaml`
12. `rg -n "holdout" src/microalpha`
13. `sed -n '220,420p' src/microalpha/walkforward.py`
14. `sed -n '620,860p' src/microalpha/walkforward.py`
15. `rg -n "order_flow" src/microalpha/walkforward.py`
16. `sed -n '400,520p' src/microalpha/walkforward.py`
17. `sed -n '1020,1145p' src/microalpha/walkforward.py`
18. `rg -n "order_flow" -S .`
19. `sed -n '1,220p' src/microalpha/config.py`
20. `rg -n "_update_manifest" src/microalpha/walkforward.py`
21. `sed -n '1360,1425p' src/microalpha/walkforward.py`
22. `sed -n '860,1045p' src/microalpha/walkforward.py`
23. `rg -n "def evaluate_portfolio_integrity" -n src/microalpha`
24. `sed -n '1,200p' src/microalpha/integrity.py`
25. `rg -n "class FlagshipMomentumStrategy" -n src/microalpha`
26. `sed -n '1,240p' src/microalpha/strategies/flagship_mom.py`
27. `sed -n '1,260p' src/microalpha/order_flow.py`
28. `sed -n '260,520p' src/microalpha/order_flow.py`
29. `rg -n "def compute_metrics" -n src/microalpha`
30. `sed -n '1,200p' src/microalpha/metrics.py`
31. `ls /srv/data/wrds`
32. `ls /srv/data/wrds/wrds`
33. `ls /srv/data/wrds/wrds/crsp/daily_csv | head`
34. `python3 - <<'PY' ... PY` (CSV scan of WRDS universe dates)
35. `tail -n 5 /srv/data/wrds/wrds/universes/flagship_sector_neutral.csv`
36. `tail -n 3 /srv/data/wrds/wrds/crsp/daily_csv/10107.csv`
37. `ls /srv/data/wrds/wrds/derived | head`
38. `head -n 3 /srv/data/wrds/wrds/crsp/daily_csv/10107.csv`
39. `sed -n '1,220p' configs/wfv_flagship_wrds_smoke.yaml`
40. `rg -n "2018-" -m 1 /srv/data/wrds/wrds/universes/flagship_sector_neutral.csv`
41. `cat docs/results_wrds_resume.md`
42. `cat project_state/CURRENT_RESULTS.md`
43. `cat project_state/KNOWN_ISSUES.md`
44. `cat docs/tickets/README.md`
45. `date -u +%Y%m%d_%H%M%S`
46. `rg -n "filter_diagnostics" src/microalpha`
47. `rg -n "holdout" tests`
48. `sed -n '1,240p' tests/test_walkforward.py`
49. `rg -n "wfv-wrds|report-wrds" Makefile`
50. `sed -n '1,120p' Makefile`
51. `git status -sb`
52. `ls -a | rg '^\.venv$' || true`
53. `source .venv/bin/activate && python - <<'PY' ... PY` (pandas version)
54. `source .venv/bin/activate && make test-fast` (failed: missing run-log files)
55. `sed -n '1,260p' scripts/validate_run_logs.py`
56. `ls /srv/data/wrds/wrds/manifests | head`
57. `ls /srv/data/wrds/wrds/manifests | tail -n 5`
58. `ls /srv/data/wrds/wrds/manifests/20251221_001618 | head`
59. `cat /srv/data/wrds/wrds/manifests/20251221_001618/manifest.json`
60. `git rev-parse HEAD`
61. `git rev-parse --abbrev-ref HEAD`
62. `source .venv/bin/activate && python -V`
63. `uname -a`
64. `sha256sum configs/wfv_flagship_wrds.yaml`
65. `python3 - <<'PY' ... PY` (update META.json fields)
66. `source .venv/bin/activate && WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make wfv-wrds`
67. `ls -td artifacts/wrds_flagship/* 2>/dev/null | head`
68. `ls artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18`
69. `ls artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18 | head`
70. `ls artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18 | head -n 20`
71. `ps -ef | rg 'microalpha wfv' || true`
72. `ls artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18 | head -n 30`
73. `ls artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18 | wc -l`
74. `ls artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18 | sort`
75. `ls artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18 | rg -n "metrics|folds|holdout|grid|bootstrap" || true`
76. `ps -p 151768 -o etime,pcpu,cmd`
77. `source .venv/bin/activate && WRDS_ENABLED=1 WRDS_DATA_ROOT=/srv/data/wrds/wrds make report-wrds`
78. `python3 - <<'PY' ... PY` (read holdout/metrics.json summary)
79. `python3 - <<'PY' ... PY` (read spa.json summary)
80. `python3 - <<'PY' ... PY` (read reality_check.json summary)
81. `sha256sum artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18/wfv_flagship_wrds.yaml`
82. `python3 - <<'PY' ... PY` (inspect manifest config_sha256)
83. `source .venv/bin/activate && make check-data-policy`
84. `source .venv/bin/activate && make test-fast`
85. `date -u +%Y-%m-%dT%H:%M:%SZ`
86. `python3 - <<'PY' ... PY` (update META.json with finished time + paths)
87. `python3 tools/agentic/gpt_bundle.py --zip --ticket ticket-23_wrds_holdout_nonzero_trades`
88. `python3 - <<'PY' ... PY` (inspect META.json fields)
89. `python3 tools/agentic/project_state_refresh.py --zip`
90. `python3 tools/build_project_state.py`
91. `python3 tools/render_project_state_docs.py`
92. `python3 - <<'PY' ... PY` (append project_state zip to META.json)
93. `python3 tools/agentic/gpt_bundle.py --zip --ticket ticket-23_wrds_holdout_nonzero_trades`
94. `python3 - <<'PY' ... PY` (append gpt_bundle path to META.json)
95. `git status -sb`
96. `git add -A`
97. `git status -sb`
98. `git commit -m "ticket-23: refresh WRDS holdout and project_state" -m "Tests: make check-data-policy; make test-fast" -m "Artifacts: artifacts/wrds_flagship/2026-01-25T22-58-24Z-4d08d18/; docs/_bundles/project_state_20260125_232239.zip; docs/_bundles/gpt_bundle_20260125_232413_ticket-23_wrds_holdout_nonzero_trades.zip" -m "Docs: docs/results_wrds_resume.md; docs/results_wrds.md; PROGRESS.md; CHANGELOG.md; project_state/CURRENT_RESULTS.md; project_state/KNOWN_ISSUES.md; docs/agent_runs/20260125_224419_ticket-23_wrds-holdout-nonzero-trades/*"`
99. `python3 - <<'PY' ... PY` (update META.json git_sha_after to fdc3bca4)
100. `git add docs/agent_runs/20260125_224419_ticket-23_wrds-holdout-nonzero-trades/COMMANDS.md docs/agent_runs/20260125_224419_ticket-23_wrds-holdout-nonzero-trades/META.json`
101. `git commit -m "ticket-23: finalize run log metadata" -m "Tests: not run (last: make check-data-policy; make test-fast)" -m "Artifacts: none" -m "Docs: docs/agent_runs/20260125_224419_ticket-23_wrds-holdout-nonzero-trades/COMMANDS.md; docs/agent_runs/20260125_224419_ticket-23_wrds-holdout-nonzero-trades/META.json"`
102. `git checkout main`
103. `git merge codex/ticket-22-wrds-resume-metrics`
