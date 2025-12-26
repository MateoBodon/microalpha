1. `ls`
2. `git status -sb`
3. `date -u +%Y%m%d_%H%M%S`
4. `git checkout -b codex/ticket-15-fix-spa-keyerror`
5. `mkdir -p "docs/agent_runs/20251226_211219_ticket-15_fix-spa-keyerror"`
6. `cat <<'EOF' | tee "docs/prompts/20251226_211219_ticket-15_fix-spa-keyerror.md" "docs/agent_runs/20251226_211219_ticket-15_fix-spa-keyerror/PROMPT.md" >/dev/null`
7. `rg -n "wrds_flagship|report --artifact-dir|report-wrds" docs Makefile src`
8. `sed -n '60,100p' Makefile`
9. `sed -n '1,220p' reports/render_wrds_flagship.py`
10. `rg -n "spa" -n src/microalpha/reporting/wrds_summary.py`
11. `sed -n '420,560p' src/microalpha/reporting/wrds_summary.py`
12. `sed -n '1,240p' src/microalpha/reporting/spa.py`
13. `sed -n '240,520p' src/microalpha/reporting/spa.py`
14. `ls "artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8" | rg "grid_returns|spa"`
15. `python3 - <<'PY' ...` (inspect grid_returns columns/head)
16. `cat "artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/spa.json"`
17. `python3 - <<'PY' ...` (print spa.json status/reason)
18. `rg -n "spa" src/microalpha/reporting/summary.py`
19. `rg -n "SpaSummary|dataclass" -n src/microalpha/reporting/wrds_summary.py`
20. `sed -n '1,120p' src/microalpha/reporting/wrds_summary.py`
21. `sed -n '340,430p' src/microalpha/reporting/wrds_summary.py`
22. `sed -n '700,830p' src/microalpha/reporting/wrds_summary.py`
23. `sed -n '150,320p' src/microalpha/reporting/wrds_summary.py`
24. `sed -n '1,160p' docs/results_wrds.md`
25. `sed -n '1,200p' project_state/CURRENT_RESULTS.md`
26. `rg -n "git_sha_after" docs/agent_runs -g "META.json"`
27. `rg -n "\\.\\.\\." docs/agent_runs -g "PROMPT.md"`
28. `sed -n '1,200p' docs/agent_runs/20251226_122058_ticket-14_wrds-full-run/PROMPT.md`
29. `python3 - <<'PY' ...` (compare PROMPT.md to docs/prompts; initial script)
30. `ls docs/prompts | head`
31. `python3 - <<'PY' ...` (compare PROMPT.md to docs/prompts; improved script)
32. `sed -n '1,200p' docs/agent_runs/20251226_141754_ticket-14_checklist-merge/PROMPT.md`
33. `sed -n '1,200p' project_state/KNOWN_ISSUES.md`
34. `sed -n '1,200p' docs/DOCS_AND_LOGGING_SYSTEM.md`
35. `apply_patch` (update `src/microalpha/reporting/spa.py`)
36. `rg -n "SpaSummary\\(" -n src/microalpha/reporting`
37. `apply_patch` (update `src/microalpha/reporting/wrds_summary.py` SpaSummary init)
38. `sed -n '500,620p' src/microalpha/reporting/wrds_summary.py`
39. `sed -n '400,500p' src/microalpha/reporting/wrds_summary.py`
40. `apply_patch` (update SPA status/error handling + banner helpers in `src/microalpha/reporting/wrds_summary.py`)
41. `apply_patch` (update SPA plot error handling in `src/microalpha/reporting/wrds_summary.py`)
42. `apply_patch` (update SPA markdown rendering in `src/microalpha/reporting/wrds_summary.py`)
43. `apply_patch` (insert inference-failed banner in docs results output)
44. `sed -n '680,760p' src/microalpha/reporting/wrds_summary.py`
45. `sed -n '750,840p' src/microalpha/reporting/wrds_summary.py`
46. `apply_patch` (update SPA highlights copy in docs results)
47. `sed -n '900,1040p' src/microalpha/reporting/wrds_summary.py`
48. `apply_patch` (add headline gating + SPA error labels in WRDS summary)
49. `cat <<'PY' > tests/test_spa_regression_keyerror.py` (new regression test)
50. `make test-fast`
51. `pytest -q tests/test_spa_regression_keyerror.py`
52. `ls artifacts/plots | rg "2025-12-26T17-21-39Z-75ce3c8"`
53. `PYTHONPATH=src:$PYTHONPATH python3 reports/spa.py --grid artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/grid_returns.csv --output-json artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/spa.json --output-md artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/spa.md --bootstrap 2000 --avg-block 63`
54. `PYTHONPATH=src:$PYTHONPATH python3 reports/render_wrds_flagship.py artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8 --output reports/summaries/wrds_flagship.md --factors-md artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/factors_ff5_mom.md --docs-results docs/results_wrds.md --docs-image-root docs/img/wrds_flagship --analytics-plots artifacts/plots --metrics-json-out reports/summaries/wrds_flagship_metrics.json --spa-json-out reports/summaries/wrds_flagship_spa.json --spa-md-out reports/summaries/wrds_flagship_spa.md`
55. `python3 - <<'PY' ...` (inspect updated spa.json status/p_value)
56. `python3 - <<'PY' ...` (inspect reports/summaries/wrds_flagship_spa.json)
57. `sed -n '1,120p' docs/results_wrds.md`
58. `sed -n '1,80p' reports/summaries/wrds_flagship.md`
59. `apply_patch` (update `project_state/CURRENT_RESULTS.md`)
60. `apply_patch` (update `project_state/KNOWN_ISSUES.md`)
61. `sed -n '1,200p' PROGRESS.md`
62. `apply_patch` (update `PROGRESS.md`)
63. `sed -n '240,340p' docs/CODEX_SPRINT_TICKETS.md`
64. `rg -n "ticket-14" docs/CODEX_SPRINT_TICKETS.md`
65. `sed -n '360,460p' docs/CODEX_SPRINT_TICKETS.md`
66. `apply_patch` (update `docs/CODEX_SPRINT_TICKETS.md`)
67. `sed -n '1,200p' CHANGELOG.md`
68. `apply_patch` (update `CHANGELOG.md`)
69. `python3 - <<'PY' ...` (update META git_sha_after values; first attempt failed)
70. `python3 - <<'PY' ...` (update META git_sha_after values; succeeded)
71. `python3 - <<'PY' ...` (verify all git_sha_after are concrete)
72. `git status -sb`
