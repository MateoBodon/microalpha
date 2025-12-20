# Prompt

PROJECT_STATE REBUILD (Codex CLI)

Task: (re)build a complete, accurate `project_state/` folder that makes this repository self-describing for humans and GPT-5.2 Pro.

Key requirements:
- Create/update all required project_state docs (17 + INDEX) and `_generated` JSON indices.
- Include metadata headers with timestamp, git SHA, branch, and commands.
- Use AST-based indexing for symbols/imports.
- Summarize pipeline entrypoints, configs, results, and known issues without guessing.
- Respect exclusions for large directories and avoid deep parsing of data/artifacts.
- Create zip bundle under `docs/gpt_bundles/`.
- Create run log under `docs/agent_runs/<timestamp>_project_state_rebuild/`.
- Update `PROGRESS.md` with entry referencing zip path.
- Commit documentation + scripts (per task plan) and avoid heavy tests.

See original user instruction in chat for full detail.
