## 1. Project snapshot (5–10 bullets)

* **Snapshot basis:** Ground-truth docs from `project_state/` (generated at `2025-12-22T19:29:50Z`, git SHA `e08b720b…`) + the published MkDocs site for cross-check (no code execution on my side). ([Mateo Bodon][1])
* **What it is today:** A **leakage-safety‑first, event-driven backtesting engine** with **walk-forward validation**, **parameter search**, and a **reporting/artifact pipeline** (`manifest.json`, `metrics.json`, `equity_curve.csv`, `trades.jsonl`, bootstraps, Markdown + PNG). (`ARCHITECTURE.md`, `DATAFLOW.md`, `PIPELINE_FLOW.md`) ([Mateo Bodon][2])
* **Main “demo” strategy:** A bundled **cross‑sectional momentum** “flagship” pipeline (signals → allocator → execution → borrow → risk controls → HAC Sharpe + Politis–White bootstrap). (`docs/flagship_strategy.md` on site; `RESEARCH_NOTES.md`) ([Mateo Bodon][3])
* **Bundled sample results exist** but are explicitly on **synthetic/sample data**; single-run Sharpe is negative; walk-forward Sharpe is small and **statistically unconvincing** (p-values ~1). (README “Latest Results”) ([GitHub][4])
* **WRDS integration exists by design** (local exports only; no direct WRDS connection) with explicit licensing guardrails and expected schema. (`WRDS & Real Data` page; `KNOWN_ISSUES.md`) ([Mateo Bodon][5])
* **Testing posture is unusually strong** for a resume repo: 56 test modules; explicit tests for time ordering, t+1 execution, LOB FIFO, walk-forward invariants; WRDS tests behind a marker. (`TEST_COVERAGE.md`, `Leakage Safety` page) ([Mateo Bodon][6])
* **Makefile supports a “main run” story** (`sample`, `wfv`, `wrds`, `report-*`, `test-wrds`, etc.). (`make_targets.txt`, `PIPELINE_FLOW.md`)
* **Known blocker:** WRDS reporting run hit a failure around the SPA step per `PROGRESS.md` / `KNOWN_ISSUES.md` (so the real-data story is not “locked” and interview-defensible yet).
* **Repo hygiene risk:** Large `data_sp500/`-style directories exist; automation is warned not to deep-parse. (`KNOWN_ISSUES.md`)

---

## 2. Project type + core claim

* **Project type:** **(B) Alpha research + backtesting system** (with some microstructure/execution simulation components), not a pricing library. (`ARCHITECTURE.md`, `API Reference`) ([Mateo Bodon][2])
* **Inferred core claim the repo is trying to make (credible framing):**

  * “microalpha is a **leakage-safe**, **deterministic**, **event-driven** backtesting + walk-forward research platform that produces **auditable artifacts** (manifest + configs + trade logs + reports) and includes tests that enforce chronology and execution invariants.” (`PLAN_OF_RECORD.md`, `Leakage Safety`, `Reproducibility`) ([Mateo Bodon][6])
* **Core claim it must NOT make yet (and you should stop implying):**

  * “I found alpha on WRDS/CRSP” — your own `PLAN_OF_RECORD.md` explicitly forbids marketing WRDS alpha until there’s **one locked run** with **bias-aware data**, **costs**, and **holdout** evidence. (Your repo is correctly *trying* to enforce this, but the WRDS evidence is not currently cleanly published/locked.)

---

## 3. Pipeline reconstruction (end-to-end)

### Main “run” entrypoints / commands

* **CLI entrypoints (primary):**

  * `microalpha run --config <cfg> --out <dir>` (single backtest) (`PIPELINE_FLOW.md`; `Examples` / `API Reference`) ([Mateo Bodon][7])
  * `microalpha wfv --config <cfg> --out <dir>` (walk-forward + parameter selection + reality check) (`PIPELINE_FLOW.md`; `Examples`) ([Mateo Bodon][7])
  * `microalpha report --artifact-dir <artifact_dir>` (render summary + plots) (`PIPELINE_FLOW.md`, `DATAFLOW.md`)
* **Make targets (defines “main run” in practice):**

  * `make sample`, `make wfv`, `make report`, `make report-wfv`
  * WRDS gated: `WRDS_DATA_ROOT=... make wfv-wrds`, `make report-wrds`, `make test-wrds`, `make wrds` (`make_targets.txt`, `PIPELINE_FLOW.md`)
* **Convenience scripts present:** `run.py`, `walk_forward.py` (`PIPELINE_FLOW.md` list of entrypoints).

### End-to-end flow (what happens)

1. **Data ingest / event stream**

   * Inputs (per `DATAFLOW.md` + docs site):

     * Sample bundle: `data/sample/` (synthetic panel + meta + rf + universe snapshot) ([Mateo Bodon][3])
     * Public bundle: `data/public/` (not fully specified in `project_state`; referenced in `DATAFLOW.md`)
     * WRDS local exports: per-symbol CSV/Parquet with required columns (`open/high/low/close/volume/...`) and NY timezone assumption. ([Mateo Bodon][5])
   * Data handlers: `CsvDataHandler`, `MultiCsvDataHandler` (`src/microalpha/data.py`; `API Reference`) ([Mateo Bodon][2])

2. **Core simulation / strategy logic**

   * `Engine` streams `MarketEvent`s, enforces monotonic timestamps, routes to strategy/portfolio/broker. (`ARCHITECTURE.md`, `Leakage Safety`, `API Reference`) ([Mateo Bodon][6])
   * Strategies (from `MODULE_SUMMARIES.md` / symbol index): `meanrev`, `breakout`, `mm`, `cs_momentum`, `flagship_mom` (flagship momentum).

3. **Portfolio + constraints + sizing**

   * `Portfolio` enforces exposure/drawdown/turnover limits and logs executions (`trades.jsonl`). (`ARCHITECTURE.md`; `API Reference`; `Reproducibility`) ([Mateo Bodon][2])
   * Capital policies (`microalpha.capital`) exist (e.g., volatility-scaled sizing). (`API Reference`) ([Mateo Bodon][2])

4. **Broker + execution / costs**

   * `SimulatedBroker` wraps an `Executor` and enforces **t+1 semantics**. (`Leakage Safety`; `API Reference`) ([Mateo Bodon][6])
   * Executors: TWAP, VWAP, Implementation Shortfall, impact models, LOB execution. (`FUNCTION_INDEX.md` + `API Reference`) ([Mateo Bodon][2])
   * Slippage models: linear, sqrt, hybrid linear+sqrt with spread floor; legacy volume slippage. (`FUNCTION_INDEX.md`; `Flagship Strategy`) ([Mateo Bodon][3])

5. **Evaluation + inference**

   * Metrics: `compute_metrics(...)` and Sharpe stats with optional HAC lags (`risk_stats.py`).
   * Walk-forward: `run_walk_forward(...)` orchestrates folds, grid search, per-fold metrics, and aggregated “reality check”. (`walkforward.py` index; `Leakage Safety` WFV section) ([Mateo Bodon][6])
   * Multiple-testing correction tooling exists (Hansen SPA utilities in `src/microalpha/reporting/spa.py` per symbol index), but WRDS reporting currently shows fragility (see `PROGRESS.md` mention of SPA failure).

6. **Artifacts + reporting**

   * Runner writes: `manifest.json` (run_id, git_sha, config hash, versions, seed), `metrics.json`, `equity_curve.csv`, `trades.jsonl`, bootstrap outputs, exposures. (`DATAFLOW.md`; `Reproducibility`; `Flagship Strategy`) ([Mateo Bodon][8])
   * Reporting: `microalpha report` uses `src/microalpha/reporting/summary.py` + `tearsheet.py` to render Markdown + PNG; factor regression injects tables when factor CSV exists. (`PIPELINE_FLOW.md`; `Factors` page) ([Mateo Bodon][9])

---

## 4. Credibility/validity audit (leakage, overfit, correctness)

Below are **interview-embarrassment risks**. For each: **risk → where → minimal diagnostic → fix direction**.

### A) Leakage / lookahead / chronology

* **Risk: “Optional unsafe mode” quietly defeats your core claim.**

  * **Where:** `Leakage Safety` explicitly documents `exec.lob_tplus1: false` disabling LOB t+1 semantics. ([Mateo Bodon][6])
  * **Diagnostic:** Add a test that runs a tiny LOB scenario with `lob_tplus1=false` and asserts either (a) a hard failure unless an explicit “unsafe” flag is set, or (b) the manifest records `unsafe_allow_lookahead=true`.
  * **Fix:** Treat disabling t+1 as **unsafe**: require an explicit config knob like `unsafe_allow_lookahead: true`, emit a loud warning, and persist it into `manifest.json` + report header.

* **Risk: Forward-fill / price alignment can leak if implemented casually.**

  * **Where:** API reference notes `CsvDataHandler.get_latest_price(ts)` supports `"exact"` and `"ffill"` modes. ([Mateo Bodon][2])
  * **Diagnostic:** Create a synthetic price series with missing dates and a “spike” after a gap; verify `ffill` never uses future values when queried at pre-spike timestamps (unit test).
  * **Fix:** Make alignment rules explicit in config; log when `ffill` is used; optionally forbid `ffill` in research runs unless explicitly enabled.

* **Risk: Universe membership and sector info may be non point-in-time (WRDS) even if the engine is leak-safe.**

  * **Where:** WRDS doc *warns* against survivorship; suggests rolling a universe using `namedt/nameendt` logic in `crsp.stocknames`. ([Mateo Bodon][5])
  * **Diagnostic:** Build two universes: (1) “today’s constituents” and (2) point-in-time membership; run the same config and show the PnL delta is non-trivial (it usually is).
  * **Fix:** Provide a canonical script (`scripts/build_flagship_universe.py` exists per `EXPERIMENTS.md`) that **outputs monthly snapshots** with effective dates; strategy must consume the latest snapshot **≤ t** only.

### B) Bias / data correctness (WRDS-level)

* **Risk: Delisting returns and terminal events are easy to get wrong (and interviewers will ask).**

  * **Where:** WRDS doc mentions `delist_date` stops trading on the delisting day, but does **not** state how delisting returns (`dlret`) are incorporated. ([Mateo Bodon][5])
  * **Diagnostic:** Pick a known-delisted permno, export CRSP daily with `ret` and `dlret`, then verify portfolio PnL around delist matches CRSP total return logic.
  * **Fix:** Explicitly handle delist returns: either bake into adjusted prices/returns in ETL, or model as a final cashflow/return shock in the engine. Document it in `docs/wrds.md` and add a WRDS-marked regression test.

* **Risk: “Missing trading days must be forward-filled by WRDS” is a dangerous instruction if misunderstood.**

  * **Where:** WRDS doc states missing days should be forward-filled by WRDS; microalpha will drop absent dates. ([Mateo Bodon][5])
  * **Diagnostic:** Add ETL QA that asserts your exported file’s date index matches NYSE calendar for the period, and flags forward-filled blocks.
  * **Fix:** Replace that doc line with a stricter rule: **do not forward-fill prices**; instead ensure complete calendar by construction or explicitly drop and log missing dates; use returns for QA.

### C) Overfitting / evaluation validity

* **Risk: Walk-forward grid search can still be “p-hacking” without a final holdout, even if per-fold selection is correct.**

  * **Where:** `Leakage Safety` says optimizer uses only in-sample and records fold windows; `PROGRESS.md` mentions “holdout evaluation mode added” but current public results don’t prove it’s locked. ([Mateo Bodon][6])
  * **Diagnostic:** Enforce a **single, immutable holdout window** (e.g., last N years) that is **never** used in parameter selection; rerun and publish only the holdout metrics as “headline”.
  * **Fix:** Make nested evaluation the default: train/val for selection (walk-forward), then one final holdout test. Store holdout metrics separately and gate README updates on it.

* **Risk: Multiple-testing correction exists (SPA) but appears brittle right now.**

  * **Where:** `src/microalpha/reporting/spa.py` is “Hansen SPA test utilities” (per module docs), and `PROGRESS.md` says WRDS report failed at SPA step.
  * **Diagnostic:** Add unit tests for SPA on controlled synthetic data:

    * Null case (identical strategies) → p ≈ 1
    * One dominant strategy → p small
    * Degenerate/constant return columns → doesn’t crash; emits “degenerate” reason
  * **Fix:** Make SPA output robust: handle zero-variance, NaNs, insufficient observations; expose `allow_zero_spa` only for smoke runs; in full runs require clean SPA or explicitly label inference as “not available”.

### D) Costs / constraints realism

* **Risk: Slippage/impact models are stylised; if metadata uses full-sample liquidity stats you leak.**

  * **Where:** Flagship uses `meta_sample.csv` with ADV/borrow/spread inputs; slippage models in `slippage.py`. ([Mateo Bodon][3])
  * **Diagnostic:** On WRDS exports, compute ADV/spread from **trailing windows** only; compare results vs “static” metadata.
  * **Fix:** Move liquidity estimation into a point-in-time metadata module (your `market_metadata.py` exists) and default to trailing-window computations.

* **Risk: Borrow accrual correctness (sign, timing, notional) is a classic “looks fine until questioned” trap.**

  * **Where:** Flagship pipeline says “daily borrow accrual from `meta_sample.csv`”. ([Mateo Bodon][3])
  * **Diagnostic:** Construct a 2-day toy: one short position with fixed borrow; verify PnL matches closed-form.
  * **Fix:** Persist a **cost breakdown** artifact (commission/slippage/borrow separately) and test it.

### E) “Green tests” that don’t validate the real claim

* **Risk: Chronology invariants are claimed, but you must keep them “unskippable” in CI.**

  * **Where:** Leakage safety page references specific tests for monotonic clocks and t+1 execution. ([Mateo Bodon][6])
  * **Diagnostic:** Ensure these tests run in the default `make test` suite (not only optional markers).
  * **Fix:** Make any “unsafe” mode flip a manifest flag and force reports to label the run “NOT LEAKAGE-SAFE”.

---

## 5. Current experiments + results interpretation

### What has actually been run (per `EXPERIMENTS.md` + `CURRENT_RESULTS.md` + README)

* `experiments/` directory is **not present**; experimentation is driven via configs + notebooks + scripts; outputs are meant to be captured via `artifacts/` + `reports/`. (`EXPERIMENTS.md`)
* **Bundled sample runs (the only fully-public evidence in snapshot):**

  * Single backtest: `configs/flagship_sample.yaml` → Sharpe_{HAC} **-0.66**, MAR **-0.41**, Max DD **17.26%**, “RealityCheck p-value” **0.861**. ([GitHub][4])
  * Walk-forward: `configs/wfv_flagship_sample.yaml` → Sharpe_{HAC} **0.22**, MAR **0.03**, Max DD **34.79%**, p-value **1.000**. ([GitHub][4])
  * Factor regression (sample FF3): alpha **-0.0055** with t-stat **-1.42** (not significant), plus large factor loadings. ([GitHub][4])

### Plain-language interpretation (blunt)

* **This is not “alpha.”**

  * Negative Sharpe on the single run and **p-values near 1** mean “nothing survives inference.” Even the walk-forward Sharpe is tiny and comes with a huge drawdown on tiny synthetic data — interviewers will correctly call this “pipeline demo, not result.” ([GitHub][4])
* **What *is* promising:**

  * The repo demonstrates a legitimate research workflow: walk-forward orchestration, reproducible artifacts, and explicit leakage tests (that’s the resume-worthy claim right now). ([Mateo Bodon][6])
* **What’s broken / not yet meaningful:**

  * WRDS “resume-grade” results are **not locked** in the provided snapshot: `KNOWN_ISSUES.md` and `PROGRESS.md` indicate WRDS reporting hit SPA fragility and that published WRDS metrics are pre-tightening and pending rerun.
  * Anything implying “production-grade alpha” should be toned down until a holdout run is published with costs, bias controls, and stable inference.

---

## 6. Codebase & infrastructure assessment

### What’s strong (keep and emphasize)

* **Leakage-safety is a first-class invariant** with explicit tests and documented rules (monotonic clocks, t+1 execution, FIFO LOB). (`Leakage Safety` + test references) ([Mateo Bodon][6])
* **Deterministic, auditable artifacts**: manifest captures git SHA, config hash, versions, seed; trade logs are JSONL and tests enforce determinism. (`Reproducibility`) ([Mateo Bodon][8])
* **Clear extension points:** runner/engine/data/portfolio/broker/execution are modular; API reference is surprisingly complete for a resume repo. ([Mateo Bodon][2])
* **Wiring for real data exists** while respecting licensing: expects local exports; warns against committing licensed data. ([Mateo Bodon][5])

### What’s weak / risky (interview scrutiny)

* **Reporting fragility around inference (SPA)** is a credibility gap: if your multiple-testing correction crashes, it looks like you can’t support inference claims (and encourages cherry-picking).
* **Data bloat** (large `data_sp500/` etc) risks slow CI / huge clones and makes the repo feel messy unless extremely justified and clearly documented. (`KNOWN_ISSUES.md`)
* **Docs in the provided `project_state` bundle are truncated** with `...` in multiple places (`PIPELINE_FLOW.md`, `DATAFLOW.md`, etc). That’s fine for a compact bundle, but for interview-grade clarity, the *repo’s* canonical docs should be fully explicit and not rely on elisions.

---

## 7. Missing pieces + highest-leverage improvements

### Missing pieces (blocking “quant-interview-grade”)

* **A single locked, bias-aware WRDS/CRSP headline run** with:

  * point-in-time universe membership
  * delist handling
  * realistic costs (and decomposition)
  * walk-forward parameter selection **plus a final holdout**
  * SPA / reality-check inference that doesn’t crash
  * a short, readable “audit this run” doc pointing to the artifact directory
* **A defensible evaluation protocol written in plain English** (not just implied):

  * what is trained, what is tuned, what is held out
  * how many configs were tried, and why that doesn’t constitute p-hacking
  * what baselines were used (equal-weight, market, simple momentum baseline)

### Highest-leverage improvements (minimal work, maximum credibility)

* **Make “unsafe” modes impossible to use accidentally** (lob_tplus1 disablement, etc): manifest flag + report banner + tests that enforce it. ([Mateo Bodon][6])
* **Add WRDS ETL QA + point-in-time universe generator as the canonical path** (scripts already exist per `EXPERIMENTS.md`; formalize and test).
* **Fix SPA robustness** and make inference output mandatory for “headline” results.
* **Publish a compact “results suite”**: 1 config + 1 dataset spec + 1 artifact directory + 1 doc page + 1 README table. Everything else becomes “exploration.”

---

## 8. Roadmap (1–2 weeks, 4–8 weeks, longer-term)

### Next 1–2 weeks: validity + minimum impressive demo run

* **Unblock WRDS reporting end-to-end**

  * Fix SPA degenerate-case handling and ensure `make report-wrds` never dies on real artifacts.
* **Produce one locked WRDS holdout run**

  * Use tightened caps (per `ROADMAP.md`) and publish: config + artifact run_id + summary page.
* **Add “audit this run” documentation**

  * One page explaining: data spec, universe construction, costs, selection, inference, reproducibility.
* **Add baselines**

  * At minimum: equal-weight and market proxy returns (and optionally a simple momentum baseline with no allocator/LOB) so your flagship isn’t evaluated in a vacuum.

### Next 4–8 weeks: full experiment grid + robustness

* **Robustness grid (pre-registered)**

  * Universe variants (top 500 vs top 1000; exchange filters)
  * Cost multipliers (0.5×/1×/2×)
  * Rebalance frequency (monthly vs weekly)
  * Risk cap sensitivity (documented, not tuned on holdout)
* **Factor attribution**

  * FF5+Mom regression + rolling betas + alpha CI; publish in `reports/summaries/`.
* **Performance + scale**

  * Make WRDS pipeline reproducible and fast enough that reruns are routine (profiling, caching, I/O).

### Longer-term: “institution-grade”

* **Data versioning + provenance** (DVC/Quilt-like discipline, checksums for exports, schema enforcement).
* **Better microstructure realism** (if you keep LOB): calibrate latency/queue parameters to a known dataset or clearly label LOB mode as “didactic”.
* **Formal research hygiene**

  * Deflated Sharpe / selection bias adjustments, pre-registered hypothesis tests, and a “model risk” section in docs.

---

## 9. Resume-grade deliverables (figures/tables/artifacts + how to present)

You want **3–8 artifacts** that look serious *and* survive interrogation. Here’s the defensible set:

1. **Headline results table (WRDS holdout only)**

   * Metrics: net Sharpe (HAC), ann. return/vol, max DD, turnover, cost breakdown (commission/slippage/borrow), SPA p-value / reality-check p-value.
   * Location: `docs/results_wrds.md` + mirrored in README (with run_id link).

2. **Equity curve + drawdown plot (holdout)**

   * One figure with: equity curve, drawdown, and a baseline overlay (equal-weight or market).
   * Location: `docs/img/wrds_flagship/<RUN_ID>/tearsheet.png` (or similar).

3. **Walk-forward fold stability plot**

   * Show chosen params per fold (heatmap) + fold Sharpe distribution (not just average).
   * Goal: prove you didn’t “win” on one lucky fold.

4. **Multiple-testing correction output (SPA)**

   * A small table: number of grid candidates, best in-sample Sharpe, SPA p-value, conclusion.
   * If SPA is unavailable, the report must say “Inference failed because X” (and that blocks “headline” status).

5. **Cost sensitivity curve**

   * Sharpe vs cost multiplier and max DD vs cost multiplier.
   * This is one of the fastest ways to look credible.

6. **Factor regression table (FF5+Mom)**

   * Alpha, t-stat (HAC), and major factor betas; include rolling beta plot if easy.
   * Location: `reports/summaries/wrds_flagship_factors.md` + embedded snippet in the main summary.

7. **Data QA table (bias + coverage)**

   * Universe size over time, % missing days, delist counts handled, sector coverage.
   * This shuts down survivorship questions quickly.

**How to present in README (tight framing):**

* Lead with the **engine claim** (“leakage-safe + reproducible + audited”) and show **one locked WRDS holdout run** as proof of capability — not as “alpha discovery.”

---

## 10. HANDOFF FOR CODEX (machine-readable)

```yaml
top_priority_tasks:
  - goal: "Fix SPA/Reality-check robustness so WRDS reporting never crashes and always emits interpretable inference outputs."
    files_likely_touched:
      - "src/microalpha/reporting/spa.py"
      - "src/microalpha/reporting/wrds_summary.py"
      - "reports/spa.py"
      - "reports/render_wrds_flagship.py"
      - "tests/test_wrds_summary_render.py"
      - "tests/test_reality_check_store.py"
    acceptance_criteria:
      - "Running WRDS report on a real artifact directory completes without exceptions, even with degenerate/constant return series."
      - "SPA outputs (json + md) exist and p-values are always in [0, 1] or explicitly marked as 'degenerate' with reasons."
      - "Unit tests cover: null case, dominant-strategy case, degenerate case."
    recommended_tests_or_commands:
      - "pytest -q"
      - "WRDS_DATA_ROOT=/path/to/wrds make report-wrds"
      - "python reports/spa.py --help"

  - goal: "Produce and publish ONE locked WRDS flagship holdout run (tightened caps) with a single canonical run_id referenced from docs + README."
    files_likely_touched:
      - "configs/wfv_flagship_wrds.yaml"
      - "configs/wfv_flagship_wrds_smoke.yaml"
      - "configs/wfv_flagship_sample_holdout.yaml"
      - "docs/wrds.md"
      - "docs/results_wrds.md"
      - "reports/summaries/wrds_flagship.md"
      - "README.md"
      - "PROGRESS.md"
    acceptance_criteria:
      - "A full WRDS walk-forward + holdout artifact directory exists with manifest/metrics/folds/bootstrap + SPA outputs."
      - "docs/results_wrds.md includes: run_id, config hash, evaluation windows, headline metrics, and explicit caveats."
      - "README links to that exact run_id and states it is holdout-only headline."
    recommended_tests_or_commands:
      - "WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds"
      - "WRDS_DATA_ROOT=/path/to/wrds make report-wrds"
      - "WRDS_DATA_ROOT=/path/to/wrds make test-wrds"

  - goal: "Add survivorship + delisting correctness to WRDS ETL and document it (including delisting returns handling)."
    files_likely_touched:
      - "scripts/etl_wrds_crsp.py"
      - "scripts/export_wrds_flagship.py"
      - "scripts/build_flagship_universe.py"
      - "docs/wrds.md"
      - "tests/test_wrds_flagship_spec.py"
      - "src/microalpha/market_metadata.py"
    acceptance_criteria:
      - "Universe generation is point-in-time (uses namedt/nameendt) and includes delisted securities within the backtest window."
      - "Delisting returns (dlret) are either incorporated into exported total returns or explicitly modeled; behavior is documented."
      - "WRDS spec tests fail if delist handling or point-in-time logic is missing."
    recommended_tests_or_commands:
      - "pytest -q -m wrds"
      - "python scripts/export_wrds_flagship.py --help"

  - goal: "Make 'unsafe' execution modes unmissable: disabling t+1 semantics must require explicit consent and be recorded in manifest + report banners."
    files_likely_touched:
      - "src/microalpha/execution.py"
      - "src/microalpha/broker.py"
      - "src/microalpha/manifest.py"
      - "src/microalpha/reporting/summary.py"
      - "docs/leakage-safety.md"
      - "tests/test_tplus1_execution.py"
      - "tests/test_time_ordering.py"
    acceptance_criteria:
      - "If lob_tplus1=false (or equivalent) is set, the run either hard-fails unless unsafe_allow_lookahead=true is present, or it emits a prominent warning + manifest flag."
      - "Reports display a clear 'NOT LEAKAGE-SAFE' banner for unsafe runs."
    recommended_tests_or_commands:
      - "pytest -q"
      - "microalpha run --config configs/mm_lob_same_tick.yaml"

  - goal: "Enforce nested evaluation: walk-forward selection uses train/val only; a final holdout window is never touched until the end and is stored separately."
    files_likely_touched:
      - "src/microalpha/config_wfv.py"
      - "src/microalpha/walkforward.py"
      - "configs/wfv_flagship_sample_holdout.yaml"
      - "tests/test_walkforward.py"
      - "docs/leakage-safety.md"
      - "docs/PLAN_OF_RECORD.md"
    acceptance_criteria:
      - "Artifacts include holdout_metrics.json (or similar) distinct from fold summaries."
      - "Tests prove optimizer never accesses holdout timestamps (synthetic sentinel test)."
      - "Docs explain the exact split protocol and what is (and isn't) tuned."
    recommended_tests_or_commands:
      - "pytest -q tests/test_walkforward.py"
      - "microalpha wfv --config configs/wfv_flagship_sample_holdout.yaml --out artifacts/sample_wfv_holdout"

  - goal: "Eliminate liquidity lookahead: compute ADV/spread/borrow inputs from trailing windows (point-in-time) and add a cost sensitivity report."
    files_likely_touched:
      - "src/microalpha/market_metadata.py"
      - "src/microalpha/slippage.py"
      - "src/microalpha/reporting/robustness.py"
      - "reports/analytics.py"
      - "tests/test_slippage_models.py"
      - "docs/flagship_strategy.md"
    acceptance_criteria:
      - "Metadata used for costs is computed using only information available up to time t."
      - "WRDS flagship report includes Sharpe vs cost-multiplier and maxDD vs cost-multiplier figures."
      - "Unit tests validate monotonicity: higher costs -> (weakly) worse net returns in controlled scenarios."
    recommended_tests_or_commands:
      - "pytest -q tests/test_slippage_models.py"
      - "WRDS_DATA_ROOT=/path/to/wrds make report-wrds"

  - goal: "Add baselines and benchmarking so flagship performance is contextualized (equal-weight, market proxy, simple momentum baseline)."
    files_likely_touched:
      - "src/microalpha/reporting/analytics.py"
      - "src/microalpha/reporting/summary.py"
      - "reports/generate_summary.py"
      - "reports/summaries/wrds_flagship.md"
      - "docs/results_wrds.md"
    acceptance_criteria:
      - "Every published results page includes at least one baseline comparison."
      - "Baselines are computed with the same calendar, costs assumptions clearly stated (or gross vs net shown)."
    recommended_tests_or_commands:
      - "pytest -q"
      - "microalpha report --artifact-dir artifacts/<run_id>"

  - goal: "Reduce repo bloat / CI risk from large data directories while keeping deterministic sample runs."
    files_likely_touched:
      - ".gitignore"
      - "scripts/check_data_policy.py"
      - "tools/build_project_state.py"
      - "Makefile"
      - "docs/DOCS_AND_LOGGING_SYSTEM.md"
      - "KNOWN_ISSUES.md"
    acceptance_criteria:
      - "Default CI/test paths do not traverse huge data directories."
      - "Fresh clone size is materially reduced OR large datasets are clearly optional with documented download/regen scripts."
      - "make sample still works offline and remains deterministic."
    recommended_tests_or_commands:
      - "make check-data-policy"
      - "make sample"
      - "pytest -q"
```

[1]: https://mateobodon.github.io/microalpha "Microalpha"
[2]: https://mateobodon.github.io/microalpha/api/ "API Reference - Microalpha"
[3]: https://mateobodon.github.io/microalpha/flagship_strategy/ "Flagship Strategy - Microalpha"
[4]: https://github.com/MateoBodon/microalpha "GitHub - MateoBodon/microalpha: A event-driven backtesting engine for quantitative strategies."
[5]: https://mateobodon.github.io/microalpha/wrds/ "WRDS & Real Data - Microalpha"
[6]: https://mateobodon.github.io/microalpha/leakage-safety/ "Leakage Safety - Microalpha"
[7]: https://mateobodon.github.io/microalpha/examples/ "Examples - Microalpha"
[8]: https://mateobodon.github.io/microalpha/reproducibility/ "Reproducibility - Microalpha"
[9]: https://mateobodon.github.io/microalpha/factors/ "Factors - Microalpha"
