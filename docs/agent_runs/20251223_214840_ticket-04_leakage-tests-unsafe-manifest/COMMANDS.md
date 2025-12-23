# Commands

1. `ls`
2. `cat AGENTS.md`
3. `cat docs/PLAN_OF_RECORD.md`
4. `cat docs/DOCS_AND_LOGGING_SYSTEM.md`
5. `cat docs/CODEX_SPRINT_TICKETS.md`
6. `rg -n "class BacktestCfg|BacktestCfg|ExecModelCfg|alignment|delay|aln|exec" src/microalpha/config.py`
7. `sed -n '1,260p' src/microalpha/config.py`
8. `sed -n '1,260p' src/microalpha/engine.py`
9. `rg -n "SignalEvent" src/microalpha -S`
10. `sed -n '1,120p' src/microalpha/events.py`
11. `rg -n "lob_tplus1|tplus1|same_day|same_day_fill|same-bar|same_bar|alignment|delay" src/microalpha -S`
12. `sed -n '460,620p' src/microalpha/execution.py`
13. `rg -n "class Executor|execute\(" src/microalpha/execution.py -n`
14. `sed -n '1,140p' src/microalpha/execution.py`
15. `rg -n "exec_model|Executor|LOBExecution|exec.type|exec" src/microalpha/runner.py src/microalpha/walkforward.py src/microalpha/broker.py src/microalpha/portfolio.py -S`
16. `sed -n '80,180p' src/microalpha/runner.py`
17. `sed -n '180,380p' src/microalpha/runner.py`
18. `sed -n '380,520p' src/microalpha/runner.py`
19. `sed -n '160,260p' src/microalpha/portfolio.py`
20. `rg -n "unsafe|leakage|lookahead|t\+1|tplus1|same.*bar|same.*tick" src/microalpha -S`
21. `rg -n "get_future_timestamps" -n src/microalpha -S`
22. `sed -n '70,140p' src/microalpha/data.py`
23. `rg -n "manifest|build\(" src/microalpha/runner.py src/microalpha/walkforward.py -S`
24. `sed -n '80,180p' src/microalpha/runner.py`
25. `sed -n '180,380p' src/microalpha/runner.py`
26. `sed -n '380,520p' src/microalpha/runner.py`
27. `sed -n '1,260p' src/microalpha/manifest.py`
28. `sed -n '1,220p' src/microalpha/reporting/summary.py`
29. `sed -n '1,240p' src/microalpha/reporting/wrds_summary.py`
30. `rg -n "manifest.json" -n src/microalpha/reporting`
31. `sed -n '760,860p' src/microalpha/reporting/wrds_summary.py`
32. `rg -n "lines = \\[\\]|lines.append\\(" -n src/microalpha/reporting/wrds_summary.py`
33. `sed -n '620,760p' src/microalpha/reporting/wrds_summary.py`
34. `sed -n '860,980p' src/microalpha/reporting/wrds_summary.py`
35. `ls artifacts/sample_flagship`
36. `ls -td artifacts/sample_flagship/* | head -1`
37. `cat artifacts/sample_flagship/2025-12-20T23-30-48Z-f8b316f/manifest.json`
38. `sed -n '1,240p' project_state/CONFIG_REFERENCE.md`
39. `cat project_state/KNOWN_ISSUES.md`
40. `sed -n '1,240p' tools/build_project_state.py`
41. `sed -n '1,240p' tools/render_project_state_docs.py`
42. `ls tests`
43. `sed -n '1,200p' tests/test_no_lookahead.py`
44. `sed -n '1,200p' tests/test_manifest_written.py`
45. `sed -n '1,200p' tests/test_artifacts_schema.py`
46. `sed -n '1,200p' tests/test_tplus1_execution.py`
47. `rg -n "lob_tplus1" tests -S`
48. `rg -n "def run_walk_forward|run_walk_forward" -n src/microalpha/walkforward.py`
49. `sed -n '160,260p' src/microalpha/walkforward.py`
50. `sed -n '720,820p' src/microalpha/walkforward.py`
51. `ls configs`
52. `rg -n "lob_tplus1|lob" configs/*.yaml`
53. `cat configs/mm_lob_same_tick.yaml`
54. `rg -n "def _write_docs_results" -n src/microalpha/reporting/wrds_summary.py`
55. `sed -n '610,660p' src/microalpha/reporting/wrds_summary.py`
56. `rg -n "summary" tests/test_reporting_analytics.py tests/test_reporting_robustness.py tests/test_reporting_spa.py tests/test_manifest_written.py -S`
57. `sed -n '1,200p' tests/test_reporting_robustness.py`
58. `date -u +"%Y%m%d_%H%M%S"`
59. `git checkout -b codex/ticket-04-leakage-tests-unsafe-manifest`
60. `echo $WRDS_DATA_ROOT`
61. `cat CHANGELOG.md`
62. `sed -n '1,200p' PROGRESS.md`
63. `cat .gitignore`
64. `ls reports/summaries | head`
65. `rg -n "def report|summary|summary-out|title" src/microalpha/cli.py src/microalpha/reporting -S`
66. `pytest -q tests/test_no_lookahead.py` (failed: FileExistsError)
67. `pytest -q tests/test_no_lookahead.py`
68. `make test-fast`
69. `make sample`
70. `make report`
71. `microalpha run --config configs/mm_lob_same_tick.yaml --out artifacts/mm_lob_same_tick`
72. `microalpha report --artifact-dir artifacts/mm_lob_same_tick/2025-12-23T22-00-05Z-ba5b480 --summary-out reports/summaries/_artifacts/mm_lob_same_tick.md --title "LOB Same Tick (Unsafe)"`
73. `rg -n "UNSAFE" reports/summaries/_artifacts/mm_lob_same_tick.md`
74. `python3 tools/build_project_state.py`
75. `python3 tools/render_project_state_docs.py`
76. `rg -n "mm_lob_same_tick" -n project_state/CONFIG_REFERENCE.md`
77. `head -40 project_state/KNOWN_ISSUES.md`
78. `git rev-parse HEAD`
79. `git status --porcelain`
80. `git diff -- docs/CODEX_SPRINT_TICKETS.md`
81. `tail -n 10 docs/CODEX_SPRINT_TICKETS.md`
82. `git diff -U5 docs/CODEX_SPRINT_TICKETS.md`
83. `git show HEAD:docs/CODEX_SPRINT_TICKETS.md | tail -n 10`
84. `RUN_NAME=20251223_214840_ticket-04-leakage-tests-unsafe-manifest mkdir -p docs/agent_runs/$RUN_NAME`
85. `cat <<'EOF' > docs/prompts/20251223_214840_ticket-04-leakage-tests-unsafe-manifest_ticket-04_leakage-tests-unsafe-manifest.md (and copy to docs/agent_runs/20251223_214840_ticket-04-leakage-tests-unsafe-manifest/PROMPT.md)`
86. `python3 - <<'PY'` (sha256 for configs/flagship_sample.yaml and configs/mm_lob_same_tick.yaml)
87. `git status --porcelain --untracked-files=all | head -n 40`
88. `git status --porcelain --untracked-files=all | rg "^\\?\\?"`
89. `ls docs/agent_runs | tail -n 5`
90. `git ls-files docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest`
91. `git status --porcelain --ignored | rg "docs/agent_runs"`
92. `cat .git/info/exclude`
93. `git diff -- reports/summaries/flagship_mom.md | head -n 40`
94. `date -u +"%Y-%m-%dT%H-%M-%SZ"`
95. `git add src/microalpha/config.py src/microalpha/execution_safety.py src/microalpha/engine.py src/microalpha/manifest.py src/microalpha/runner.py src/microalpha/walkforward.py src/microalpha/reporting/summary.py src/microalpha/reporting/wrds_summary.py tests/test_no_lookahead.py configs/mm_lob_same_tick.yaml`
96. `git commit -m "ticket-04: add unsafe execution guardrails" -m "Tests: pytest -q tests/test_no_lookahead.py; make test-fast" -m "Artifacts: artifacts/sample_flagship/2025-12-23T21-59-20Z-ba5b480/; artifacts/mm_lob_same_tick/2025-12-23T22-00-05Z-ba5b480/" -m "Docs: n/a"`
97. `git status --porcelain`
98. `git add CHANGELOG.md PROGRESS.md reports/summaries/flagship_mom.md project_state project_state/_generated`
99. `git add -f docs/CODEX_SPRINT_TICKETS.md docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest`
100. `git status --porcelain`
101. `git add -f docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest`
102. `git commit -m "ticket-04: update logs and project state" -m "Tests: pytest -q tests/test_no_lookahead.py; make test-fast" -m "Artifacts: artifacts/sample_flagship/2025-12-23T21-59-20Z-ba5b480/; artifacts/mm_lob_same_tick/2025-12-23T22-00-05Z-ba5b480/" -m "Docs: PROGRESS.md, CHANGELOG.md, project_state/*, docs/agent_runs/*"`
103. `git rev-parse HEAD`
104. `cat <<'EOF' > docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest/META.json`
105. `git add -f docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest/META.json`
106. `git commit -m "ticket-04: add run meta" -m "Tests: pytest -q tests/test_no_lookahead.py; make test-fast" -m "Artifacts: artifacts/sample_flagship/2025-12-23T21-59-20Z-ba5b480/; artifacts/mm_lob_same_tick/2025-12-23T22-00-05Z-ba5b480/" -m "Docs: docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest/META.json"`
107. `BUNDLE_TIMESTAMP=2025-12-23T22-22-01Z make gpt-bundle TICKET=ticket-04 RUN_NAME=20251223_214840_ticket-04_leakage-tests-unsafe-manifest`
108. `git status --porcelain`
109. `git add -f docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest/META.json`
110. `git commit -m "ticket-04: update run meta for bundle" -m "Tests: pytest -q tests/test_no_lookahead.py; make test-fast" -m "Artifacts: artifacts/sample_flagship/2025-12-23T21-59-20Z-ba5b480/; artifacts/mm_lob_same_tick/2025-12-23T22-00-05Z-ba5b480/" -m "Docs: docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest/META.json"`
111. `BUNDLE_TIMESTAMP=2025-12-23T22-22-01Z make gpt-bundle TICKET=ticket-04 RUN_NAME=20251223_214840_ticket-04_leakage-tests-unsafe-manifest`
112. `git status --porcelain`
113. `git add -f docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest/RESULTS.md docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest/COMMANDS.md`
114. `git commit -m "ticket-04: finalize run results" -m "Tests: pytest -q tests/test_no_lookahead.py; make test-fast" -m "Artifacts: artifacts/sample_flagship/2025-12-23T21-59-20Z-ba5b480/; artifacts/mm_lob_same_tick/2025-12-23T22-00-05Z-ba5b480/" -m "Docs: docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest/RESULTS.md"`
115. `git status --porcelain`
116. `git --no-pager log --oneline -n 5`
