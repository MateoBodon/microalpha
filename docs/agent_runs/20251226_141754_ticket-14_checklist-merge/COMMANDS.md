# Commands

1. `date "+%Y%m%d_%H%M%S"`
2. `mkdir -p docs/agent_runs/20251226_141754_ticket-14_checklist-merge`
3. `cat > docs/prompts/20251226_141754_ticket-14_checklist-merge_ticket-14_checklist-merge.md <<'EOF' ... EOF`
4. `cat > docs/agent_runs/20251226_141754_ticket-14_checklist-merge/PROMPT.md <<'EOF' ... EOF`
5. `sed -n '1,200p' docs/agent_runs/20251226_091335_ticket-14_order-flow-trace/RESULTS.md`
6. `python3 - <<'PY' ... PY` (inspect pre-fix folds.json order_flow_diagnostics)
7. `python3 - <<'PY' ... PY` (inspect post-fix folds.json order_flow_diagnostics)
8. `python3 - <<'PY' ... PY` (inspect manifest.json for order_flow_diagnostics)
9. `cat docs/agent_runs/20251226_091335_ticket-14_order-flow-trace/META.json`
10. `cat docs/agent_runs/20251226_122058_ticket-14_wrds-full-run/META.json`
11. `rg -n "ticket-13|ticket-14" -n docs/CODEX_SPRINT_TICKETS.md`
12. `sed -n '360,440p' docs/CODEX_SPRINT_TICKETS.md`
13. `git log --oneline --decorate -n 15`
14. `apply_patch` (update docs/agent_runs/20251226_091335_ticket-14_order-flow-trace/META.json git_sha_after)
15. `apply_patch` (update docs/agent_runs/20251226_122058_ticket-14_wrds-full-run/META.json git_sha_after)
16. `apply_patch` (update docs/agent_runs/20251226_091335_ticket-14_order-flow-trace/RESULTS.md with stage evidence)
17. `git diff main..HEAD -- configs`
18. `git diff main..HEAD -U0 | rg -n "min_adv|min_price|min_trades|min_turnover|max_exposure|max_single_name_weight|turnover_cap|turnover"`
19. `git show --stat 7d23c4b7`
20. `git diff main..HEAD -- src/microalpha/portfolio.py`
21. `ls -la artifacts/wrds_flagship_debug/2025-12-26T09-33-29Z-695a387`
22. `ls -la artifacts/wrds_flagship_debug/2025-12-26T09-44-24Z-695a387`
23. `cat docs/agent_runs/20251226_091335_ticket-14_order-flow-trace/TESTS.md`
24. `ls -1 docs/agent_runs/20251226_091335_ticket-14_order-flow-trace`
25. `ls -1 docs/agent_runs/20251226_122058_ticket-14_wrds-full-run`
26. `date -u "+%Y-%m-%dT%H-%M-%SZ"`
27. `cat > docs/agent_runs/20251226_141754_ticket-14_checklist-merge/TESTS.md <<'EOF' ... EOF`
28. `cat > docs/agent_runs/20251226_141754_ticket-14_checklist-merge/RESULTS.md <<'EOF' ... EOF`
29. `apply_patch` (update PROGRESS.md with checklist run entry)
30. `git add PROGRESS.md`
31. `git add -f docs/agent_runs/20251226_091335_ticket-14_order-flow-trace/META.json docs/agent_runs/20251226_091335_ticket-14_order-flow-trace/RESULTS.md docs/agent_runs/20251226_122058_ticket-14_wrds-full-run/META.json docs/agent_runs/20251226_141754_ticket-14_checklist-merge/COMMANDS.md docs/agent_runs/20251226_141754_ticket-14_checklist-merge/PROMPT.md docs/agent_runs/20251226_141754_ticket-14_checklist-merge/RESULTS.md docs/agent_runs/20251226_141754_ticket-14_checklist-merge/TESTS.md docs/prompts/20251226_141754_ticket-14_checklist-merge_ticket-14_checklist-merge.md`
32. `git commit -m "ticket-14: finalize checklist evidence" -m "Tests: not run (checklist-only; see prior run logs)" -m "Artifacts: artifacts/wrds_flagship_debug/2025-12-26T09-33-29Z-695a387/, artifacts/wrds_flagship_debug/2025-12-26T09-44-24Z-695a387/, artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/" -m "Docs: docs/agent_runs/20251226_091335_ticket-14_order-flow-trace/, docs/agent_runs/20251226_122058_ticket-14_wrds-full-run/, docs/agent_runs/20251226_141754_ticket-14_checklist-merge/, PROGRESS.md"`
33. `git rev-parse HEAD`
34. `date -u "+%Y-%m-%dT%H:%M:%SZ"`
35. `cat > docs/agent_runs/20251226_141754_ticket-14_checklist-merge/META.json <<'EOF' ... EOF`
36. `BUNDLE_TIMESTAMP=2025-12-26T19-22-33Z make gpt-bundle TICKET=ticket-14 RUN_NAME=20251226_141754_ticket-14_checklist-merge` (failed: invalid revision range)
37. `git log --reverse --pretty=format:%H\ %s 9a2ffa30e9df9754195a4003c7237edb19f67fb5..2450bf0793208ceea3cab5ef037eceeb1496809a`
38. `git show --quiet --pretty=format:%P 2450bf0793208ceea3cab5ef037eceeb1496809a`
39. `git rev-parse 9a2ffa30`
40. `apply_patch` (fix git_sha_after in docs/agent_runs/20251226_122058_ticket-14_wrds-full-run/META.json)
41. `apply_patch` (fix git_sha_before in docs/agent_runs/20251226_141754_ticket-14_checklist-merge/META.json)
