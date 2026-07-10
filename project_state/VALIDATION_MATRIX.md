# Validation Matrix

last_updated: 2026-07-03
updated_by: Codex T-001
source_event: Pro strategy install and evidence inventory

| Level | Command | What It Proves | What It Does Not Prove | Expected Cost |
|---|---|---|---|---|
| L0 | `git status --short` | Shows dirty/untracked state before/after work. | No code correctness. | instant |
| L1 | `python3 -m py_compile tools/agentic/ai_os_v2_bundle.py` | Bundle helper has valid Python syntax. | Runtime bundle contents or policy correctness. | instant |
| L1 | `python3 -m ruff check tools/agentic/ai_os_v2_bundle.py` | New helper satisfies lint/import rules. | Whole-repo lint or behavior. | seconds |
| L1 | `python3 tools/agentic/ai_os_v2_bundle.py ...` | Archive/bundle script can generate zips and manifests. | Full review quality; consumer judgment. | seconds |
| L1 | `make check-data-policy` | Tracked data-like files do not match restricted-data signatures outside allowlist. | It cannot prove all untracked/local data is safe. | seconds |
| L2 | `make test-fast` | Prints/asserts the local `microalpha` import path, validates legacy run logs, and runs the pytest suite with Makefile-enforced `PYTHONPATH=src:$PYTHONPATH`. | Full CI matrix, coverage threshold, MkDocs build, or WRDS reproduction. | minutes |
| L2 | `python3 -m pytest -q` | Unit/integration suite passes in current Python env. | WRDS-only behavior unless data/markers included. | minutes |
| L2 | `python3 -m mkdocs build` | Docs site builds. | Claim correctness. | seconds-minutes |
| L3 | `WRDS_DATA_ROOT=/abs/path make wfv-wrds && make report-wrds` | Local WRDS pipeline can reproduce a run/report. | Public claim approval or data-license safety by itself. | expensive/data-dependent |
| L4 | Claim/evidence audit with rendered docs and artifacts | External-facing claims trace to evidence and caveats. | Future data drift. | review-heavy |

## T-000/T-001 Required Checks

Documentation/tooling/evidence-state tickets should run L0/L1 as applicable and
the safest available L2 fast checks. WRDS commands are not required unless a
ticket explicitly calls for WRDS reproduction and a licensed data root is
available.

## Validation Caveats

- Passing tests do not authorize performance claims.
- Fast-test evidence is only valid if the run log records the imported
  `microalpha.__file__` path or the Makefile contract is unchanged from T-001.
- A generated bundle is only useful if Heavy/Pro can verify inclusion/exclusion
  choices from manifest and index files.
- Historical archive indexes preserve old context; they do not validate old
  claims.
