# PROJECT_STATE REBUILD (Codex CLI)
You are Codex running inside the repo workspace (Codex CLI). Follow AGENTS.md instructions (they are injected automatically).
Your task is to (re)build a complete, accurate `project_state/` folder that makes this repository self-describing for humans and GPT-5.2 Pro.

IMPORTANT: Do not waste tokens on a big upfront plan. Just execute end-to-end and finish. (No intermediate “status updates” requirements.)

========================
GOAL
========================
Produce a fully populated `project_state/` directory that (1) is accurate (grounded in actual files), (2) is internally consistent, and (3) is optimized for LLM reading without direct repo access.

This is documentation/analysis work only. Preserve code behavior.

========================
SCOPE / EXCLUSIONS (HARD)
========================
- DO NOT recursively read huge directories or binary artifacts.
- Exclude from deep parsing:
  - .git/, .venv/, __pycache__/
  - reports/, data/ (only read small metadata files, registries, README, config; sample at most 1–2 small representative outputs)
  - experiments/**/outputs_*/ (only list + sample a tiny subset)
  - docs/agent_runs/** (do NOT parse every run; summarize index + last N runs only)
- You MAY list directory trees and file counts/sizes for excluded dirs.

========================
ACCURACY RULES
========================
- Do not guess. If uncertain, mark as “unclear” and cite the file path(s) that caused ambiguity.
- Prefer machine-derived indices (AST + import parsing) over manual extraction when possible.
- Every project_state doc must include a metadata header with:
  - generation timestamp
  - git SHA (HEAD)
  - branch
  - the command(s) used for generation

========================
DELIVERABLES
========================
Create/update ALL of the following files in `project_state/` (keep stable headings so diffs are clean):

1) ARCHITECTURE.md
2) MODULE_SUMMARIES.md
3) FUNCTION_INDEX.md
4) DEPENDENCY_GRAPH.md
5) PIPELINE_FLOW.md
6) DATAFLOW.md
7) EXPERIMENTS.md
8) CURRENT_RESULTS.md
9) RESEARCH_NOTES.md
10) OPEN_QUESTIONS.md
11) KNOWN_ISSUES.md
12) ROADMAP.md
13) CONFIG_REFERENCE.md
14) SERVER_ENVIRONMENT.md
15) TEST_COVERAGE.md
16) STYLE_GUIDE.md
17) CHANGELOG.md

ALSO create:
18) INDEX.md  (one-page navigation + “how to read this folder”)
19) _generated/ (directory)
    - _generated/repo_inventory.json (file list + roles + sizes)
    - _generated/symbol_index.json (AST-derived: file -> classes/functions + docstring first line)
    - _generated/import_graph.json (internal imports adjacency list)
    - _generated/make_targets.txt (Make targets extracted from Makefile)

========================
PROCEDURE (DO THIS)
========================
A) Collect metadata
- Record: git SHA, branch, timestamp, python version, installed deps if quickly available.
- Do NOT run heavy environment installs.

B) Fast repo scan
- Use `rg --files` to enumerate files quickly.
- Identify roots: src/, experiments/, tools/, tests/, docs/, configs, Makefile, README.

C) Build machine-derived indices (preferred)
- Write a small helper script (stdlib only) under tools/ (or run ad-hoc in a temp file) to:
  1) enumerate python files under src/, experiments/, tools/
  2) AST-parse each to extract:
     - top-level classes and functions
     - signatures (best-effort; ok if partial)
     - docstring first line
  3) parse imports to build internal dependency adjacency list
- Write results to `project_state/_generated/*.json`

D) Write/update the 17+2 markdown docs
- Use the generated JSON as ground truth for MODULE_SUMMARIES / FUNCTION_INDEX / DEPENDENCY_GRAPH.
- For PIPELINE_FLOW, extract entrypoints from:
  - Makefile targets
  - CLI scripts (argparse/typer/click)
  - experiments/*/run*.py
- For CURRENT_RESULTS / KNOWN_ISSUES:
  - Prefer summaries from PROGRESS.md + project_state itself + latest docs/agent_runs (last 3 runs)
  - Do NOT invent results; cite the artifact path(s).
- Keep each doc structured and scannable:
  - bullets, short paragraphs, tables where appropriate
  - lots of explicit file paths and “entrypoint command examples”
  - avoid giant walls of text

E) Consistency check (required)
- Verify every required file exists.
- Spot-check that:
  - key modules mentioned in ARCHITECTURE appear in MODULE_SUMMARIES
  - PIPELINE_FLOW entrypoints exist
  - CONFIG_REFERENCE keys point to real config files
- Fix contradictions before finishing.

F) Packaging for upload (artifact; do not commit zip)
- Create `docs/gpt_bundles/project_state_<timestamp>_<shortsha>.zip` containing:
  - project_state/
  - REPO_PLAN.md (if present)
  - docs/PLAN_OF_RECORD.md + docs/DOCS_AND_LOGGING_SYSTEM.md (if present)
  - PROGRESS.md
- Do NOT add the zip to git.

G) Run log + commit
- Create a run log directory:
  docs/agent_runs/<timestamp>_project_state_rebuild/
  with: PROMPT.md, COMMANDS.md, RESULTS.md, TESTS.md, META.json
- Update PROGRESS.md with a one-paragraph entry + paths to the zip.
- Commit only documentation + scripts needed for generation:
  - branch name: chore/project_state_refresh
  - commit message includes: “Rebuild project_state @ <shortsha>”
  - commit body includes Tests: (if any)

========================
TESTS (OPTIONAL)
========================
Only run quick commands that are safe:
- `make test-fast` if it is known to be fast; otherwise skip and note why.

========================
FINAL RESPONSE (your final assistant message)
========================
Return:
- files created/updated (paths)
- commands run (including zip command)
- where the zip artifact is located
- any exclusions made (what you didn’t parse deeply)
- known uncertainties you couldn’t resolve (with file references)
