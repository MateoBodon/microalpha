# Ticket 32 — WRDS resume line: pick the best defensible metric window

## Goal
Produce a single "best defensible" WRDS resume line by explicitly choosing (and labeling) **overall WFV OOS** vs **holdout-only** reporting.

## Acceptance criteria
- A run log under `docs/agent_runs/<RUN_NAME>/` documenting which metric window was chosen and why, including exact source paths.
- A new tracked snippet under `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/`:
  - `resume_line_overall_oos.md` (if choosing overall), and/or
  - `resume_line_holdout.md` (if choosing holdout).
- Snippet must explicitly label the reporting window and include `run_id` + `dataset_id`.
- No bulky outputs committed; any scratch stays in `artifacts/_local/<RUN_NAME>/` or `reports/_runs/<RUN_NAME>/`.
