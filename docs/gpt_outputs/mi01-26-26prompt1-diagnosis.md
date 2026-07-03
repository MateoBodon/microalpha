### 1) What this repo is

* **Purpose:**
  `microalpha` is a leakage-safe, deterministic, event-driven backtesting + walk-forward validation system that produces audit-grade artifacts (manifests, metrics, trades, reports), with optional “real data” runs via local WRDS/CRSP exports. (See `PROJECT.md` + `project_state/ARCHITECTURE.md`.)

* **Current state (as of the uploaded snapshot):**

  * The system’s core pipeline is clearly defined as:
    `DataHandler -> Engine -> Strategy -> Portfolio -> Broker -> Execution -> Artifacts` (`project_state/ARCHITECTURE.md` L15–L24).
  * It has a substantial test suite (64 test modules) and explicitly reports **~78% coverage** in the bundled suites (`project_state/TEST_COVERAGE.md`, last line).
  * The **only “officially surfaced” performance metrics in this snapshot** are in `project_state/CURRENT_RESULTS.md`:

    * **Sample flagship (single run):** Sharpe(HAC) **-0.66**, MaxDD **17.26%** (`project_state/CURRENT_RESULTS.md` L15–L20).
    * **Sample walk-forward:** Sharpe(HAC) **0.22**, MaxDD **34.79%** (`project_state/CURRENT_RESULTS.md` L22–L27).
    * **Sample holdout WFV:** Holdout Sharpe(HAC) **1.29**, Holdout MaxDD **9.36%** (`project_state/CURRENT_RESULTS.md` L29–L33).
    * **WRDS (real-data pipeline):** Sharpe_HAC **0.27**, MaxDD **3.41%**, Reality Check p **0.988**, SPA p **0.015** (`project_state/CURRENT_RESULTS.md` L37–L47).
      This is the best “real data” evidence explicitly summarized in the snapshot.
  * “Resume metrics refreshed” is explicitly claimed for Ticket-24 / the WRDS rerun (`project_state/CURRENT_RESULTS.md` L66–L69), but the resume snippet you pasted does **not** match the WRDS snapshot numbers in `CURRENT_RESULTS.md`.

* **Main risks / unknowns:**

  * **Your resume performance line (Sharpe 0.46 / MaxDD 7.9% / CAGR 6.7% / bootstrap p=0.23)** is **not corroborated anywhere in the uploaded snapshot** (it does not appear in `project_state/CURRENT_RESULTS.md`, and a grep for `0.46` in this snapshot returns nothing). That means: *as of this snapshot*, it’s not “audit-linked” to a run_id + artifact dir.
  * The “real data” headline numbers we *can* point to right now (WRDS Sharpe_HAC 0.27, MaxDD 3.41%) are **credibility-strong** (because they include SPA + reality-check outputs in the documented pipeline), but **not particularly “impressive” on Sharpe** if you’re trying to wow someone with pure performance.
  * **The snapshot indicates workflow drift / hygiene issues** (dirty worktree, backup files, unignored scratch outputs), which can undermine “audit-grade” claims if not cleaned up (`project_state/_generated/git_status.txt`).
  * **WRDS dataset versioning/schema is still an explicit open question**, which directly impacts the “real data metrics” story (`project_state/OPEN_QUESTIONS.md`, first bullet; `project_state/BACKLOG.md` items 1–2).

**Resume-metrics reality check (based on what’s in this snapshot):**

* Your *engineering* bullet is strong and looks consistent with the repo’s documented design and test posture (t+1, walk-forward, bootstrap/SPA, CI/tests).
* Your *performance* bullet (Sharpe 0.46, MaxDD 7.9%, CAGR 6.7%, bootstrap p=0.23):

  * Likely refers to the **public mini-panel config** (`configs/wfv_flagship_public.yaml` exists per `project_state/CONFIG_REFERENCE.md`), but those results are **not currently recorded** in `project_state/CURRENT_RESULTS.md`.
  * Also: “bootstrap p=0.23 (no evidence of overfit)” is directionally OK, but slightly risky wording. A safer phrasing is: “bootstrap reality-check p=0.23” (and let the reader infer), or “not statistically significant at conventional levels.”

---

### 2) What’s broken or drifting

* **Docs drift: `docs/RUNBOOK.md` is a placeholder, while the real run instructions live in `project_state/RUNBOOK.md`.**
  Evidence: `docs/RUNBOOK.md` contains “- (commands)” placeholders (`docs/RUNBOOK.md` L5–L15), whereas `project_state/RUNBOOK.md` contains the actual canonical commands (e.g., `make test-fast`, WRDS commands, etc.).
* **Docs drift: `docs/NOW.md` is also a placeholder.**
  Evidence: `docs/NOW.md` is still templated with “- (bullets)” (`docs/NOW.md` L8–L15).
* **Resume metrics are not “repo-linked” in this snapshot.**
  Evidence: `project_state/CURRENT_RESULTS.md` lists sample + WRDS snapshots but contains no numbers matching your resume snippet (e.g., no Sharpe 0.46 / MaxDD 7.9 / CAGR 6.7). The only WRDS snapshot shown is Sharpe_HAC 0.27, MaxDD 3.41% (`project_state/CURRENT_RESULTS.md` L39–L46).
* **Project-state snapshot is not commit-consistent across its own files.**
  Evidence:

  * `project_state/ARCHITECTURE.md` was generated at git_sha `4d08d182...` (`project_state/ARCHITECTURE.md` L1–L4),
  * `project_state/CURRENT_RESULTS.md` is at git_sha `e76eb4d...` (`project_state/CURRENT_RESULTS.md` L1–L4),
  * `project_state/_generated/git_head.txt` reports HEAD as `31fe5532...` (`project_state/_generated/git_head.txt` L1).
    This makes it easy for “current results” to silently drift from “current code”.
* **Tracking policy / repo hygiene drift: lots of untracked backup files and a scratch output dir that appears not ignored.**
  Evidence: `project_state/_generated/git_status.txt` shows many untracked `*.bak.*` and `*.append*` files (`git_status.txt` L12–L75), and also shows `?? reports/_runs/` (`git_status.txt` L54) even though `TRACKING_POLICY.md` explicitly says `reports/_runs/` should be ignored (see `TRACKING_POLICY.md`, “Ignored (local-only)” section).
* **Tracking-policy adoption is incomplete in the underlying repo state.**
  Evidence: `project_state/_generated/git_status.txt` shows `?? TRACKING_POLICY.md` (`git_status.txt` L28), implying the policy file existed but was untracked at snapshot time. That’s a “policy exists but isn’t yet enforced” smell.
* **Known dependency risk for “real data”: WRDS is blocked without local exports and a correct `WRDS_DATA_ROOT`.**
  Evidence: `project_state/KNOWN_ISSUES.md` first bullet; and `project_state/CURRENT_RESULTS.md` references `WRDS_DATA_ROOT=/srv/data/wrds/wrds` (`CURRENT_RESULTS.md` L68–L75).

---

### 3) What to do next (tickets)

#### Ticket 1

* **Filename:** `docs/tickets/TICKET-27_refresh-public-mini-panel-resume-metrics.md`
* **Goal (one sentence):** Reproduce (or invalidate) the resume’s “OOS Sharpe 0.46 / MaxDD 7.9% / CAGR 6.7% / bootstrap p=0.23” by rerunning the **public mini-panel** config and publishing a fully linked, audit-grade summary.
* **Why now (leverage):** Your current resume performance line is not traceable to a run in the snapshot, and public data is the fastest, license-safe way to get a reproducible “numbers” line without WRDS friction.
* **Acceptance criteria (checklist):**

  * [ ] A new run log exists under `docs/agent_runs/<RUN_NAME>/` with all required files (`TRACKING_POLICY.md` “Run logging contract”).
  * [ ] Run is executed with the canonical public config: `configs/wfv_flagship_public.yaml` (listed in `project_state/CONFIG_REFERENCE.md`).
  * [ ] Artifacts are written to an **ignored** run-scoped location (e.g., `artifacts/_local/<RUN_ID>/...`) and the run log links to them.
  * [ ] A small curated summary is promoted into `docs/artifacts/resume/public/<RUN_ID>/` (e.g., metrics JSON + a short MD snippet).
  * [ ] `project_state/CURRENT_RESULTS.md` is updated to include a “Public mini-panel” subsection with the exact run_id and headline metrics.
  * [ ] If the new metrics differ materially from the resume snippet, a “before/after” note is written (in the run’s `RESULTS.md`) and the resume snippet is updated accordingly.
* **Suggested test plan:**

  * `make test-fast`
  * `make check-data-policy`
  * Run the public WFV + report commands (record exact commands in the run log)
  * `make validate-runlogs`

#### Ticket 2

* **Filename:** `docs/tickets/TICKET-28_refresh-wrds-resume-metrics-with-dataset-id.md`
* **Goal (one sentence):** Refresh the “real data” (WRDS) headline run and make it resume-credible by pinning a **dataset_id/schema version** and surfacing it in manifests + resume summaries.
* **Why now (leverage):** You already have WRDS results summarized (`project_state/CURRENT_RESULTS.md` L37–L47), but without a pinned dataset version, “real-data metrics” are fragile and hard to defend in interviews/reviews.
* **Acceptance criteria (checklist):**

  * [ ] `docs/wrds.md` (or equivalent) clearly defines the canonical WRDS export layout, schema/version, and the expected `WRDS_DATA_ROOT` shape (this is explicitly called out as missing in `project_state/BACKLOG.md` item 2 and `project_state/OPEN_QUESTIONS.md`).
  * [ ] `META.json` for the WRDS resume run includes `dataset_id` that matches the documented versioning scheme (`docs/DOCS_AND_LOGGING_SYSTEM.md` “META.json” template).
  * [ ] `src/microalpha/manifest.py` (or the manifest writer path) includes dataset_id/schema metadata in `manifest.json` for WRDS runs (so artifacts are self-describing).
  * [ ] Rerun `configs/wfv_flagship_wrds.yaml` (or the current canonical WRDS config) and regenerate `docs/results_wrds_resume.md` + `project_state/CURRENT_RESULTS.md` to point at the new run_id.
  * [ ] The WRDS resume summary includes: holdout window dates, Sharpe_HAC, MaxDD, MAR, turnover, SPA p-value, reality-check p-value, and dataset_id.
* **Suggested test plan:**

  * `make test-fast`
  * `WRDS_DATA_ROOT=/path/to/wrds make test-wrds`
  * `WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds && make report-wrds`
  * `make validate-runlogs`

#### Ticket 3

* **Filename:** `docs/tickets/TICKET-29_automate-resume-metrics-extraction.md`
* **Goal (one sentence):** Add a deterministic script + Make target to regenerate resume/current-results markdown from a run directory so resume numbers never drift from artifacts again.
* **Why now (leverage):** The repo already has strong “audit” intentions (`docs/DOCS_AND_LOGGING_SYSTEM.md`), but resume numbers are currently manual and drift-prone (`project_state/OPEN_QUESTIONS.md` last bullet).
* **Acceptance criteria (checklist):**

  * [ ] Add a script (e.g., `scripts/update_resume_metrics.py`) that reads `manifest.json` + `metrics.json` (+ `holdout_metrics.json` when present) and outputs:

    * `docs/artifacts/resume/<run_id>/metrics.json`
    * `docs/artifacts/resume/<run_id>/snippet.md` (copy-pastable resume line)
  * [ ] Add a Make target (e.g., `make resume-metrics RUN_ID=<...>`) that runs the script.
  * [ ] The script can run on sample/public artifacts without WRDS.
  * [ ] Add a unit test that runs the extractor against an existing small artifact directory (e.g., `artifacts/sample_flagship/...` referenced in `project_state/CURRENT_RESULTS.md` L15) and asserts stable outputs.
* **Suggested test plan:**

  * `make test-fast`
  * Run `make resume-metrics RUN_ID=<sample_run_id>` and confirm files under `docs/artifacts/resume/...`
  * `make validate-runlogs`

#### Ticket 4

* **Filename:** `docs/tickets/TICKET-30_repo-hygiene-and-ignore-policy-fix.md`
* **Goal (one sentence):** Eliminate `.bak/.append` debris and ensure canonical scratch paths (like `reports/_runs/`) are ignored so the workflow stays deterministic and policy-compliant.
* **Why now (leverage):** The snapshot shows substantial hygiene drift (`project_state/_generated/git_status.txt`), which can silently poison bundling, reviews, and the “audit-grade” story.
* **Acceptance criteria (checklist):**

  * [ ] Update `.gitignore` so `reports/_runs/` is ignored (it currently shows as untracked: `git_status.txt` L54).
  * [ ] Add ignore rules for `*.bak.*` and `*.append*` (or fix the tool creating them) since they clutter the repo root and key docs paths (`git_status.txt` L12–L76).
  * [ ] Update agentic tooling (`tools/agentic/*`) so it does not create backup files in tracked directories during normal operation.
  * [ ] Add a CI/fast-check guard: fail `make test-fast` if `git status --porcelain` contains `*.bak.*` or `.append`.
* **Suggested test plan:**

  * `make test-fast`
  * `git status --porcelain` should be clean after running `python3 tools/agentic/project_state_refresh.py --zip`

---

### 4) Fast sanity checks

* `make test-fast`
* `make validate-runlogs`
* `make check-data-policy`
* `make sample && make report`
* `make wfv && make report-wfv`
* `microalpha wfv --config configs/wfv_flagship_public.yaml --out artifacts/_local/public_wfv && microalpha report --artifact-dir artifacts/_local/public_wfv/<RUN_ID>`
* `WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds && make report-wrds`
* `python3 tools/agentic/project_state_refresh.py --zip`
