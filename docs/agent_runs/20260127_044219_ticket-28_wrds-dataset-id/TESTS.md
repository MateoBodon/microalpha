# Tests

- [x] `source .venv/bin/activate && make test-fast`
  - Result: pass (128 passed, 1 skipped; 1 warning).
- [x] `source .venv/bin/activate && make check-data-policy`
  - Result: pass (scanned 1072 files; allowlisted 46).
- [x] `source .venv/bin/activate && make validate-runlogs`
  - Result: pass.
- [x] `source .venv/bin/activate && WRDS_DATA_ROOT=/srv/data/wrds/wrds make test-wrds`
  - Result: pass (1 selected).
