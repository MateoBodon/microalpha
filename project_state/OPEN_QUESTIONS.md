<!--
generated_at: 2025-12-21T22:42:31Z
git_sha: 2b48ef75f24acdb206db20d9f5a2681366ac5afa
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
