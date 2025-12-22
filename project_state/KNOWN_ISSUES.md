<!--
generated_at: 2025-12-21T22:42:31Z
git_sha: 2b48ef75f24acdb206db20d9f5a2681366ac5afa
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
- WRDS smoke run produced zero trades and flat SPA comparator t-stats; reporting now skips SPA with a reason and flags degenerate runs (no longer blocks report rendering).
- Full WRDS holdout WFV run `2025-12-21T22-32-44Z-2b48ef7` produced zero trades/flat metrics; investigate data coverage, universe filters, and signal generation before claiming results.
