<!--
generated_at: 2025-12-21T21:29:21Z
git_sha: 33c9c2a0bab056c4296a66ee652af49cc646f7df
branch: feat/ticket-02-holdout-wfv
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Known Issues

- WRDS runs require local exports and are blocked without `WRDS_DATA_ROOT` (see `docs/wrds.md`).
- `docs/results_wrds.md` explicitly notes metrics are from a pre-tightening config and need a rerun.
- Some large data directories (`data/`, `data_sp500/`) are present; avoid deep parsing in automation.
- WRDS smoke universe is seeded from 2019 liquidity ranks (survivorship/lookahead) to keep it small; it is **not** valid for performance claims.
- WRDS smoke run produced zero trades and flat SPA comparator t-stats; smoke reports use `--allow-zero-spa` to render despite empty activity.
