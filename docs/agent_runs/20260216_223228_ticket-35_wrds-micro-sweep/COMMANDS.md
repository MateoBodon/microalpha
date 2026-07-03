# Commands

Working directory for commands unless noted: `/home/codex/repos/microalpha`.

1. Initialize run log scaffold:
   - `python3 tools/agentic/runlog_init.py --run-name "20260216_223228_ticket-35_wrds-micro-sweep" --ticket "ticket-35" --summary "WRDS micro-sweep for improved holdout metrics + resume snippet"`

2. Pre-register sweep before execution and add sweep config:
   - Edited `docs/agent_runs/20260216_223228_ticket-35_wrds-micro-sweep/PROMPT.md`
   - Added `docs/prompts/20260216_223228_ticket-35_wrds-micro-sweep.md`
   - Added `configs/wfv_flagship_wrds_sweep35.yaml`

3. Execute WRDS micro-sweep (local-only artifacts):
   - `source .venv/bin/activate && WRDS_DATA_ROOT=/srv/data/wrds/wrds MPLCONFIGDIR=/tmp/matplotlib microalpha wfv --config configs/wfv_flagship_wrds_sweep35.yaml --out artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship`

4. Generate run-scoped local report:
   - `source .venv/bin/activate && WRDS_DATA_ROOT=/srv/data/wrds/wrds MPLCONFIGDIR=/tmp/matplotlib microalpha report --artifact-dir artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621 --summary-out reports/_runs/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship.md`

5. Promote resume-safe tracked artifacts for best sweep run:
   - Wrote:
     - `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/metrics.json`
     - `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/manifest_excerpt.json`
     - `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/snippet.md`

6. Refresh leaderboard outputs:
   - `python3 scripts/wrds_leaderboard.py --help`
   - `python3 scripts/wrds_leaderboard.py --out docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`

7. Update policy/docs pointers:
   - Edited `scripts/data_policy_allowlist.txt` (resume aggregate globs)
   - Edited `project_state/CURRENT_RESULTS.md`, `PROGRESS.md`, `CHANGELOG.md`, `docs/CODEX_SPRINT_TICKETS.md`

8. Validate run log + data policy + tests:
   - `python3 tools/agentic/validate_runlog.py --run-name 20260216_223228_ticket-35_wrds-micro-sweep`
   - `source .venv/bin/activate && make check-data-policy`
   - `source .venv/bin/activate && make test-fast` (initial run failed on incomplete META schema for this new run log)
   - Updated `docs/agent_runs/20260216_223228_ticket-35_wrds-micro-sweep/META.json` and added `ticket-35` entry in `docs/CODEX_SPRINT_TICKETS.md`
   - `source .venv/bin/activate && make test-fast` (rerun passed: `128 passed, 1 skipped`)
