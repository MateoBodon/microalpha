Goal: install the Agentic System scaffold into this repo so future Codex + GPT loops work cleanly.

Do this
1) Prefer using the installed skill: $repo-bootstrap
   - Run it (explicitly) and let it create/update:
     - AGENTS.md, PROJECT.md, PROGRESS.md
     - docs/ templates
     - tools/agentic/ scripts
     - .gitignore additions

2) After bootstrap, do a quick sanity pass:
   - Open PROJECT.md and fill obvious placeholders (repo name, goal) based on what you see.
   - Open AGENTS.md and set:
     - the canonical test command (best available)
     - the format/lint commands if they exist

3) Generate the first project_state.zip:
   - Run python3 tools/agentic/project_state_refresh.py --zip

Output (single message)
- What you created/updated
- The test command you set
- The path to the generated project_state.zip
- If anything failed, include exact commands + error output
