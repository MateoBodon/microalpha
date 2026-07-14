# Tests

- `pytest -q` — PASS: 129 passed; one third-party deprecation warning.
- `PYTHONPATH=src pytest -q tests/test_docs_links.py tests/test_data_policy.py` — PASS: 2 passed.
- `python3 scripts/check_data_policy.py` — PASS: 1,072 files scanned; 46 allowlisted.
- `python3 scripts/validate_run_logs.py` — PASS: all run logs validated.
