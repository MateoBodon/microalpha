<!--
generated_at: 2025-12-21T19:48:07Z
git_sha: 631272f7041bff01de865fa5139a4a9e4004c3b2
branch: feat/ticket-06-bundle-commit-consistency
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
