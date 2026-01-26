# Ticket 24 — WRDS resume metrics refresh

## Goal
Rerun WRDS flagship on codex-worker (AX162-S) and refresh resume-facing real-data metrics docs from the new artifacts.

## Scope
- Run WRDS flagship using local exports at `/srv/data/wrds`.
- Regenerate WRDS report.
- Update `docs/results_wrds_resume.md`, `project_state/CURRENT_RESULTS.md`, and the run log `docs/agent_runs/<RUN_NAME>/RESULTS.md`.
- Do not change strategy logic or candidate grids.
- Do not add/commit raw WRDS data.

## Acceptance Criteria
- New artifacts exist at `artifacts/wrds_flagship/<RUN_ID>/`.
- `docs/results_wrds_resume.md` references `<RUN_ID>`, git SHA, exact commands, and headline metrics with clear labeling.
- `project_state/CURRENT_RESULTS.md` updated to the same `<RUN_ID>` and snapshot.
- Run log `docs/agent_runs/<RUN_NAME>/RESULTS.md` records commands, env notes, and artifact path.
- `make check-data-policy` passes.
- `make validate-runlogs` passes.
- No WRDS raw files staged/committed.

## Plan
1. Create run log scaffold + prompt capture for ticket-24.
2. Execute WRDS flagship + report using `/srv/data/wrds` and collect new run id.
3. Refresh resume-facing docs and project_state headline references.
4. Validate run logs, data policy, and regenerate project_state bundle.
5. Produce gpt bundle and update PROGRESS.

## Notes
- Run used `WRDS_DATA_ROOT=/srv/data/wrds/wrds` because the universe and metadata live under the nested `/wrds` directory on codex-worker.
- Record all commands and environment details in the run log.
