# Commands

Commands executed for ticket-32 window selection and snippet extraction.

1. `git status --short`
2. `ls -la docs/tickets`
3. `ls -la docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553`
4. `sed -n '1,260p' docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/metrics.json`
5. `sed -n '1,260p' docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/best_model_metrics.json`
6. `sed -n '1,260p' docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/manifest_excerpt.json`
7. `sed -n '1,260p' docs/tickets/TICKET-31_wrds_best-real-data-resume-line_from_spa.md`
8. `sed -n '1,260p' artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/manifest.json`
9. `sed -n '1,260p' artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/holdout_manifest.json`
10. `sed -n '1,260p' artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/metrics.json`
11. `sed -n '1,260p' artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/holdout_metrics.json`
12. `sed -n '1,260p' artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/spa.json`
13. `sed -n '1,220p' docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/snippet.md`
14. `sed -n '1,220p' docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/best_model_snippet.md`
15. `sed -n '1,260p' /home/codex/.codex/skills/runlog-init/SKILL.md`
16. `python3 tools/agentic/runlog_init.py --ticket "ticket-32" --summary "Pick one defensible WRDS resume metric window and publish labeled snippet" --run-name "20260216_021416_ticket-32_wrds-resume-line-window-choice"`
17. `python3 - <<'PY' ...` (extract/print overall vs holdout metric comparison values from source JSONs)
18. `date -u +%Y%m%d_%H%M%S`
19. `date -u +%Y-%m-%dT%H:%M:%SZ`
20. `git rev-parse HEAD`
21. `git rev-parse --abbrev-ref HEAD`
22. `sha256sum configs/wfv_flagship_wrds.yaml`
23. `python3 - <<'PY' ...` (print platform + python version)
24. `rg -n "microalpha|wrds|resume line|holdout|overall oos|ticket-31|ticket-32" /home/codex/.codex/memories/MEMORY.md -S`
25. `sed -n '1,260p' /home/codex/.codex/memories/rollout_summaries/019c01c4-3faa-7572-a6a4-9513e7c59091.md`
26. `tail -n 80 PROGRESS.md`
27. `tail -n 80 CHANGELOG.md`
28. `sed -n '1,140p' docs/CODEX_SPRINT_TICKETS.md`
29. `python3 tools/agentic/validate_runlog.py --run-name 20260216_021416_ticket-32_wrds-resume-line-window-choice`
30. `git status --short`
31. `sed -n '1,260p' docs/agent_runs/20260216_021416_ticket-32_wrds-resume-line-window-choice/RESULTS.md`
32. `sed -n '1,260p' docs/agent_runs/20260216_021416_ticket-32_wrds-resume-line-window-choice/META.json`
33. `python3 - <<'PY' ...` (update `finished_at_utc` in run `META.json`)
34. `python3 tools/agentic/validate_runlog.py --run-name 20260216_021416_ticket-32_wrds-resume-line-window-choice`
35. `python3 tools/agentic/validate_runlog.py --run-name 20260216_021416_ticket-32_wrds-resume-line-window-choice` (post-edit recheck)
36. `sed -n '1,320p' /home/codex/.codex/skills/gpt-bundle/SKILL.md`
37. `python3 tools/agentic/gpt_bundle.py --ticket "ticket-32" --run-name "20260216_021416_ticket-32_wrds-resume-line-window-choice"`
38. `sed -n '1,260p' docs/agent_runs/20260216_021416_ticket-32_wrds-resume-line-window-choice/COMMANDS.md`
39. `sed -n '1,260p' docs/agent_runs/20260216_021416_ticket-32_wrds-resume-line-window-choice/RESULTS.md`
40. `sed -n '1,320p' docs/agent_runs/20260216_021416_ticket-32_wrds-resume-line-window-choice/META.json`
41. `python3 - <<'PY' ...` (append bundle path + refresh `finished_at_utc` in run `META.json`)
42. `python3 tools/agentic/validate_runlog.py --run-name 20260216_021416_ticket-32_wrds-resume-line-window-choice`
