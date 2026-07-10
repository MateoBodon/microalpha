# T-000 - Install AI Project OS v2

status: review-ready
owner_flow: Pro planned -> Heavy dispatches -> Codex executes -> Heavy reviews -> Pro recenter
created: 2026-07-03
updated: 2026-07-03

## Goal

Install AI Project OS v2 for microalpha, preserve pre-v2 docs and state
artifacts, create canonical current documentation, and generate the first Project
State Audit Bundle for GPT 5.5 Pro Extended.

## Scope

### In Scope

- Inspect the repo and discover existing docs, prompts, tickets, run logs,
  project_state files, result reports, and old bundles.
- Preserve old docs through `docs/_archive/pre_ai_os_v2/20260703/`.
- Create the requested canonical docs under `docs/strategy/`,
  `docs/tickets/`, and `project_state/`.
- Add simple reusable bundle/archive tooling under `tools/agentic/`.
- Generate a Project State Audit Bundle and T-000 Review Bundle.
- Record commands and validation results.

### Out Of Scope

- Product behavior changes.
- Research method changes.
- Result-number changes.
- Raw WRDS data access, upload, or inclusion in any bundle.
- Rewriting old run logs beyond deprecation/index pointers.

## Acceptance Criteria

- Old docs and artifacts are indexed and selected pre-v2 docs are copied into the
  archive with relative paths preserved.
- Canonical AI OS v2 docs exist and state unknowns honestly.
- Project State Audit Bundle exists under `reports/_bundles/`.
- T-000 Review Bundle exists under `reports/_bundles/`.
- Run log exists under `reports/_runs/20260703_172217_T-000_install_ai_project_os_v2/`.
- Validation commands and outcomes are recorded.
- Bundles exclude raw restricted data and unnecessary large binaries.

## Validation Level

L1 targeted for documentation/tooling plus fast repo checks where available.

Expected commands:

```bash
git status --short
python3 -m py_compile tools/agentic/ai_os_v2_bundle.py
python3 tools/agentic/ai_os_v2_bundle.py --archive-date 20260703 --archive-only
python3 tools/agentic/ai_os_v2_bundle.py --archive-date 20260703 --project-bundle reports/_bundles/... --review-bundle reports/_bundles/... --run-dir reports/_runs/...
python3 -m ruff check tools/agentic/ai_os_v2_bundle.py
make check-data-policy
make test-fast
```

## Stop-The-Line Conditions

- Raw WRDS/private data appears in a bundle.
- Large binary/generated files are bundled without index-only treatment.
- Current docs contradict archive status.
- Validation is fabricated or not recorded.
- Product behavior changes.

## Review Artifacts

- Project State Audit Bundle:
  `reports/_bundles/<timestamp>_microalpha_project-state_initial.zip`
- Review Bundle:
  `reports/_bundles/<timestamp>_microalpha_review_T-000.zip`
- Archive index:
  `docs/_archive/pre_ai_os_v2/20260703/ARCHIVE_INDEX.md`
- Archive manifest:
  `docs/_archive/pre_ai_os_v2/20260703/ARCHIVE_MANIFEST.json`
- Run log:
  `reports/_runs/20260703_172217_T-000_install_ai_project_os_v2/`
