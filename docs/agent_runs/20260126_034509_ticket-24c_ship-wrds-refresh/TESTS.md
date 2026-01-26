Tests executed:

1) `cd /home/codex/repos/microalpha && make test-fast && make check-data-policy && pytest -q tests/test_docs_links.py && make validate-runlogs && git status -sb && git diff --stat`
   - Failed: `make test-fast` errored (`pytest: No such file or directory`).

2) `cd /home/codex/repos/microalpha && source .venv/bin/activate && make test-fast && make check-data-policy && pytest -q tests/test_docs_links.py && make validate-runlogs && git status -sb && git diff --stat`
   - Passed (126 passed, 1 skipped; warnings: DeprecationWarning in `src/microalpha/config.py:87`).

3) `cd /home/codex/repos/microalpha && make validate-runlogs`
   - Passed.
