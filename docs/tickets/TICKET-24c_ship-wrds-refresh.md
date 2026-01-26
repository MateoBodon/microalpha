# Ticket 24c — Ship WRDS refresh outputs

## Goal
Stage, commit, and push the WRDS refresh outputs (docs + run logs + images) so resume metrics remain auditably current.

## Scope
- Stage/commit modified WRDS docs and project_state outputs tied to the 2026-01-26 WRDS refresh.
- Track required run logs under `docs/agent_runs/20260126_000243_ticket-00_project-state-refresh/`, `docs/agent_runs/20260126_011723_ticket-24_wrds-resume-metrics-refresh/`, and `docs/agent_runs/20260126_023947_ticket-24b_finalize-wrds-refresh/`.
- Track WRDS report images under `docs/img/wrds_flagship/2026-01-26T01-22-23Z-e76eb4d/` and ensure doc links resolve.
- Produce a `gpt_bundle.zip` for this ticket.
- Do **not** add `artifacts/` contents or WRDS raw exports.

## Acceptance Criteria
- `docs/results_wrds.md`, `docs/results_wrds_resume.md`, and `reports/summaries/wrds_flagship.md` reference run `2026-01-26T01-22-23Z-e76eb4d` consistently.
- `project_state/CURRENT_RESULTS.md` and related project_state docs reflect the same run_id.
- Required run logs and ticket docs are tracked and validate via `make validate-runlogs`.
- `make check-data-policy` passes and no WRDS raw files are staged/committed.
- `pytest -q tests/test_docs_links.py` passes.
- `gpt_bundle.zip` produced for `TICKET-24c_ship-wrds-refresh`.
- Git status is clean on `main` after commit and push.

## Plan
1. Add ticket-24c sprint entry and create run log + prompt files.
2. Update living docs (PROGRESS, CHANGELOG) and resolve any untracked outputs.
3. Run required validation/tests and address failures.
4. Stage docs/project_state/run logs/images; commit and push to `origin/main`.
5. Generate `gpt_bundle.zip` for this ticket.

## Notes
- This ticket only ships documentation and audit artifacts; no strategy logic changes.
