ls
sed -n '1,200p' PROJECT.md
sed -n '1,200p' AGENTS.md
sed -n '1,200p' PROGRESS.md
sed -n '1,200p' docs/DOCS_AND_LOGGING_SYSTEM.md
ls project_state
date -u +"%Y%m%d_%H%M%S"
git rev-parse HEAD
git rev-parse --abbrev-ref HEAD
python3 --version
uname -a
python3 tools/agentic/project_state_refresh.py --zip
sed -n '1,200p' project_state/ARCHITECTURE.md
sed -n '1,80p' project_state/_generated/INDEX.md
ls project_state/_generated
sed -n '1,200p' project_state/RUNBOOK.md
sed -n '1,200p' project_state/README.md
sed -n '1,200p' project_state/INDEX.md
sed -n '1,200p' project_state/PIPELINE_FLOW.md
sed -n '1,200p' project_state/CURRENT_RESULTS.md
sed -n '1,200p' project_state/KNOWN_ISSUES.md
sed -n '1,200p' project_state/ROADMAP.md
sed -n '1,200p' project_state/BACKLOG.md
sed -n '1,200p' project_state/OPEN_QUESTIONS.md
sed -n '1,160p' project_state/RESEARCH_NOTES.md
sed -n '1,200p' Makefile
sed -n '1,200p' README.md
sed -n '1,260p' tools/render_project_state_docs.py
rg -n "ARCHITECTURE|Runbook" -n tools/render_project_state_docs.py
rg -n "def render_architecture" -n tools/render_project_state_docs.py
sed -n '260,360p' tools/render_project_state_docs.py
rg -n "RUNBOOK" tools/render_project_state_docs.py
sed -n '1,220p' tools/build_project_state.py
apply_patch (update project_state/RUNBOOK.md)
apply_patch (update project_state/BACKLOG.md)
apply_patch (update project_state/KNOWN_ISSUES.md)
apply_patch (update project_state/ROADMAP.md)
apply_patch (update project_state/OPEN_QUESTIONS.md)
python3 tools/agentic/project_state_refresh.py --zip
sed -n '1,200p' /home/codex/.codex/skills/project-state-refresh/SKILL.md
apply_patch (update PROGRESS.md)
date -u +"%Y-%m-%dT%H:%M:%SZ"
RUN_NAME="20260126_000243_ticket-00_project-state-refresh"; mkdir -p "docs/agent_runs/${RUN_NAME}"
RUN_NAME="20260126_000243_ticket-00_project-state-refresh"; cat <<'EOF' > "docs/agent_runs/${RUN_NAME}/PROMPT.md"
RUN_NAME="20260126_000243_ticket-00_project-state-refresh"; cat <<'EOF' > "docs/prompts/${RUN_NAME}.md"
RUN_NAME="20260126_000243_ticket-00_project-state-refresh"; cat <<'EOF' > "docs/agent_runs/${RUN_NAME}/RESULTS.md"
RUN_NAME="20260126_000243_ticket-00_project-state-refresh"; cat <<'EOF' > "docs/agent_runs/${RUN_NAME}/TESTS.md"
RUN_NAME="20260126_000243_ticket-00_project-state-refresh"; cat <<'EOF' > "docs/agent_runs/${RUN_NAME}/META.json"
git status --porcelain -uall
rg -n "docs/prompts" .gitignore
rg -n "_bundles" .gitignore
date -u +"%Y-%m-%dT%H:%M:%SZ"
apply_patch (update docs/agent_runs/20260126_000243_ticket-00_project-state-refresh/META.json)
python3 tools/agentic/project_state_refresh.py --zip
apply_patch (update PROGRESS.md)
apply_patch (update docs/agent_runs/20260126_000243_ticket-00_project-state-refresh/RESULTS.md)
date -u +"%Y-%m-%dT%H:%M:%SZ"
apply_patch (update docs/agent_runs/20260126_000243_ticket-00_project-state-refresh/META.json)
git status --porcelain -uall
date -u +"%Y-%m-%dT%H:%M:%SZ"
apply_patch (update docs/agent_runs/20260126_000243_ticket-00_project-state-refresh/META.json)
python3 tools/agentic/project_state_refresh.py --zip --out docs/_bundles/project_state_20260126_001303.zip
date -u +"%Y-%m-%dT%H:%M:%SZ"
apply_patch (update docs/agent_runs/20260126_000243_ticket-00_project-state-refresh/META.json)
