# Commands

1. `date -u +"%Y%m%d_%H%M%S"`
2. `RUN_NAME=20251226_065226_ticket-13_fix-wrds-degeneracy; mkdir -p docs/agent_runs/$RUN_NAME docs/prompts`
3. `cat <<'EOF' > docs/prompts/20251226_065226_ticket-13_fix-wrds-degeneracy.md` (prompt capture)
4. `cp docs/prompts/20251226_065226_ticket-13_fix-wrds-degeneracy.md docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/PROMPT.md`
5. `rg -n "FlagshipMomentumStrategy|momentum" src/microalpha`
6. `sed -n '1,220p' src/microalpha/strategies/flagship_mom.py`
7. `sed -n '220,520p' src/microalpha/strategies/flagship_mom.py`
8. `rg -n "diagnostic|diagnostics|integrity|selection_summary|folds.json|folds" -S src/microalpha`
9. `sed -n '300,720p' src/microalpha/walkforward.py`
10. `apply_patch` (src/microalpha/strategies/flagship_mom.py)
11. `apply_patch` (src/microalpha/walkforward.py)
12. `cat <<'EOF' > tests/test_flagship_filter_diagnostics.py`
13. `rg -n "log_level|debug|verbose|diagnostic" configs src/microalpha`
14. `python3 - <<'PY'` (inspect universe columns)
15. `python3 - <<'PY'` (universe summary stats)
16. `python3 - <<'PY'` (ADV/price threshold counts)
17. `python3 - <<'PY'` (universe vs price-file coverage)
18. `python3 - <<'PY'` (sample price file columns)
19. `rg -n "MultiCsvDataHandler|CsvDataHandler|timestamp|date" src/microalpha/data.py`
20. `sed -n '150,240p' src/microalpha/data.py`
21. `python3 - <<'PY'` (inspect parsed price index)
22. `sed -n '1,120p' configs/wfv_flagship_wrds.yaml`
23. `python3 - <<'PY'` (compute single-fold window dates)
24. `python3 - <<'PY'` (write single-fold debug config)
25. `WRDS_DATA_ROOT=$(python3 - <<'PY' ...) microalpha wfv --config docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/wfv_flagship_wrds_single_fold.yaml` (failed: non-degenerate rejected all candidates)
26. `ls -td artifacts/wrds_flagship_debug/* 2>/dev/null | head -1`
27. `python3 - <<'PY'` (inspect folds.json filter_diagnostics null)
28. `python3 - <<'PY'` (confirm strategy name in debug config)
29. `apply_patch` (src/microalpha/walkforward.py)
30. `WRDS_DATA_ROOT=$(python3 - <<'PY' ...) microalpha wfv --config docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/wfv_flagship_wrds_single_fold.yaml` (failed: non-degenerate rejected all candidates)
31. `ls -td artifacts/wrds_flagship_debug/* 2>/dev/null | head -1`
32. `python3 - <<'PY'` (inspect folds.json filter diagnostics)
33. `python3 - <<'PY'` (summarize exclusion reasons)
34. `rg -n "min_qty|max_single_name_weight|max_positions|turnover_cap|order" src/microalpha/portfolio.py`
35. `sed -n '180,320p' src/microalpha/portfolio.py`
36. `rg -n "def _sized_quantity" -n src/microalpha/portfolio.py`
37. `sed -n '420,520p' src/microalpha/portfolio.py`
38. `rg -n "def _signal_quantity" -n src/microalpha/portfolio.py`
39. `sed -n '360,420p' src/microalpha/portfolio.py`
40. `sed -n '1,200p' src/microalpha/engine.py`
41. `rg -n "cs_symbols" -n src/microalpha/walkforward.py`
42. `sed -n '240,320p' src/microalpha/walkforward.py`
43. `make test-fast`
44. `python3 - <<'PY'` (hash debug config)
45. `ls -td artifacts/wrds_flagship_debug/* 2>/dev/null | head -1`
46. `python3 - <<'PY'` (summarize filter diagnostics stats)
47. `git rev-parse HEAD`
48. `date -u +"%Y-%m-%dT%H:%M:%SZ"`
49. `cat <<'EOF' > docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/RESULTS.md`
50. `cat <<'EOF' > docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/TESTS.md`
51. `cat <<'EOF' > docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/META.json`
52. `apply_patch` (PROGRESS.md)
53. `apply_patch` (project_state/KNOWN_ISSUES.md)
54. `apply_patch` (CHANGELOG.md)
55. `make gpt-bundle TICKET=ticket-13 RUN_NAME=20251226_065226_ticket-13_fix-wrds-degeneracy`
56. `apply_patch` (docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/RESULTS.md)
57. `date -u +"%Y-%m-%dT%H:%M:%SZ"`
58. `python3 - <<'PY'` (update META.json finished_at_utc)
59. `BUNDLE_TIMESTAMP=2025-12-26T07-10-10Z make gpt-bundle TICKET=ticket-13 RUN_NAME=20251226_065226_ticket-13_fix-wrds-degeneracy`
60. `date -u +"%Y-%m-%dT%H:%M:%SZ"`
61. `python3 - <<'PY'` (update META.json finished_at_utc)
62. `date -u +"%Y-%m-%dT%H-%M-%SZ"`
63. `apply_patch` (docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/RESULTS.md)
64. `python3 - <<'PY'` (update META.json finished_at_utc)
65. `BUNDLE_TIMESTAMP=2025-12-26T07-12-26Z make gpt-bundle TICKET=ticket-13 RUN_NAME=20251226_065226_ticket-13_fix-wrds-degeneracy`
66. `git status -sb`
67. `git diff --stat`
68. `git ls-files | rg -n "/Volumes/|Storage/Data|wrds/crsp|wrds/manifests|daily_csv"`
69. `git ls-files | rg -n "^artifacts/|^data/|^data_sp500"`
70. `git ls-files docs/local/WRDS_DATA_ROOT.md`
71. `rg -n "unsafe_execution|allow_unsafe_execution|allow_unsafe|unsafe_execution" configs src/microalpha`
72. `python3 - <<'PY'` (inspect debug manifest + integrity)
73. `apply_patch` (docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/RESULTS.md)
74. `date -u +"%Y-%m-%dT%H:%M:%SZ"`
75. `python3 - <<'PY'` (update META.json finished_at_utc)
