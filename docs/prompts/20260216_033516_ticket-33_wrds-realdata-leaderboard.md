# Ticket 33 — WRDS real-data leaderboard + best resume line

## Goal
Identify the best currently available WRDS real-data resume metrics across existing run artifacts and publish a single best, provenance-complete resume line.

## Context
Current shipped WRDS resume artifacts are centered on run_id `2026-01-27T04-47-22Z-31fe553` with dataset_id `wrds_crsp_export_20251221_v1`, including:
- `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/metrics.json`
- `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/resume_line_holdout.md`
- `project_state/CURRENT_RESULTS.md`

Ticket-32 picked holdout-only as the best-defensible single window, but priority now is best possible currently available real-data metrics without heavy reruns.

## Constraints
- No surprise top-level directories.
- Bulky outputs must stay in `artifacts/_local/<RUN_NAME>/...` or `reports/_runs/<RUN_NAME>/...`.
- Run log required under `docs/agent_runs/<RUN_NAME>/` with `PROMPT.md`, `COMMANDS.md`, `RESULTS.md`, `TESTS.md`, `META.json`.
- Leaderboard must come from artifact-traceable files and carry `run_id` + `dataset_id` (or explicit missing provenance marker).
- Keep outputs small and reviewable (CSV/MD/JSON only).

## Requested implementation
1. Initialize run log.
2. Implement deterministic scanner script (`scripts/wrds_leaderboard.py`) to search:
   - `artifacts/wrds_flagship/**/metrics.json`
   - `artifacts/_local/**/wrds_flagship/**/metrics.json`
3. For each run, merge data from `manifest.json`, `holdout_metrics.json`, and available inference files.
4. Write:
   - `docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
   - `docs/artifacts/resume/wrds/leaderboard/leaderboard.md`
5. Apply pre-registered best rule:
   - Primary: maximize holdout `Sharpe_HAC`
   - Guardrails: `trades >= 20`, `maxdd_pct <= 15%`, `dataset_id` present
   - Tie-breakers: lower MaxDD, higher MAR
6. Write best-line artifact:
   - `docs/artifacts/resume/wrds/leaderboard/resume_line_best.md`
7. Update `project_state/CURRENT_RESULTS.md` with leaderboard/best-line pointers and explicit window label.

## Acceptance criteria
- Complete run log exists for the new run name.
- Tracked leaderboard CSV + MD exist.
- Tracked best resume line exists, with explicit window label and `run_id` + `dataset_id`.
- Selection rule is stated in run log before final selection.
- No bulky committed outputs.
- `project_state/CURRENT_RESULTS.md` references the leaderboard and chosen line.

## Test plan
- `python3 tools/agentic/validate_runlog.py --run-name <RUN_NAME>`
- `python3 scripts/wrds_leaderboard.py --help`
- `python3 scripts/wrds_leaderboard.py --out docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
- `make test-fast` (or justify if not applicable)
