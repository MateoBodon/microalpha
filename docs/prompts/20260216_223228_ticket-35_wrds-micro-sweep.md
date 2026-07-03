# Ticket 35 Prompt (verbatim working brief)

Goal: run a small pre-registered WRDS sweep to improve holdout resume-defensible performance, publish the best provenance-complete resume snippet, and refresh WRDS leaderboard outputs.

Key constraints:
- Pre-register sweep knobs, combo cap <= 12, fixed winner rule before execution.
- Keep holdout window fixed to canonical WRDS holdout.
- Local-only bulky outputs under `artifacts/_local/<RUN_NAME>/...` and `reports/_runs/<RUN_NAME>/...`.
- Commit only resume-safe aggregates/snippets; no raw WRDS rows or per-security time series.

Required deliverables:
- Run log under `docs/agent_runs/20260216_223228_ticket-35_wrds-micro-sweep/` with `PROMPT.md`, `COMMANDS.md`, `RESULTS.md`, `TESTS.md`, `META.json`.
- New sweep config at `configs/wfv_flagship_wrds_sweep35.yaml`.
- Promoted resume artifact folder `docs/artifacts/resume/wrds/<BEST_RUN_ID>/` containing `metrics.json`, `manifest_excerpt.json`, `snippet.md`.
- Refreshed leaderboard outputs:
  - `docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
  - `docs/artifacts/resume/wrds/leaderboard/leaderboard.md`
  - `docs/artifacts/resume/wrds/leaderboard/resume_line_best.md`
- Updated `project_state/CURRENT_RESULTS.md` with either new best run or explicit no-improvement outcome.
- `make test-fast` executed and outcome recorded.

Test plan:
- `python3 tools/agentic/validate_runlog.py --run-name 20260216_223228_ticket-35_wrds-micro-sweep`
- `python3 scripts/wrds_leaderboard.py --help`
- `python3 scripts/wrds_leaderboard.py --out docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
- `make test-fast`
