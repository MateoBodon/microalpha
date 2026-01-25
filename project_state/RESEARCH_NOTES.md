<!--
generated_at: 2026-01-25T23:23:20Z
git_sha: 4d08d18202a411cd831efce739cd5cb37e6deb1e
branch: codex/ticket-22-wrds-resume-metrics
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Research Notes

- Leakage safety invariants and tests: `docs/leakage-safety.md`, `tests/test_time_ordering.py`, `tests/test_tplus1_execution.py`.
- Reproducibility + manifests: `docs/reproducibility.md`, `src/microalpha/manifest.py`.
- Sample flagship design: `docs/flagship_strategy.md` (12-1 momentum, TWAP, risk-parity allocator).
- WRDS flagship specification: `docs/flagship_momentum_wrds.md` and `configs/wfv_flagship_wrds.yaml`.
- Factor regression workflow: `docs/factors.md`, `reports/factors_ff.py`.
- WRDS results + rerun guidance: `docs/results_wrds.md`.
