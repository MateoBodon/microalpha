# Runbook

last_updated: 2026-07-03
updated_by: Codex T-001
source_event: Pro strategy install and evidence inventory

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

If using an existing global Python environment, record that in the run log.

## Fast Validation

```bash
git status --short
python3 -m ruff check tools/agentic/ai_os_v2_bundle.py
python3 -m py_compile tools/agentic/ai_os_v2_bundle.py
make check-data-policy
make test-fast
```

`make test-fast` runs:

```bash
PYTHONPATH=src:$PYTHONPATH python3 - <<'PY'
import pathlib
import sys
import microalpha
path = pathlib.Path(microalpha.__file__).resolve()
root = (pathlib.Path.cwd() / "src").resolve()
print(f"microalpha_import_path={path}")
sys.exit(0 if root in path.parents else f"imported non-local microalpha: {path}")
PY
PYTHONPATH=src:$PYTHONPATH python3 scripts/validate_run_logs.py
PYTHONPATH=src:$PYTHONPATH pytest -q
```

The Makefile first prints and asserts the imported `microalpha` path, then sets
`PYTHONPATH=src:$PYTHONPATH` for the run-log validator and pytest. This makes
fast validation import this checkout's local `src/microalpha` package instead of
a different installed checkout. Run logs for validation tickets should record:

```bash
python3 - <<'PY'
import pathlib
import microalpha
print(pathlib.Path(microalpha.__file__).resolve())
PY
```

## Broader Local Checks

```bash
python3 -m ruff check .
python3 -m mypy src/microalpha/reporting/factors.py
python3 -m pytest -q
python3 -m mkdocs build
```

Use these when product code, docs site behavior, typing-sensitive code, or
claim/release surfaces change.

## Sample/Public Workflows

```bash
make sample
make report
make wfv
make report-wfv
microalpha wfv --config configs/wfv_flagship_public.yaml --out artifacts/public_wfv
microalpha report --artifact-dir artifacts/public_wfv/<RUN_ID>
```

## WRDS Workflows

WRDS commands require local licensed exports. Do not run them unless the data
root is present and the ticket calls for WRDS work.

```bash
WRDS_DATA_ROOT=/abs/path/to/wrds make wfv-wrds
WRDS_DATA_ROOT=/abs/path/to/wrds make report-wrds
WRDS_DATA_ROOT=/abs/path/to/wrds make wfv-wrds-smoke
WRDS_DATA_ROOT=/abs/path/to/wrds make report-wrds-smoke
WRDS_DATA_ROOT=/abs/path/to/wrds make wrds-flagship
```

Never commit or bundle raw WRDS data.

## AI OS v2 Archive And Bundles

Archive/index old docs:

```bash
python3 tools/agentic/ai_os_v2_bundle.py --archive-date 20260703 --archive-only
```

Generate the T-000 Project State Audit and Review bundles:

```bash
python3 tools/agentic/ai_os_v2_bundle.py \
  --archive-date 20260703 \
  --project-bundle reports/_bundles/<timestamp>_microalpha_project-state_initial.zip \
  --review-bundle reports/_bundles/<timestamp>_microalpha_review_T-000.zip \
  --run-dir reports/_runs/<run_name>
```

Generate a ticket-specific Heavy review bundle:

```bash
python3 tools/agentic/ai_os_v2_bundle.py \
  --archive-date 20260703 \
  --ticket T-001 \
  --purpose "T-001 strategy/evidence/data-inventory review bundle for Heavy review." \
  --review-bundle reports/_bundles/<timestamp>_microalpha_review_T-001.zip \
  --run-dir reports/_runs/<run_name>
```

Generated bundle zips live under `reports/_bundles/` and are transport artifacts,
not source files.

## Output Zones

| Zone | Use | Git treatment |
|---|---|---|
| `docs/strategy/` | current AI OS v2 strategy docs | tracked |
| `project_state/` | current factual state docs | tracked |
| `docs/_archive/pre_ai_os_v2/` | archive indexes and selected copied historical docs | tracked |
| `reports/_runs/<RUN_NAME>/` | run-scoped command/results logs | ignored except README |
| `reports/_bundles/*.zip` | generated context/review bundles | ignored except README |
| `artifacts/_local/` | local scratch outputs | ignored |
| `docs/artifacts/` | curated small evidence outputs | tracked |

## Troubleshooting

- If `make test-fast` fails in `scripts/validate_run_logs.py`, inspect the
  reported legacy `docs/agent_runs/*/META.json` file before changing tests.
- If data-policy checks fail, do not allowlist blindly; inspect whether the file
  contains raw restricted data or only safe metadata.
- If bundle generation creates an unexpectedly large zip, inspect
  `bundle_manifest.json` and `BUNDLE_INDEX.md` for included/excluded paths.
