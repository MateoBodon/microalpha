### Repo understanding

* **microalpha is a leakage‑safe, event‑driven backtesting + walk‑forward validation system** with a “research hygiene first” posture (strict chronology, t+1 execution semantics, explicit unsafe opt‑in).
* Core runtime is the classic pipeline: **DataHandler → Engine → Strategy → Portfolio → Broker/Execution → Artifacts/Reports** (events: Market/Signal/Order/Fill + LookaheadError).
* **Strategies live under `src/microalpha/strategies/`** (flagship cross‑sectional momentum plus breakout/mean‑reversion/market‑making variants).
* **Execution is pluggable** (TWAP/VWAP/impact models + LOB simulation w/ latency knobs); costs/borrow are treated as first‑class “headline” requirements (per Plan of Record).
* **Walk‑forward orchestration** runs a declared parameter grid on training folds and evaluates out‑of‑sample; there’s also a **final holdout mode** to prevent “tuning on holdout”.
* **Reporting is a subsystem, not an afterthought**: summary Markdown + plots, optional factor regressions, robustness/cost sensitivity, and inference (SPA + reality‑check/bootstrap).
* The repo **commits deterministic sample/public artifacts** (so README + tests can assert reproducibility) and supports **optional WRDS/CRSP** via local exports (`WRDS_DATA_ROOT`).
* There are **many repo guardrails**: run‑log validation, data‑policy scanning, leakage tests/unsafe banners, PnL integrity checks, baseline suite comparison reporting.
* Repo is **data‑heavy**: `data_sp500/` dominates the tracked file count (900+ CSVs) and is explicitly called out as something automation should avoid deep‑parsing.
* “AI memory” is expected to live in `project_state/` (AST‑derived indices + short docs), plus structured run logs under `docs/agent_runs/`.
* **Make targets** cover sample/WFV/report/test pipelines, plus WRDS‑guarded targets (`wfv-wrds`, `report-wrds`, etc.).
* There’s an **agentic scaffold** in progress (PROJECT.md, agent tooling, run log templates), but the captured repo map shows **consistency drift** between “tracked reality” and “project_state docs”.

---

### Current status

**What works:**

* Sample + walk‑forward + report flows exist and are first‑class (`make sample`, `make wfv`, `make report`, `make report-wfv`).
* WRDS workflows are implemented as **guarded** targets and documented as requiring local exports (consistent with “no licensed data in repo”).
* Major validity upgrades appear completed per `PROGRESS.md`: holdout evaluation mode, leakage guardrails + unsafe labeling, SPA robustness, PnL integrity checks, non‑degenerate constraints/diagnostics, baseline suite + comparison reporting, run‑log validator, data policy guardrails.

**What is missing:**

* **Repo-map consistency:** `project_state/` docs and AST indices are **not in sync** with the tracked file list (e.g., tracked modules like `src/microalpha/order_flow.py` / `src/microalpha/reporting/baselines.py` show up in `git_ls_files`, but do *not* appear in `project_state/_generated/symbol_index.json` / `MODULE_SUMMARIES.md`).
* **Operational docs are placeholder:** `project_state/BACKLOG.md`, `project_state/RUNBOOK.md`, and `docs/RUNBOOK.md` are stubbed with “(commands)” / “(bullets)”.
* **Agentic scaffold is not cleanly integrated** in the captured working tree: the generated `git_status.txt` shows a dirty tree with untracked items (including `tools/agentic/` and various `*.bak.*` backups).

**What is broken:**

* **Dependency graph generation is wrong:** `project_state/_generated/import_graph.json` records imports as `microalpha.microalpha.*` (systematic duplication), so `project_state/DEPENDENCY_GRAPH.md` is misleading as‑is.
* **Project-state metadata drift:** multiple `project_state/*.md` headers claim `generated_at` / `git_sha` from an older branch/commit while `_generated/git_head.txt` says `main` at a newer SHA — the bundle is a mixed snapshot rather than a coherent one.
* The captured `.gitignore` diff (in `_generated/git_diff.patch`) appears to add ignore rules for **`docs/agent_runs/` and `project_state/_generated/`**, which would block the repo’s established “commit run logs + generated indices” workflow going forward.

**Biggest risks (ranked):**

1. **Self‑misleading repo memory:** `project_state/` is currently inconsistent (stale/mixed), which will cause future agents/humans to make wrong decisions quickly.
2. **Evaluation validity regressions:** despite strong guardrails, this domain’s failure mode is subtle (leakage, survivorship, holdout contamination). Any drift here is high‑impact.
3. **WRDS reproducibility + licensing constraints:** workflows depend on local exports; easy for docs/results to become untestable by others and easy to accidentally cross the “don’t commit licensed data” line.
4. **Automation fragility from repo size:** large tracked datasets (`data_sp500/`) and many committed artifacts can make bundling, scanning, and CI slower/brittle unless consistently excluded/handled.
5. **Docs/results drift:** README/docs may cite run IDs/metrics that become stale unless tied to deterministic artifact checks (some exist, but consistency is not guaranteed).

---

### Best next tickets (ranked)

#### 1) **ticket-19_finish-agentic-scaffold-cleanup**

* **Goal (1 sentence):** Make the agentic scaffold *repo-consistent* by cleaning bootstrap leftovers and ensuring the intended agentic tooling + docs are properly tracked and usable.
* **Scope (what to change / not change):**

  * **Change:** clean up untracked backup files, remove or ignore bootstrap residue, ensure `tools/agentic/` and new “repo identity” docs are correctly included in version control, and reconcile `.gitignore` with the repo’s “commit run logs + project_state indices” practice.
  * **Do not change:** core backtesting logic, WRDS ETL logic, strategy behavior, or any numerical results.
* **Acceptance criteria (3–7 bullets):**

  * `git status --porcelain` is clean after the ticket (no stray `*.bak.*`, no `.gitignore.append`, no untracked `tools/agentic/`).
  * `.gitignore` does **not** prevent adding new `docs/agent_runs/**` or `project_state/_generated/**` updates (these are part of the repo’s audit workflow).
  * `python3 tools/agentic/project_state_refresh.py --zip` produces an updated `project_state.zip` without errors.
  * `make test-fast` passes.
  * `docs/DECISIONS.md` records what was cleaned/kept (so future agents understand why those paths are/aren’t ignored).
* **Test command(s):**

  * `python3 tools/agentic/project_state_refresh.py --zip`
  * `make test-fast`
* **Risk level:** **med**
* **Notes for Codex (pitfalls, files to touch):**

  * Pitfall: blindly applying “agentic-system-kit” `.gitignore` defaults will **break this repo’s audit trail** (it *intentionally* commits run logs + project_state indices).
  * Likely files: `.gitignore`, `AGENTS.md`, `docs/CODEX_SPRINT_TICKETS.md`, `PROGRESS.md`, `CHANGELOG.md`, plus the untracked `tools/agentic/` directory and any backup artifacts.
  * Do **not** touch/commit raw WRDS exports; keep only license‑safe logs/specs.

---

#### 2) **ticket-20_project-state-fidelity-refresh**

* **Goal (1 sentence):** Regenerate `project_state/` so it accurately reflects the current `main` tree and fix the dependency graph naming bug (`microalpha.microalpha.*`).
* **Scope (what to change / not change):**

  * **Change:** `tools/build_project_state.py` (import parsing/normalization), rerender `project_state/_generated/*` and derived docs (`MODULE_SUMMARIES.md`, `FUNCTION_INDEX.md`, `DEPENDENCY_GRAPH.md`, etc.).
  * **Do not change:** runtime engine/strategy logic; this is “repo memory correctness” only.
* **Acceptance criteria (3–7 bullets):**

  * `project_state/_generated/symbol_index.json` includes currently tracked modules that are missing today (e.g., `src/microalpha/order_flow.py`, `src/microalpha/reporting/baselines.py`).
  * `project_state/DEPENDENCY_GRAPH.md` contains **zero** occurrences of `microalpha.microalpha`.
  * The generated headers (`generated_at`, `git_sha`, `branch`) consistently match `_generated/git_head.txt` and `_generated/git_branch.txt`.
  * Generation explicitly avoids deep parsing of `data_sp500/` and other large data dirs (no runtime blowups).
  * `python3 tools/build_project_state.py` and `python3 tools/render_project_state_docs.py` run successfully.
* **Test command(s):**

  * `python3 tools/build_project_state.py`
  * `python3 tools/render_project_state_docs.py`
  * `make test-fast`
* **Risk level:** **low–med**
* **Notes for Codex (pitfalls, files to touch):**

  * Fixing import graph: ensure you’re not double‑prefixing package names when normalizing imports.
  * Validate against the *tracked* file list (e.g., from `git ls-files`) to ensure new modules aren’t silently skipped.
  * Files: `tools/build_project_state.py`, `tools/render_project_state_docs.py`, `project_state/_generated/*`, `project_state/*.md`.

---

#### 3) **ticket-21_replace-placeholders-runbook-backlog**

* **Goal (1 sentence):** Replace placeholder Runbook/Backlog files with short, accurate, repo‑specific guidance aligned to the Plan of Record.
* **Scope (what to change / not change):**

  * **Change:** `project_state/RUNBOOK.md`, `project_state/BACKLOG.md`, and (if it’s intended to exist) `docs/RUNBOOK.md`; keep them concise and command‑driven.
  * **Do not change:** any code or artifacts.
* **Acceptance criteria (3–7 bullets):**

  * No placeholder “(commands)” / “(bullets)” remains in these files.
  * Runbook includes the canonical “happy path” commands: setup, sample, WFV, report, tests, and WRDS‑guarded equivalents.
  * Backlog lists ~5–10 concrete next tasks with “why/impact” and how to test each (no vague bullets).
  * References (Make targets, scripts, configs) match the repo’s actual target names (from `project_state/_generated/make_targets.txt`).
  * `mkdocs build` succeeds (if the docs site consumes these pages); otherwise at least `make test-fast` remains green.
* **Test command(s):**

  * `make test-fast`
  * `mkdocs build` (if docs are wired to include the new/updated pages)
* **Risk level:** **low**
* **Notes for Codex (pitfalls, files to touch):**

  * Don’t invent commands—cross‑check against Make targets and CLI help.
  * Keep the backlog “small diffs, testable” (avoid mixing research goals with infra changes in a single item).

---

### If context is insufficient

Not required for this audit (the provided `project_state.zip` includes the repo file map, Make targets, git status/diff snapshot, and AST indices needed to identify the highest‑leverage inconsistencies and propose testable next tickets).
