# Tests

- `make test-fast`
  - Result: SKIPPED (target not defined in `Makefile`).
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
- Negative check (expected failure):
  - `python3 scripts/check_data_policy.py` after staging `tmp_policy_violation.csv` with `secid` header failed and reported the file (exit non-zero).

## Latest run (2025-12-22)

- `make test-fast`
  - Result: SKIPPED (target not defined in `Makefile`).
- `pytest -q`
  - Result: 103 passed, 1 skipped in 28.48s.
  - Warnings:
    - DeprecationWarning in `src/microalpha/config.py:87` (ExecModelCfg.aln).
    - FutureWarning in `src/microalpha/reporting/analytics.py:165` (fillna method).
- `python3 -m compileall scripts tools`
  - Result: success.
- `python3 scripts/check_data_policy.py`
  - Result: Data policy check passed. Scanned 1072 files; allowlisted 15.
- Negative check (expected failure):
  - Staged `tmp_policy_violation.csv` with `secid`, ran `python3 scripts/check_data_policy.py` (exit 2), reported the file, then cleaned up.
