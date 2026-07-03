You are setting up this repo to follow the **Agentic System Kit v2** workflow.

## Objectives
1) Install/refresh the scaffold safely (without clobbering existing repo docs).
2) Ensure tracking/logging structure exists:
   - `docs/agent_runs/` (tracked)
   - `docs/tickets/`
   - `artifacts/_local/` (ignored; README tracked)
   - `reports/_runs/` (ignored; README tracked)
3) Ensure helper scripts exist under `tools/agentic/`.

## Steps
1) Run the repo bootstrap skill in safe mode (tools-only refresh):
   - `python3 ~/.codex/skills/repo-bootstrap/scripts/bootstrap_repo.py --force-tools`
   (If CODEX_HOME is set, use `/skills/...`.)

2) Verify `.gitignore` contains the Agentic System Kit block and that it does **NOT** ignore `docs/agent_runs/`.

3) Create an initial project-state bundle:
   - `python3 tools/agentic/project_state_refresh.py --zip`
   Record the output path in `PROGRESS.md`.

## Guardrails
- Do not overwrite existing `AGENTS.md`, `PROJECT.md`, `PROGRESS.md` unless explicitly instructed.
- Do not introduce new top-level directories beyond the canonical zones in `TRACKING_POLICY.md`.

<environment_context>
  <cwd>/home/codex/repos/microalpha</cwd>
  <shell>bash</shell>
</environment_context>

<skill>
<name>repo-bootstrap</name>
<path>/home/codex/.codex/skills/repo-bootstrap/SKILL.md</path>
---
name: repo-bootstrap
description: Bootstrap a repo with the Agentic System Kit scaffold (docs/logging/tracking policy + tools/agentic).
metadata:
  short-description: Install/refresh scaffold + .gitignore + helper scripts
---

# repo-bootstrap

## Purpose
Install (or refresh) the **Agentic System Kit** scaffold into the current git repository so agent work is consistent across projects.

Key deliverables enabled by the scaffold:
- Standard run logs under `docs/agent_runs/`
- Review bundles under `artifacts/_local/gpt_bundles/`
- Project-state bundles under `artifacts/_local/project_state_bundles/`

## What to do

1) Determine the repo root (git).

2) Run the bootstrap script.

Safe default (recommended):
- `python3 ~/.codex/skills/repo-bootstrap/scripts/bootstrap_repo.py --force-tools`

Notes:
- This updates only `tools/agentic/*` while leaving repo-specific memory/docs alone.
- If `CODEX_HOME` is set, use `$CODEX_HOME/skills/...` instead of `~/.codex/...`.

For a brand new repo, you can omit flags:
- `python3 ~/.codex/skills/repo-bootstrap/scripts/bootstrap_repo.py`

If you truly want to reset everything to the kit templates:
- `python3 ~/.codex/skills/repo-bootstrap/scripts/bootstrap_repo.py --force`

3) (Optional) Generate a first project-state bundle:
- `python3 tools/agentic/project_state_refresh.py --zip`

## Output
- List of created/updated files
- (Optional) The path to the created `project_state_*.zip`
</skill>
