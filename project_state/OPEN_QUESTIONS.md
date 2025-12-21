<!--
generated_at: 2025-12-21T19:43:02Z
git_sha: bf7e8ea58e82c009404eb0e5fa2ccde8a62a72a2
branch: feat/ticket-06-bundle-commit-consistency
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Open Questions

- Full WRDS walk-forward rerun with tightened caps is pending (see `docs/results_wrds.md`).
- Confirm which WRDS export schema is authoritative if additional columns are needed beyond `docs/wrds.md`.
- Decide whether to keep `Plan.md` as long-term roadmap or split into `docs/plan.md` (per `Plan.md`).
- Do we need additional public datasets beyond `data/public/` for regression tests?
