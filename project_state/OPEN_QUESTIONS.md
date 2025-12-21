<!--
generated_at: 2025-12-21T21:29:21Z
git_sha: 33c9c2a0bab056c4296a66ee652af49cc646f7df
branch: feat/ticket-02-holdout-wfv
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Open Questions

- Full WRDS walk-forward rerun with tightened caps is pending (see `docs/results_wrds.md`).
- Confirm which WRDS export schema is authoritative if additional columns are needed beyond `docs/wrds.md`.
- Decide whether to keep `Plan.md` as long-term roadmap or split into `docs/plan.md` (per `Plan.md`).
- Do we need additional public datasets beyond `data/public/` for regression tests?
