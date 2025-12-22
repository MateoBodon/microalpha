<!--
generated_at: 2025-12-22T19:29:50Z
git_sha: e08b720b29a8d96342e12e8fb1fc0beaf009f221
branch: chore/project_state_refresh
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Open Questions

- Full WRDS walk-forward rerun with tightened caps is pending (see `docs/results_wrds.md`).
- Confirm which WRDS export schema is authoritative if additional columns are needed beyond `docs/wrds.md`.
- Decide whether to keep `Plan.md` as long-term roadmap or split into `docs/plan.md` (per `Plan.md`).
- Do we need additional public datasets beyond `data/public/` for regression tests?
