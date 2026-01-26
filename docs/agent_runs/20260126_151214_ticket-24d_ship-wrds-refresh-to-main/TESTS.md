Tests:
- `cd /home/codex/repos/microalpha && make test-fast && make check-data-policy && pytest -q tests/test_docs_links.py && make validate-runlogs && git status -sb` (failed: `make: pytest: No such file or directory`).
- `cd /home/codex/repos/microalpha && source .venv/bin/activate && make test-fast && make check-data-policy && pytest -q tests/test_docs_links.py && make validate-runlogs && git status -sb` (pass: `make test-fast` -> 126 passed, 1 skipped, 1 warning; `make check-data-policy` passed; `pytest -q tests/test_docs_links.py` passed; `make validate-runlogs` passed).
