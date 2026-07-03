Filename: docs/tickets/TICKET-32_wrds_resume_line_pick-the-best-defensible-metric.md
Goal: Produce a single “best defensible” WRDS resume line by explicitly choosing (and labeling) overall WFV OOS vs holdout-only reporting, and generating a snippet that matches your resume style (e.g., include CAGR if you want).
Acceptance criteria:

A run log under docs/agent_runs/<RUN_NAME>/ documenting which metric window was chosen and why (with exact source paths).

A new tracked snippet under docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/:

resume_line_overall_oos.md (if choosing overall), and/or

resume_line_holdout.md (if choosing holdout),

with explicit labeling of the window, plus run_id + dataset_id.

No bulky outputs committed; any scratch stays in artifacts/_local/<RUN_NAME>/ or reports/_runs/<RUN_NAME>/.
