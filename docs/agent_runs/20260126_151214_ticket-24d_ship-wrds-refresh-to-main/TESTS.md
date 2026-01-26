Tests:
- `make validate-runlogs && make check-data-policy && pytest -q tests/test_docs_links.py && make test-fast` (failed: `/bin/bash: line 1: pytest: command not found`).
- `source .venv/bin/activate && make validate-runlogs && make check-data-policy && pytest -q tests/test_docs_links.py && make test-fast` (pass; pytest: 126 passed, 1 skipped; 1 warning).
