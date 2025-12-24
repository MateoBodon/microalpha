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
