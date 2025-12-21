# Commands

- ls
- sed -n '1,200p' AGENTS.md
- sed -n '1,200p' Plan.md
- git status --short --branch
- rg --files
- git rev-parse HEAD
- git rev-parse --abbrev-ref HEAD
- date -u '+%Y-%m-%dT%H:%M:%SZ'
- python3 --version
- mkdir -p tools project_state/_generated
- python3 tools/build_project_state.py
- python3 tools/render_project_state_docs.py
- date -u '+%Y-%m-%dT%H-%M-%SZ'
- mkdir -p docs/agent_runs/2025-12-20T21-31-14Z_project_state_rebuild
- zip -r docs/gpt_bundles/project_state_2025-12-20T21-31-14Z_b128e4af.zip project_state PROGRESS.md
- make test
- (various sed/ls/cat/rg reads across README, Makefile, docs, configs, tests, artifacts)
