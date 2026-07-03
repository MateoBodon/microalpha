# Commands

Working directory for commands unless noted: `/home/codex/repos/microalpha`.

1. Initialize run log scaffold:
   - `python3 tools/agentic/runlog_init.py --ticket "ticket-33" --summary "Build WRDS leaderboard and pick best resume line from existing artifacts" --run-name "20260216_033516_ticket-33_wrds-realdata-leaderboard"`

2. Inspect candidate artifact inventory and schema:
   - `find artifacts -type f \( -name 'metrics.json' -o -name 'holdout_metrics.json' -o -name 'manifest.json' \) | rg 'wrds_flagship|wrds'`
   - `python3 - <<'PY' ...` (inspected keys in `metrics.json`, `holdout_metrics.json`, `manifest.json`, `holdout_manifest.json`, `spa.json`, `reality_check.json`)

3. Pre-register best-rule before selection:
   - Edited `docs/agent_runs/20260216_033516_ticket-33_wrds-realdata-leaderboard/RESULTS.md` to record the fixed primary metric, guardrails, and tie-breakers before running selection.

4. Implement scanner:
   - Created `scripts/wrds_leaderboard.py`.

5. Validate scanner CLI and generate outputs:
   - `python3 scripts/wrds_leaderboard.py --help`
   - `python3 scripts/wrds_leaderboard.py --out docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`

6. Inspect generated artifacts:
   - `sed -n '1,220p' docs/artifacts/resume/wrds/leaderboard/leaderboard.md`
   - `sed -n '1,220p' docs/artifacts/resume/wrds/leaderboard/resume_line_best.md`
   - `python3 - <<'PY' ...` (parsed `leaderboard.csv` row count and top rows)

7. Sanity-check script syntax:
   - `python3 -m py_compile scripts/wrds_leaderboard.py`

8. Run repo test target requested by ticket:
   - `PATH=/home/codex/repos/microalpha/.venv/bin:$PATH make test-fast`
   - Outcome: failed at `python3 scripts/validate_run_logs.py` due existing invalid run-log metadata (`docs/agent_runs/20260216_025221_ticket-ticket-32b/META.json`).

9. Update docs pointers and run-log artifacts:
   - Edited `project_state/CURRENT_RESULTS.md`, `project_state/KNOWN_ISSUES.md`, `PROGRESS.md`, `CHANGELOG.md`, `docs/CODEX_SPRINT_TICKETS.md`, `docs/prompts/20260216_033516_ticket-33_wrds-realdata-leaderboard.md`, and run-log files under `docs/agent_runs/20260216_033516_ticket-33_wrds-realdata-leaderboard/`.

10. Validate run-log folder completeness (required test plan item):
   - `python3 tools/agentic/validate_runlog.py --run-name 20260216_033516_ticket-33_wrds-realdata-leaderboard`
