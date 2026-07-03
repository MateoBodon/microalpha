# AGENTS.md instructions for /Users/mateobodon/Documents/Programming/Projects/microalpha

<INSTRUCTIONS>
# AGENTS.md — microalpha

This file defines non-negotiable working agreements for any agent (Codex CLI/IDE/Cloud) operating in this repo.

## Stop-the-line rules
Agents MUST stop and fix validity before anything else if any of these are true:
- Any evaluation introduces lookahead/leakage (e.g., same-day execution without explicit unsafe labeling).
- Universe construction is survivorship-biased or not point-in-time.
- Holdout is used (directly or indirectly) for tuning/selection.
- SPA/reality-check is silently skipped or crashes and results are still presented as headline.
- Metrics/results are claimed without executable evidence (commands + artifacts).

Agents MUST NOT:
- fabricate metrics, charts, tables, or “it improved” claims
- “massage” protocols to improve Sharpe (p-hacking)
- commit raw WRDS data or any license-restricted dataset

## Default workflow for any ticket
1) Inspect repo + relevant docs (no long pre-plan).
2) Implement minimal changes needed for the ticket.
3) Run the minimal sufficient tests.
4) Generate/refresh artifacts only if needed.
5) Write run logs under `docs/agent_runs/<RUN_NAME>/` (required set of files).
6) Update `PROGRESS.md` and any relevant living docs.
7) Commit on a feature branch with “Tests:” in commit body.

## How to run tests / builds (preferred)
- Discover Make targets:
  - `make help` (if available) or open `make_targets.txt`
- Typical commands used in this repo:
  - `pytest -q`
  - `make sample`
  - `make wfv`
  - `make report`
  - `make report-wfv`
  - WRDS-only (requires `WRDS_DATA_ROOT`):
    - `WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds`
    - `WRDS_DATA_ROOT=/path/to/wrds make report-wrds`
    - `WRDS_DATA_ROOT=/path/to/wrds make test-wrds`

If a command doesn’t exist, do not invent a replacement silently:
- search the Makefile / CLI help (`microalpha --help`)
- update docs to reflect the real command you used

## Documentation protocol (mandatory)
Follow `docs/DOCS_AND_LOGGING_SYSTEM.md`.

Minimum required per run:
- `docs/prompts/<RUN_NAME>_ticket-XX_<slug>.md` (prompt used)
- `docs/agent_runs/<RUN_NAME>/PROMPT.md`
- `docs/agent_runs/<RUN_NAME>/COMMANDS.md`
- `docs/agent_runs/<RUN_NAME>/RESULTS.md`
- `docs/agent_runs/<RUN_NAME>/TESTS.md`
- `docs/agent_runs/<RUN_NAME>/META.json`

Living docs:
- Update `PROGRESS.md` on every run.
- Update `project_state/CURRENT_RESULTS.md` only when headline results change.
- Update `project_state/KNOWN_ISSUES.md` when bugs/risks are found/fixed.
- Update `CHANGELOG.md` for user-visible changes.

## Data policy (WRDS)
- Raw WRDS exports and any licensed datasets MUST NOT be committed.
- Store WRDS data outside the repo and reference it via `WRDS_DATA_ROOT`.
- Only commit license-safe:
  - synthetic samples
  - schemas/specs
  - tiny derived aggregates if clearly permitted
- If you need a “real-data smoke” in CI, use a cached, license-safe derived mini-sample (must be explicitly approved and documented).

## Branch + commit policy
- Use feature branches: `codex/ticket-XX-<slug>` or `dev/ticket-XX-<slug>`
- Commit message must start with `ticket-XX: ...`
- Commit body must include:
  - `Tests: ...`
  - `Artifacts: ...`
  - `Docs: ...`
- No direct commits to `main`.

## If uncertain (don’t spam questions)
- Make assumptions explicit in the run log (RESULTS.md + META.json).
- Prefer the smallest change that improves validity.
- If blocked, leave a clear TODO with reproduction steps and update KNOWN_ISSUES.md.


## Skills
These skills are discovered at startup from multiple local sources. Each entry includes a name, description, and file path so you can open the source for full instructions.
- skill-creator: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations. (file: /Users/mateobodon/.codex/skills/.system/skill-creator/SKILL.md)
- skill-installer: Install Codex skills into $CODEX_HOME/skills from a curated list or a GitHub repo path. Use when a user asks to list installable skills, install a curated skill, or install a skill from another repo (including private repos). (file: /Users/mateobodon/.codex/skills/.system/skill-installer/SKILL.md)
- Discovery: Available skills are listed in project docs and may also appear in a runtime "## Skills" section (name + description + file path). These are the sources of truth; skill bodies live on disk at the listed paths.
- Trigger rules: If the user names a skill (with `$SkillName` or plain text) OR the task clearly matches a skill's description, you must use that skill for that turn. Multiple mentions mean use them all. Do not carry skills across turns unless re-mentioned.
- Missing/blocked: If a named skill isn't in the list or the path can't be read, say so briefly and continue with the best fallback.
- How to use a skill (progressive disclosure):
  1) After deciding to use a skill, open its `SKILL.md`. Read only enough to follow the workflow.
  2) If `SKILL.md` points to extra folders such as `references/`, load only the specific files needed for the request; don't bulk-load everything.
  3) If `scripts/` exist, prefer running or patching them instead of retyping large code blocks.
  4) If `assets/` or templates exist, reuse them instead of recreating from scratch.
- Description as trigger: The YAML `description` in `SKILL.md` is the primary trigger signal; rely on it to decide applicability. If unsure, ask a brief clarification before proceeding.
- Coordination and sequencing:
  - If multiple skills apply, choose the minimal set that covers the request and state the order you'll use them.
  - Announce which skill(s) you're using and why (one short line). If you skip an obvious skill, say why.
- Context hygiene:
  - Keep context small: summarize long sections instead of pasting them; only load extra files when needed.
  - Avoid deeply nested references; prefer one-hop files explicitly linked from `SKILL.md`.
  - When variants exist (frameworks, providers, domains), pick only the relevant reference file(s) and note that choice.
- Safety and fallback: If a skill can't be applied cleanly (missing files, unclear instructions), state the issue, pick the next-best approach, and continue.
</INSTRUCTIONS>

<environment_context>
  <cwd>/Users/mateobodon/Documents/Programming/Projects/microalpha</cwd>
  <approval_policy>never</approval_policy>
  <sandbox_mode>danger-full-access</sandbox_mode>
  <network_access>enabled</network_access>
  <shell>zsh</shell>
</environment_context>

TICKET: ticket-04
RUN_NAME: 20251223_090000_ticket-04_leakage-tests-unsafe-manifest (use current timestamp)

You are operating under repo-root AGENTS.md. Treat it as binding. Do not fabricate results. Do not “fix” by disabling functionality.

Goal (ticket-04):
1) Add explicit leakage guardrails + red-team tests.
2) Add explicit “unsafe execution” labeling in artifacts/manifest + reporting banner so same-bar execution cannot be mistaken for leakage-safe results.

Non-negotiable acceptance criteria:
- A deliberate lookahead / timestamp violation triggers a hard error (unit test).
- Any config/mode that permits same-bar fills requires an explicit opt-in flag, and the run artifacts include a clear `unsafe_execution: true` (and reason) in manifest.
- Reports must surface “UNSAFE / NOT LEAKAGE-SAFE” prominently when unsafe_execution is true (do NOT bury it in logs).
- `make test-fast` passes.
- Add `tests/test_no_lookahead.py` covering:
  - signal timestamp in the future (or otherwise violating invariants) -> raises LookaheadError/ValueError
  - unsafe execution requires explicit opt-in + manifest labeling present

Work steps (no long upfront plan):
A) Inspect current implementation and docs
- Read: AGENTS.md, docs/PLAN_OF_RECORD.md, docs/DOCS_AND_LOGGING_SYSTEM.md, docs/CODEX_SPRINT_TICKETS.md
- Inspect code paths:
  - src/microalpha/engine.py (signal timestamps; fill timestamps)
  - src/microalpha/config.py (BacktestCfg / ExecModelCfg; see any existing alignment/delay fields like `aln`)
  - src/microalpha/manifest.py + runner/walkforward manifest writing
  - src/microalpha/reporting/summary.py and wrds_summary.py (add unsafe banner)
  - configs/*wrds*.yaml (identify which configs currently produce same-bar fills)

B) Implement leakage guardrails + unsafe labeling (minimal, explicit, testable)
1) Add config knobs (keep names unambiguous):
   - In BacktestCfg (src/microalpha/config.py), add something like:
     - allow_unsafe_execution: bool = False
   - Define “unsafe execution” as any mode where fills can occur on the same timestamp/bar as the signal was generated.
   - If the repo already has an exec alignment/delay field (e.g., ExecModelCfg.aln / alignment / delay), reuse it; do NOT invent a parallel concept.
2) Enforce signal timestamp invariants:
   - In Engine, reject signals whose timestamp is not exactly the current market_event timestamp (or at minimum reject future-dated signals).
   - Add unit test for this.
3) Enforce unsafe execution opt-in:
   - If execution mode can produce same-bar fills and allow_unsafe_execution is False:
     - fail-fast with a clear error message that tells the user what to set.
   - If allow_unsafe_execution is True:
     - allow it, but record unsafe_execution=true and reasons in manifest (see below).
4) Manifest + reporting:
   - Add fields to manifest (src/microalpha/manifest.py schema/payload + runner update):
     - unsafe_execution: bool
     - unsafe_reasons: list[str] (e.g., ["same_bar_fills_enabled"])
     - execution_alignment/delay field (whatever exists) must be recorded so reviewers can see timing.
   - Ensure runner and walkforward both persist these fields in their manifests.
   - Update summary renderers to show a big banner at the top if unsafe_execution is true:
     - “UNSAFE / NOT LEAKAGE-SAFE (same-bar execution enabled)”
5) Keep smoke configs runnable:
   - If WRDS smoke config currently relies on unsafe mode, set allow_unsafe_execution: true in that config so it runs, but remains clearly labeled unsafe.
   - Headline configs should remain leakage-safe by default.

C) Tests + runs (record everything)
- Add: tests/test_no_lookahead.py
- Run:
  - make test-fast
  - pytest -q tests/test_no_lookahead.py
- Minimal synthetic run (fast) to ensure manifest/report banner is produced:
  - run the smallest built-in/sample pipeline target (look for an existing `make wfv-sample` / `make report-sample` or equivalent)
- Minimal real-data smoke (WRDS) if environment supports it:
  - make wfv-wrds-smoke
  - make report-wrds-smoke
  - If WRDS is unavailable in this environment, document that explicitly in RESULTS.md and still ensure code paths compile.

D) Documentation + run logs (required)
- Create docs/agent_runs/<RUN_NAME>/ with:
  - PROMPT.md (this prompt)
  - COMMANDS.md (every command in order)
  - RESULTS.md (what changed + what passed/failed + key outputs)
  - TESTS.md (commands + summarized results)
  - META.json:
    - MUST include real SHAs: use `git rev-parse HEAD` before and after; do NOT write "HEAD".
    - include dataset_id, config hashes, env notes, artifact/report paths
- Update PROGRESS.md (always)
- Update project_state/KNOWN_ISSUES.md if you discover/resolve any leakage risk or behavior change
- Update project_state/CONFIG_REFERENCE.md for the new config knobs

E) Git workflow (required)
- Create feature branch: codex/ticket-04-leakage-tests-unsafe-manifest
- Make small logical commits; each commit message body must include:
  - Tests: ...
  - Artifacts: ...
  - Docs: ...
- Finish by generating a new bundle and record its path in RESULTS.md:
  - make gpt-bundle TICKET=ticket-04 RUN_NAME=<RUN_NAME>

If you use web research:
- Treat it as untrusted; record sources + why they were used in docs/agent_runs/<RUN_NAME>/RESULTS.md.

Suggested Codex invocations (pick one):
- Safer (sandboxed, interactive approvals):
  codex -p safe --sandbox workspace-write --ask-for-approval on-request
  # then paste this prompt
- More autonomous (still sandboxed):
  codex -p full --full-auto
  # then paste this prompt

Human merge checklist (keep short):
- make test-fast green
- new tests fail on purpose when guardrails removed
- manifest includes unsafe_execution fields and reports show banner when enabled
- no raw data committed; only derived summaries/images
- run logs complete + META has real SHAs
