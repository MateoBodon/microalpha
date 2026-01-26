Create or update `project_state/` so that:
- A fresh GPT session can understand the repo quickly.
- The docs stay accurate and practical.

Preferred:
- Invoke skill **$project-state-refresh**.

Fallback:
- Run `python3 tools/agentic/project_state_refresh.py --zip`

Then:
- Ensure `project_state/` contains accurate architecture + runbook info (edit files as needed).
- Keep it high-signal: what exists, how to run, where results live, what’s broken, what’s next.

Output:
- What you updated
- The path to the created `project_state.zip`

<environment_context>
  <cwd>/home/codex/repos/microalpha</cwd>
  <shell>bash</shell>
</environment_context>

<skill>
<name>project-state-refresh</name>
<path>/home/codex/.codex/skills/project-state-refresh/SKILL.md</path>
---
name: project-state-refresh
description: Generate/update project_state/ and produce project_state.zip for GPT recentering.
metadata:
  short-description: Update project_state docs + zip bundle
---

# project-state-refresh

## Purpose
Produce a **fresh, uploadable** `project_state.zip` that lets a new GPT session understand the repo quickly.

## Preferred execution
Run the repo-local script (if scaffold exists):
- `python3 tools/agentic/project_state_refresh.py --zip`

If the repo-local script doesn't exist yet:
- Run `$repo-bootstrap` first, then re-run.

## Output
Print the path to the created `project_state.zip`.
</skill>
