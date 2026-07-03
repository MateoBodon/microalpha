# tools/agentic

Small, deterministic helper scripts that standardize the agentic workflow across repos.

## Core scripts

- `runlog_init.py`  
  Creates a new `docs/agent_runs/<RUN_NAME>/` folder with standard files:
  `PROMPT.md`, `COMMANDS.md`, `RESULTS.md`, `TESTS.md`, `META.json`.

- `gpt_bundle.py`  
  Creates a zip bundle under `artifacts/_local/gpt_bundles/` containing:
  - `DIFF.patch` (range diff)
  - `REPO_SNAPSHOT.md` (tracked-file inventory summary)
  - git status/log/stats
  - key docs (`AGENTS.md`, `PROJECT.md`, `PROGRESS.md`, …)
  - ticket file (best-effort)
  - run log folder (best-effort)

- `project_state_refresh.py`  
  Ensures `project_state/` exists and emits `project_state/_generated` git metadata.
  Optionally creates a `project_state_*.zip` under `artifacts/_local/project_state_bundles/`.

- `repo_snapshot.py`  
  Generates a lightweight repo snapshot markdown file at `docs/_generated/repo_snapshot.md`.

- `ticket_new.py`  
  Optional: create a new ticket file from a local template.

- `validate_runlog.py`  
  Optional: validate that a run log folder has the required files.

## Philosophy

- These scripts never call an LLM.
- They should be safe to run repeatedly.
- Prefer adding options rather than creating repo-specific forks.
