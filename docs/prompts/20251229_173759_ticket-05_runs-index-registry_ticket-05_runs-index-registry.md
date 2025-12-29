TICKET: ticket-05
RUN_NAME: <SET_THIS_TO_UTC_TIMESTAMP>_ticket-05_runs-index-registry
BRANCH: codex/ticket-05-runs-index-registry

You are Codex working inside the microalpha repo.

Hard requirements (binding):
- Follow AGENTS.md stop-the-line rules. Do NOT fabricate results or “it works” claims.
- Follow docs/DOCS_AND_LOGGING_SYSTEM.md: you MUST write a complete run log under docs/agent_runs/<RUN_NAME>/ with:
  PROMPT.md, COMMANDS.md, RESULTS.md, TESTS.md, META.json.
- Do not ask for a long plan. Inspect → implement → test → document.
- Tests: at minimum run `make test-fast` (note: it now includes run-log validation) and record outputs in TESTS.md.
- Data policy: do NOT commit raw WRDS data or anything license-restricted. If in doubt, exclude and document.

Ticket goal (from docs/CODEX_SPRINT_TICKETS.md #ticket-05):
- Implement an experiment registry that scans artifact manifests and writes a deterministic runs index CSV:
  output path: reports/summaries/runs_index.csv
- Make the index stable/deterministic for sample runs in CI/local.
- Add docs that explicitly state “do not cherry-pick” and define what qualifies as a headline run.

Suggested Codex invocation (human runs one of these before pasting this prompt):
- Safer interactive: `codex --sandbox workspace-write --ask-for-approval on-request`
- More autonomy (still sandboxed): `codex --full-auto`
(Do NOT use --yolo.)

Implementation steps (do these in order; no big upfront plan):
1) Create the run log directory and start logging immediately:
   - mkdir -p docs/agent_runs/<RUN_NAME>/
   - Write docs/agent_runs/<RUN_NAME>/PROMPT.md with the exact text of this prompt.
   - Start docs/agent_runs/<RUN_NAME>/COMMANDS.md and append every command you execute, in order.

2) Inspect existing artifact layout and manifest schema:
   - Find existing manifest files (likely under artifacts/<experiment>/<run_id>/manifest.json).
   - Identify the minimal stable fields we can rely on (run_id, git_sha, dataset_id, config hash/paths, date range, headline metrics if present).

3) Implement the runs index builder:
   - Add/extend: src/microalpha/manifest.py (helpers to load and validate manifest.json safely).
   - Add a new script: scripts/build_runs_index.py
     Requirements:
     - Scans manifests under artifacts/ with a pattern that matches real structure (support both artifacts/*/manifest.json and artifacts/*/*/manifest.json; detect automatically).
     - Deterministic output:
       * stable column order
       * stable row ordering (sort by [experiment, run_id] or [run_id])
       * stable formatting (no timestamps in file generation, consistent float formatting)
     - Robust behavior:
       * If a manifest is missing non-critical fields, leave blanks but do not crash.
       * If a manifest is invalid JSON, emit a clear error and exit non-zero (this prevents silently skipping failures).
     - Write CSV to reports/summaries/runs_index.csv.

4) Add tests:
   - Add tests/test_runs_index.py using tmp_path fixtures:
     * Create a fake artifacts tree with 2–3 manifest.json files in different subfolders.
     * Ensure the script/library produces the expected CSV rows in deterministic order.
     * Ensure invalid JSON causes a non-zero exit (or raises a clear exception) and is asserted.
   - Tests must not require WRDS or large data.

5) Wire into Makefile / reporting (minimal, do not overbuild):
   - Add a Makefile target, e.g. `runs-index:` that runs the script to produce reports/summaries/runs_index.csv.
   - Optionally include it in an existing “report” target if one exists, but don’t risk breaking workflows.

6) Documentation: “no cherry-pick” policy
   - Add docs/RUN_REGISTRY.md (or update an existing doc) explaining:
     * what the runs index is
     * how to regenerate it
     * explicit anti-cherry-pick rule: headline claims must reference the holdout run(s) and must be accompanied by the runs_index.csv
     * what disqualifies a run from headline (e.g., spa_status != ok, unsafe execution, missing costs, etc.)
   - Update PROGRESS.md with a ticket-05 entry linking the run log.
   - If this changes reporting outputs, update project_state/CURRENT_RESULTS.md accordingly (only if materially relevant).

7) Generate the artifact output for this ticket:
   - Run the runs index builder on the repo’s sample artifacts (and WRDS artifacts if present locally, but do NOT add WRDS outputs if they aren’t already license-safe).
   - Ensure reports/summaries/runs_index.csv exists and is committed.

8) Run minimal tests (record everything):
   - `make test-fast`
   - `python3 -m compileall tools scripts src` (if fast)
   - `python3 scripts/build_runs_index.py --help` (if you added argparse)
   - `python3 scripts/build_runs_index.py` (or via make target) and verify the CSV is produced.

9) Run log finalization:
   - Fill docs/agent_runs/<RUN_NAME>/RESULTS.md:
     * what changed
     * where the new runs_index.csv is
     * any limitations
   - Fill TESTS.md with commands and key outputs.
   - Fill META.json with required schema fields (see docs/DOCS_AND_LOGGING_SYSTEM.md).
   - Ensure `make validate-runlogs` passes.

10) Git workflow:
   - Create feature branch: codex/ticket-05-runs-index-registry
   - Make small logical commits.
   - Every commit message body must include:
     - Tests run:
     - Artifacts/logs:
     - Docs updated:
   - Do NOT merge unless explicitly told by the human.

11) Bundle at end (mandatory):
   - `make gpt-bundle TICKET=ticket-05 RUN_NAME=<RUN_NAME>`
   - Record the bundle path in docs/agent_runs/<RUN_NAME>/RESULTS.md.

Stop condition:
- You are done ONLY when:
  - reports/summaries/runs_index.csv exists and is deterministic (tests prove it),
  - docs updated for “no cherry-pick” policy,
  - run log complete (PROMPT/COMMANDS/RESULTS/TESTS/META),
  - make test-fast passes,
  - bundle created and path recorded.
