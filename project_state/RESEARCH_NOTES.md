<!--
generated_at: 2025-12-21T19:43:02Z
git_sha: bf7e8ea58e82c009404eb0e5fa2ccde8a62a72a2
branch: feat/ticket-06-bundle-commit-consistency
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
