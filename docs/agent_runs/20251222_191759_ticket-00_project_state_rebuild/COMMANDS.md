# Commands

Web research: disabled (no web.run calls).

1. `ls`
2. `cat AGENTS.md`
3. `rg --files src`
4. `rg --files experiments tools scripts tests configs docs examples benchmarks`
5. `sed -n '1,200p' tools/build_project_state.py`
6. `sed -n '200,400p' tools/build_project_state.py`
7. `sed -n '1,200p' tools/render_project_state_docs.py`
8. `sed -n '200,400p' tools/render_project_state_docs.py`
9. `sed -n '400,800p' tools/render_project_state_docs.py`
10. `ls data`
11. `rg -n "2025-12-21T22-32-44Z-2b48ef7" -S .`
12. `sed -n '1,200p' docs/results_wrds.md`
13. `sed -n '1,160p' docs/results_wrds_smoke.md`
14. `git rev-parse --abbrev-ref HEAD`
15. `git checkout -b chore/project_state_refresh`
16. `date -u "+%Y%m%d_%H%M%S"`
17. `date -u "+%Y-%m-%dT%H:%M:%SZ"`
18. `git rev-parse HEAD`
19. `python3 --version`
20. `sed -n '1,200p' docs/DOCS_AND_LOGGING_SYSTEM.md`
21. `rg -n "sample_flagship" README.md`
22. `rg -n "coverage" README.md`
23. `sed -n '1,200p' Makefile`
24. `ls notebooks`
25. `sed -n '1,200p' PROGRESS.md`
26. `sed -n '1,120p' docs/agent_runs/20251222_123806_ticket-11_data-policy-guardrails/RESULTS.md`
27. `sed -n '1,200p' configs/wfv_flagship_wrds_smoke.yaml`
28. `ls data/sample`
29. `ls data/wrds`
30. `apply_patch` (update helpers in `tools/render_project_state_docs.py`)
31. `apply_patch` (add PROGRESS + recent runs to `render_current_results`)
32. `apply_patch` (revise `render_known_issues`)
33. `apply_patch` (wire PROGRESS/recent runs in `main()`)
34. `apply_patch` (case-insensitive progress issue detection)
35. `date -u "+%Y-%m-%dT%H:%M:%SZ"`
36. `PROJECT_STATE_GENERATED_AT=2025-12-22T19:22:33Z python3 tools/build_project_state.py`
37. `PROJECT_STATE_GENERATED_AT=2025-12-22T19:22:33Z python3 tools/render_project_state_docs.py`
38. `sed -n '1,200p' project_state/CURRENT_RESULTS.md`
39. `sed -n '1,200p' project_state/KNOWN_ISSUES.md`
40. `date -u "+%Y-%m-%dT%H:%M:%SZ"`
41. `PROJECT_STATE_GENERATED_AT=2025-12-22T19:23:19Z python3 tools/build_project_state.py`
42. `PROJECT_STATE_GENERATED_AT=2025-12-22T19:23:19Z python3 tools/render_project_state_docs.py`
43. `sed -n '1,200p' project_state/KNOWN_ISSUES.md`
44. `python3 -m pip freeze | shasum -a 256`
45. `date "+%Y-%m-%dT%H:%M:%S%z"`
46. `python3 -c "import platform; print(platform.platform())"`
47. `mkdir -p docs/agent_runs/20251222_191759_ticket-00_project_state_rebuild`
48. `cat <<'EOF' > docs/agent_runs/20251222_191759_ticket-00_project_state_rebuild/PROMPT.md` (heredoc)
49. `cat <<'EOF' > docs/agent_runs/20251222_191759_ticket-00_project_state_rebuild/COMMANDS.md` (heredoc)
50. `apply_patch` (fix COMMANDS.md)
51. `cat <<'EOF' > docs/agent_runs/20251222_191759_ticket-00_project_state_rebuild/RESULTS.md` (heredoc)
52. `cat <<'EOF' > docs/agent_runs/20251222_191759_ticket-00_project_state_rebuild/TESTS.md` (heredoc)
53. `cat <<'EOF' > docs/agent_runs/20251222_191759_ticket-00_project_state_rebuild/META.json` (heredoc)
54. `date -u "+%Y-%m-%dT%H-%M-%SZ"`
55. `zip -r docs/gpt_bundles/project_state_2025-12-22T19-27-41Z_e08b720b.zip project_state docs/PLAN_OF_RECORD.md docs/DOCS_AND_LOGGING_SYSTEM.md PROGRESS.md`
56. `apply_patch` (update `PROGRESS.md`)
57. `apply_patch` (update `META.json` with bundle path)
58. `apply_patch` (update `RESULTS.md` with bundle path)
59. `date -u "+%Y-%m-%dT%H:%M:%SZ"`
60. `PROJECT_STATE_GENERATED_AT=2025-12-22T19:29:50Z python3 tools/build_project_state.py`
61. `PROJECT_STATE_GENERATED_AT=2025-12-22T19:29:50Z python3 tools/render_project_state_docs.py`
62. `sed -n '1,200p' project_state/CURRENT_RESULTS.md`
63. `zip -r docs/gpt_bundles/project_state_2025-12-22T19-27-41Z_e08b720b.zip project_state docs/PLAN_OF_RECORD.md docs/DOCS_AND_LOGGING_SYSTEM.md PROGRESS.md`
