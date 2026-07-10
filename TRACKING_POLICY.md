# Tracking Policy

This policy keeps repos clean, reviewable, and consistent across projects.

## Core principles

1. **Everything important is reproducible.**  
   If a result matters, we record how to reproduce it (command, inputs, config, git SHA).

2. **Large / machine-specific outputs stay out of git.**  
   Git history should remain fast and reviewable.

3. **Logs are structured and easy to audit.**  
   Every run has a run folder with standard files and explicit paths to outputs.

## Canonical zones

### Tracked (commit these)

- `docs/`  
  Human-facing documentation, including:
  - `docs/agent_runs/` — run logs (**tracked**)
  - `docs/tickets/` — scoped work items
  - `docs/artifacts/` — curated, stable outputs (small tables/plots/manifests)

- `project_state/`  
  Curated “how this project works” snapshot (may include a `_generated/` subfolder that is rebuildable).

- Source code, configs, tests.

### Ignored (local-only)

These are allowed top-level scratch zones. Put new large outputs here.

- `artifacts/_local/`  
  Local datasets, zips, large intermediates.

- `reports/_runs/`  
  Run-scoped bulky outputs (one folder per run).

- `reports/_bundles/`
  Generated context/review/state bundle zips. Keep the README tracked; leave
  generated zips ignored unless a release/audit explicitly asks to track one.

- `docs/_generated/`, `docs/_bundles/`, `project_state/_generated/`  
  Rebuildable generated files (unless your project intentionally tracks some of them).

- `.cache/`, `tmp/`, `.venv/`, `__pycache__/`

- `.agent/` (if your runner creates it)

## Rules of engagement

### No surprise top-level directories
Do **not** create new top-level directories unless they are one of the canonical zones above.  
If you genuinely need a new top-level directory, document it and update `.gitignore` accordingly.

### Run outputs must be run-scoped
New output directories must include a run name in the path, e.g.:

- `docs/agent_runs/<RUN_NAME>/...` (logs; tracked)
- `docs/artifacts/<topic>/<date>/...` (curated; tracked)
- `reports/_runs/<RUN_NAME>/...` (bulky; ignored)
- `reports/_bundles/<BUNDLE_NAME>.zip` (context bundles; ignored)
- `artifacts/_local/<RUN_NAME>/...` (local; ignored)

### Never depend on `.git/info/exclude`
If something should be ignored, it belongs in `.gitignore` (shared policy).

### Promote, don’t commit raw dumps
If a run produces a useful result in `reports/_runs/` or `artifacts/_local/`:
- promote a **small** summary artifact into `docs/artifacts/`
- link to the raw output path from `docs/agent_runs/<RUN_NAME>/RESULTS.md`

### Deterministic manifests
When outputs depend on data or randomness, record:
- input file names + hashes (or dataset version)
- seeds
- key config flags
- the git SHA

## Run logging contract (non-negotiable)

Every run must have a folder:

`docs/agent_runs/<RUN_NAME>/`

Minimum files:
- `PROMPT.md`
- `COMMANDS.md`
- `RESULTS.md`
- `TESTS.md`
- `META.json`

Use: `python3 tools/agentic/runlog_init.py --ticket ... --summary ...`
