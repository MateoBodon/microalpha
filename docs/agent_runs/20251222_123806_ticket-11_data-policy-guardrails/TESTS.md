# Tests

- `pytest -q`
  - Result: 103 passed, 1 skipped in 28.80s.
  - Warnings:
    - DeprecationWarning in `src/microalpha/config.py:87` (ExecModelCfg.aln).
    - FutureWarning in `src/microalpha/reporting/analytics.py:165` (fillna method).
- `python3 -m compileall scripts tools`
  - Result: success.
- `python scripts/check_data_policy.py`
  - Result: failed (`python` not found: `zsh: command not found: python`).
- `python3 scripts/check_data_policy.py`
  - Result: Data policy check passed. Scanned 1072 files; allowlisted 14.
