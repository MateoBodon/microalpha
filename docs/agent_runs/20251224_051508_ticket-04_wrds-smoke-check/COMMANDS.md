# Commands

1. `date -u +"%Y%m%d_%H%M%S"`
2. `echo $WRDS_DATA_ROOT`
3. `cat docs/local/WRDS_DATA_ROOT.md`
4. `RUN_NAME=20251224_051508_ticket-04_wrds-smoke-check mkdir -p docs/agent_runs/$RUN_NAME` (and write prompt files)
5. `WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make wfv-wrds-smoke`
6. `WRDS_DATA_ROOT=/Volumes/Storage/Data/wrds make report-wrds-smoke`
7. `ls -t reports/summaries/wrds_flagship_smoke* | head -n 5`
8. `ls -t docs/results_wrds_smoke.md`
9. `ls -t docs/img/wrds_flagship_smoke | head -n 3`
10. `tail -n 20 PROGRESS.md`
11. `git rev-parse HEAD`
12. `python3 - <<'PY'` (sha256 for configs/wfv_flagship_wrds_smoke.yaml)
13. `git status --porcelain`
14. `git ls-files docs/img/wrds_flagship_smoke | head -n 5`
15. `git commit -m "ticket-04: wrds smoke rerun" ...`
16. `date -u +"%Y-%m-%dT%H-%M-%SZ"`
17. `BUNDLE_TIMESTAMP=2025-12-24T05-19-48Z make gpt-bundle TICKET=ticket-04 RUN_NAME=20251224_051508_ticket-04_wrds-smoke-check` (failed: RESULTS placeholder)
18. `apply_patch` (update RESULTS bundle path)
19. `git add -f docs/agent_runs/20251224_051508_ticket-04_wrds-smoke-check/RESULTS.md docs/agent_runs/20251224_051508_ticket-04_wrds-smoke-check/COMMANDS.md`
20. `git commit -m "ticket-04: finalize wrds smoke results" ...`
21. `BUNDLE_TIMESTAMP=2025-12-24T05-19-48Z make gpt-bundle TICKET=ticket-04 RUN_NAME=20251224_051508_ticket-04_wrds-smoke-check`
