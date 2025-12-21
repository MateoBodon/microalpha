## 1. Project snapshot (5–10 bullets)

* Snapshot basis: **project_state.zip** generated at **2025‑12‑20** on commit **b128e4af…** (headers in all `project_state/*.md` files).
* Repo is a **leakage‑safe, event‑driven backtesting + research** stack: `DataHandler → Engine → Strategy → Portfolio → Broker → Execution → Artifacts` (ARCHITECTURE.md → “System overview”).
* **Primary workflows** are “single backtest” + “walk‑forward validation” + “report” via CLI (`microalpha run`, `microalpha wfv`, `microalpha report`) and Make targets (PIPELINE_FLOW.md → “Primary entrypoints”; `_generated/make_targets.txt`).
* **Flagship demo**: cross‑sectional momentum pipeline on bundled synthetic multi‑asset dataset (`data/sample/`) with allocator + queue/impact cost model + borrow accrual + inference reporting. ([Mateo Bodon][1])
* **Leakage safety is explicitly designed + tested**: monotonic timestamps, t+1 execution, fill ordering, portfolio timestamp guards, LOB FIFO, WFV in‑sample‑only optimization. ([Mateo Bodon][2])
* **Reproducibility is first‑class**: per‑run `manifest.json` includes git SHA, config hash, versions, and seed; `trades.jsonl` is deterministic; WFV bootstrap p‑values should replay. ([Mateo Bodon][3])
* **WRDS/CRSP integration exists but is “guarded”** (env + local exports only) with explicit survivorship/corporate‑action cautions (KNOWN_ISSUES.md; WRDS guide). ([Mateo Bodon][4])
* **Current “real data” evidence is not resume‑credible yet**: latest WRDS metrics show **Sharpe_HAC ~0.40** but **max drawdown ~82%** and **non‑significant** reality check / SPA p‑values (CURRENT_RESULTS.md → “Latest WRDS result”; KNOWN_ISSUES.md).
* **Experiments story is thin**: `EXPERIMENTS.md` explicitly says there is no dedicated `experiments/` directory; experimentation is configs + scripts/notebooks + artifacts.
* I did **not** execute the code; this audit is reconstructed from **project_state docs + generated indices** and the published MkDocs pages.

---

## 2. Project type + core claim

* **Type:** (B) **alpha research + backtesting system** (with a secondary “microstructure/LOB simulator” track).
* **Inferred core claim the repo is trying to make:**

  * “Microalpha is a **leakage‑safe, deterministic research backtester** with **walk‑forward validation** and **proper inference** (HAC Sharpe, block bootstrap reality checks, SPA), demonstrated end‑to‑end on a flagship cross‑sectional momentum pipeline and extendable to WRDS/CRSP.” (ARCHITECTURE.md + DATAFLOW.md + PIPELINE_FLOW.md; plus Leakage Safety / Reproducibility pages). ([Mateo Bodon][2])
* Blunt truth: **your strongest claim today is research hygiene + reproducibility**, not “found alpha.” Your own CURRENT_RESULTS supports that (p‑values + drawdown).

---

## 3. Pipeline reconstruction (end-to-end)

### “Main run” entrypoints / commands (from docs)

* **Single backtest**

  * `microalpha run --config <cfg> --out <dir>` (PIPELINE_FLOW.md → “Primary entrypoints”)
  * Example flagship sample run command sequence is documented. ([Mateo Bodon][1])
* **Walk-forward validation**

  * `microalpha wfv --config <cfg> --out <dir>` (PIPELINE_FLOW.md)
  * Flagship sample WFV uses **252d train / 63d test** and a small grid (top_frac, skip_months). ([Mateo Bodon][1])
* **Reporting**

  * `microalpha report --artifact-dir <dir>` which invokes `src/microalpha/reporting/summary.py` + `tearsheet.py` (PIPELINE_FLOW.md → “Report pipeline”; FUNCTION_INDEX.md sections).
* **WRDS (guarded)**

  * `WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds` then `make report-wrds` (PIPELINE_FLOW.md → “WRDS (guarded)”).
  * Data stays **local**; repo should only contain derived summaries/plots (WRDS guide). ([Mateo Bodon][4])

### End-to-end flow (reconstructed from DATAFLOW.md + function index)

1. **Config → strongly typed config objects**

   * YAML configs in `configs/` (18 files; e.g., `configs/flagship_sample.yaml`, `configs/wfv_flagship_wrds.yaml`) feed `parse_config` (`src/microalpha/config.py`) and `WFVCfg` (`src/microalpha/config_wfv.py`).
   * DATAFLOW.md → “Processing (1)” + FUNCTION_INDEX.md → `parse_config`, `load_wfv_cfg`, `run_walk_forward`.
2. **Data ingest → market events**

   * `DataHandler` layer loads per‑symbol CSVs / panels: `CsvDataHandler` (single asset) and `MultiCsvDataHandler` (multi‑asset, synchronised). (DATAFLOW.md → “Processing (2)”; `src/microalpha/data.py`).
   * WRDS path expects `SYMBOL.csv|parquet` schema with `date, open, high, low, close, volume` etc. ([Mateo Bodon][4])
3. **Engine orchestration → strict time semantics**

   * `Engine` enforces monotonic timestamps and dispatches events; `LookaheadError` exists as a hard stop (Leakage Safety → “Engine invariants”; `src/microalpha/engine.py`). ([Mateo Bodon][2])
4. **Strategy logic**

   * Strategies in `src/microalpha/strategies/`:

     * Flagship: `flagship_mom.py` (cross‑sectional **12‑1 sector‑neutral momentum**) ([Mateo Bodon][1])
     * Others: `meanrev.py`, `breakout.yaml` strategy, `mm.py` (LOB market making), `cs_momentum.py` configs etc (repo inventory + configs list).
5. **Portfolio construction + constraints**

   * `Portfolio` applies sizing/constraints and refuses stale/backdated signals; risk controls include sector caps, exposure heat, ADV turnover clamp (Leakage Safety → “Portfolio guards”; Flagship Strategy → “Pipeline Overview”; `src/microalpha/portfolio.py`, `src/microalpha/risk.py`). ([Mateo Bodon][1])
6. **Broker + execution + cost/impact**

   * `Broker` interfaces between portfolio and execution (`src/microalpha/broker.py`).
   * Execution models include TWAP/VWAP/Implementation Shortfall and an internal LOB mode (ARCHITECTURE.md; `src/microalpha/execution.py`).
   * Flagship sample uses **TWAP + IOC queue model + linear+sqrt impact + spread floor**, plus **borrow accrual** from metadata. ([Mateo Bodon][1])
7. **Metrics + inference**

   * Metrics: `src/microalpha/metrics.py` + `src/microalpha/risk_stats.py` (Newey‑West HAC + block bootstrap).
   * Walk‑forward includes a **bootstrap reality check** over strategy variants (FUNCTION_INDEX.md → `bootstrap_reality_check`, `bootstrap_reality_check` called from `run_walk_forward`).
8. **Artifacts**

   * Written under `artifacts/<run_id>/`: `manifest.json`, `metrics.json`, `equity_curve.csv`, `trades.jsonl`, `bootstrap.json`, and WFV fold summaries (DATAFLOW.md → “Outputs”; Reproducibility → “Manifest fields / Trade logs”). ([Mateo Bodon][3])
9. **Reporting**

   * `src/microalpha/reporting/summary.py` generates markdown summary (optionally includes factor table and costs/coverage sections).
   * `src/microalpha/reporting/tearsheet.py` renders equity/drawdown + bootstrap plots.
   * Factor regression helper exists (`reports/factors_ff.py`) with Newey‑West SE. ([Mateo Bodon][5])

### Critical module map (high-level)

* CLI / orchestration: `src/microalpha/cli.py`, `src/microalpha/runner.py`, wrappers `run.py`, `walk_forward.py` (ARCHITECTURE.md).
* Config: `src/microalpha/config.py`, `src/microalpha/config_wfv.py` (BacktestCfg / WFVCfg).
* Data: `src/microalpha/data.py`, `src/microalpha/events.py`, `src/microalpha/market_metadata.py`
* Core sim: `src/microalpha/engine.py`
* Strategy: `src/microalpha/strategies/*` (flagship momentum, mean reversion, breakout, market making)
* Portfolio / risk: `src/microalpha/portfolio.py`, `src/microalpha/risk.py`, `src/microalpha/allocators.py`
* Brokerage / execution: `src/microalpha/broker.py`, `src/microalpha/execution.py`, `src/microalpha/limit_order_book.py`, `src/microalpha/slippage.py`
* Metrics / inference: `src/microalpha/metrics.py`, `src/microalpha/risk_stats.py`, walk‑forward orchestration `src/microalpha/walkforward.py`
* Artifacts / reproducibility: `src/microalpha/manifest.py`, `src/microalpha/logging.py`
* Reporting: `src/microalpha/reporting/summary.py`, `src/microalpha/reporting/tearsheet.py`, plus `reports/*.py` scripts.

---

## 4. Credibility/validity audit (leakage, overfit, correctness)

Below are **interview‑embarrassment risks** I’d expect a serious reviewer to probe. For each: **risk → where → minimal diagnostic → fix direction**.

### A) Leakage / timestamp semantics

* **Risk:** “Same‑tick” fills or signal‑to‑fill timing mistakes (classic lookahead).

  * **Where:** Leakage Safety notes t+1 is default, but **LOB t+1 can be disabled** (`exec.lob_tplus1: false`). ([Mateo Bodon][2])
  * **Minimal diagnostic:** Add a “red team” test that forces `lob_tplus1: false` + a strategy that keys off fills, and assert a `LookaheadError` or explicit “unsafe mode” warning is raised.
  * **Fix:** Make “unsafe” execution modes **opt‑in with explicit acknowledgement** (e.g., `exec.allow_same_tick_fills: true`), and stamp the manifest with an `unsafe_execution: true` flag (Reproducibility page emphasizes manifest auditability). ([Mateo Bodon][3])

* **Risk:** Momentum signal uses close(t) but trades at close(t) (implicit lookahead).

  * **Where:** Flagship is “12‑1 momentum” with t+1 execution invariant stated. ([Mateo Bodon][1])
  * **Minimal diagnostic:** Unit test: construct a toy price panel with a single jump at day t, ensure the strategy cannot profit from that jump until day t+1 fill.
  * **Fix:** Enforce signal timestamp == current market event, and enforce fills strictly > signal timestamp unless in explicitly marked unsafe mode.

* **Risk:** VWAP execution uses future volume/price path; if any upstream component accidentally reads execution schedule/realized VWAP as “information”, that’s leakage.

  * **Where:** `src/microalpha/execution.py` includes `VWAP — Volume-weighted execution across future timestamps.` (ARCHITECTURE.md + FUNCTION_INDEX).
  * **Minimal diagnostic:** Add a test ensuring strategy state never reads fills/realized prices to form signals (e.g., strategy API only sees market event, not execution outcomes).
  * **Fix:** Separate interfaces: strategy sees **market data only**; execution outcomes are logged post‑hoc; forbid back‑references.

### B) Walk-forward / overfitting / p-hacking

* **Risk:** Repeated config tweaking on WRDS until metrics “look good” → p‑hacking, even with WFV.

  * **Where:** OPEN_QUESTIONS.md + KNOWN_ISSUES.md explicitly say **WRDS WFV rerun pending** and prior metrics were “pre‑tightening.” That’s exactly where p‑hacking happens.
  * **Minimal diagnostic:** Introduce a **frozen protocol** doc and a final **untouched holdout period** config. Then rerun once.
  * **Fix:** Implement a 3‑tier protocol:

    * **Train** (research / model selection)
    * **Validation** (WFV selection / hyperparameters)
    * **Final test** (single locked evaluation period, never used for tuning)
    * Store the protocol parameters inside artifacts/manifest for audit.

* **Risk:** WFV fold overlap + bootstrap inference misuse (double counting dependence).

  * **Where:** `src/microalpha/walkforward.py` has bootstrap reality check + fold summaries.
  * **Minimal diagnostic:** Validate that aggregated return stream for inference is **concatenated OOS test windows only**, no overlap, no in‑sample leakage.
  * **Fix:** Make “evaluation return stream” an explicit artifact (`oos_returns.csv`) and use it consistently for Sharpe, bootstrap, and factor regression.

### C) Data biases (survivorship, corporate actions, missingness)

* **Risk:** Survivorship bias through universe construction (especially any S&P500‑style list built from today’s constituents).

  * **Where:** WRDS guide explicitly warns “download full history panels, do not pre‑filter to active listings.” ([Mateo Bodon][4])
    Repo also has scripts like `scripts/build_flagship_universe.py`, `scripts/augment_sp500.py` (repo inventory).
  * **Minimal diagnostic:** For WRDS runs, compute and log:

    * fraction of traded symbols with `delist_date` in sample
    * whether you included securities where `nameendt` < test_end (should be possible historically)
  * **Fix:** Universe file generation should be **date‑conditional** (e.g., CRSP `namedt/nameendt` window logic is even suggested in docs) and saved per rebalance date. ([Mateo Bodon][4])

* **Risk:** Corporate action handling / delisting returns mishandled → inflated performance OR bogus drawdowns.

  * **Where:** WRDS guide: use adjustment factors; include delisted securities; optionally stop trading on delisting date. ([Mateo Bodon][4])
  * **Minimal diagnostic:** Add QA checks comparing:

    * provided `ret` column vs computed price returns
    * delisting windows: last trading day + delisting return treatment
  * **Fix:** Bake WRDS QA into the exporter pipeline (`scripts/export_wrds_flagship.py`) and fail fast if inconsistencies exceed tolerance.

* **Risk:** Calendar misalignment / stale forward‑filled prices creating “free rebalancing” effects cross‑sectionally.

  * **Where:** WRDS guide says missing days should be forward‑filled by WRDS, and Microalpha drops absent dates per symbol. ([Mateo Bodon][4])
  * **Minimal diagnostic:** Log per‑day **coverage ratio** (#symbols with valid market event / #universe) and ensure ranking uses only symbols with fresh data at that timestamp.
  * **Fix:** In `MultiCsvDataHandler`, require a canonical calendar (NYSE) and explicit missingness policy (drop symbol vs carry‑forward with a “stale” flag that prevents trading).

### D) Transaction costs / leverage realism

* **Risk:** “Good Sharpe” that disappears under costs; current turnover numbers already look extreme.

  * **Where:** Flagship sample pipeline includes impact + spread floor + queue model + borrow accrual. ([Mateo Bodon][1])
    But CURRENT_RESULTS shows WRDS turnover in the **billions** and drawdown **82%** (CURRENT_RESULTS.md).
  * **Minimal diagnostic:** Cost sensitivity sweep: multiply spreads/impact by {0.5, 1, 2, 4} and show Sharpe/return/turnover curves.
  * **Fix:** Make cost model parameters explicit in config + include a “cost breakdown” artifact (`costs.json`) and report it (summary renderer already has `_render_cost_section` in `src/microalpha/reporting/summary.py`).

* **Risk:** Leverage / sizing blowups (82% max DD screams either leverage, concentration, or no vol targeting).

  * **Where:** ROADMAP.md calls out “drawdown reduction validation” as a pending milestone; CURRENT_RESULTS.md shows the severity.
  * **Minimal diagnostic:** Decompose drawdown driver:

    * gross exposure time series
    * top positions concentration
    * sector exposure heat series
  * **Fix:** Add hard caps:

    * max gross leverage
    * max single‑name weight
    * volatility targeting (e.g., daily vol forecast → scale gross)
    * turnover cap tied to ADV (already mentioned as “ADV turnover clamp,” but you need to show it actually binds). ([Mateo Bodon][1])

### E) Statistical reporting correctness

* **Risk:** Factor regression alignment error (frequency mismatch).

  * **Where:** Factors page states `ff3_sample.csv` is **daily**, and uses Newey‑West HAC lag 5. ([Mateo Bodon][5])
    But other repo docs elsewhere imply “weekly” factors (this discrepancy undermines trust).
  * **Minimal diagnostic:** Assert factor index spacing + ensure portfolio returns are at same frequency (or explicitly resampled).
  * **Fix:** Make the regression utility:

    * infer frequency
    * resample returns/factors to common frequency
    * log the chosen frequency in the output table + manifest.

* **Risk:** “Reality check p‑value” misinterpreted as proof; with p≈1 it’s actually saying **no edge**.

  * **Where:** CURRENT_RESULTS.md shows reality check p‑values near 1; Leakage Safety claims reproducible p‑values. ([Mateo Bodon][2])
  * **Minimal diagnostic:** Include a “how to read this” section in summary output: what null is, what p means.
  * **Fix:** Treat inference outputs as **guardrails**, not badges; gate any “resume claim” on passing thresholds that you pre‑register.

---

## 5. Current experiments + results interpretation

### What has actually been run (from EXPERIMENTS.md + CURRENT_RESULTS.md)

* **Experiment scaffolding**

  * `EXPERIMENTS.md` explicitly: **no `experiments/` directory**; experiments live in **configs**, `scripts/`, and `notebooks/`.
* **Bundled sample flagship**

  * Single run artifacts under `artifacts/sample_flagship/` (ARCHITECTURE.md → “Artifact layout”).
  * WFV run artifacts under `artifacts/sample_wfv/`.
  * WFV setup documented: 252 train / 63 test, small grid {top_frac, skip_months}. ([Mateo Bodon][1])
* **WRDS flagship**

  * `CURRENT_RESULTS.md` lists a “Latest WRDS result” and `KNOWN_ISSUES.md` says the published WRDS metrics are **pre‑tightening** and need a rerun.

### Plain-language interpretation (no spin)

* **Sample flagship single run:** Sharpe_HAC ≈ **‑0.66**, MAR ≈ **‑0.41**, max DD ≈ **17%**, reality check p ≈ **0.86** (CURRENT_RESULTS.md).

  * Interpretation: as “alpha evidence” it’s **useless** (and should be framed as such); as a **demo of the pipeline + artifacts + inference plumbing**, it’s fine.
* **Sample flagship walk-forward:** Sharpe_HAC ≈ **0.22**, max DD ≈ **35%**, reality check p = **1.0** (CURRENT_RESULTS.md).

  * Interpretation: again, **no statistical support** for edge; but WFV pipeline is producing fold+bootstrap artifacts.
* **WRDS walk-forward:** Sharpe_HAC ≈ **0.40** with **max DD ≈ 82%**, turnover ≈ **$1.84B**, reality check p ≈ **0.986**, SPA p ≈ **0.603** (CURRENT_RESULTS.md).

  * Interpretation: this is the one that matters for interviews, and it currently says:

    * risk controls / sizing are **not sane** (82% DD),
    * inference says **not significant** (p’s),
    * so **not resume‑credible yet** as an “alpha result.”
  * The only defensible angle right now is: “I built and validated a leakage‑safe, reproducible research stack; WRDS experiments are in progress; here are the guardrails.”

---

## 6. Codebase & infrastructure assessment

### Strengths (what would impress a reviewer)

* **Leakage discipline is explicit** and tied to named tests (Leakage Safety page links specific tests like `tests/test_time_ordering.py`, `tests/test_tplus1_execution.py`, LOB FIFO, walkforward tests). ([Mateo Bodon][2])
* **Reproducibility hooks are real**: manifest fields (git SHA, config hash, versions, seed) and deterministic trade logs are first‑class artifacts. ([Mateo Bodon][3])
* **Walk-forward orchestration exists as a real module**, not a notebook hack: `src/microalpha/walkforward.py` has dedicated functions for config load, param optimization, warmup collection, summaries, and bootstrap reality check (FUNCTION_INDEX.md).
* **Reporting pipeline is modular** (summary + tearsheet) and factor regression is integrated (reporting functions + factors utility). ([Mateo Bodon][5])
* **Test suite breadth looks serious** (55 test files in `tests/` per repo inventory; TEST_COVERAGE.md reports ~78% coverage and highlights key invariants).

### Weak points / technical debt that will get noticed

* **Docs/indices are visibly truncated with “…”** in multiple project_state files (ARCHITECTURE.md, DATAFLOW.md, PIPELINE_FLOW.md, MODULE_SUMMARIES.md, FUNCTION_INDEX.md). That reads like “auto-docs exist but aren’t actually informative.”
* **Config Reference leaks local absolute paths** (`/Users/.../microalpha/configs/...`) in `CONFIG_REFERENCE.md`. That’s sloppy and undermines reproducibility claims.
* **Experiment provenance is fragmented**: `EXPERIMENTS.md` admits there is no central experiment runner; results are split across artifacts + docs. That makes it harder to defend against “you tuned until it worked.”
* **The key resume blocker is empirical**: the only real‑data snapshot is a drawdown disaster and not statistically significant (CURRENT_RESULTS.md).

---

## 7. Missing pieces + highest-leverage improvements

### Missing pieces (blockers to “quant‑interview‑grade”)

* **A single, locked, defensible WRDS result**:

  * fixed protocol + costs + risk caps + final holdout + factor attribution + inference.
  * Today you have a WFV run, but it’s not “tightened,” and the published metrics are ugly (CURRENT_RESULTS.md, KNOWN_ISSUES.md).
* **A benchmark baseline**:

  * You’re running momentum. Interviewers will ask: “How does this compare to the canonical 12‑1 momentum long‑short or FF MOM factor?”
  * You need a baseline implementation + table, or you look like you’re hiding.
* **A “research registry” / experiment ledger**:

  * You already have manifests; you need a “runs index” that prevents cherry‑picking and shows what was tried.
* **Consistency in analytics docs**:

  * Factor sample frequency inconsistency (docs claim daily vs other docs implying weekly) is a trust killer.

### Highest-leverage improvements (minimal work, maximum credibility)

* **Make WRDS flagship rerun the #1 priority** and treat it like a paper replication:

  * lock config,
  * add explicit leverage/turnover caps,
  * publish net/gross, cost breakdown, drawdown, and factor regression.
* **Add 2 “red team” leakage tests**:

  * “shift signals +1 day should preserve (or improve?)” (should usually degrade)
  * “use future return as signal should throw `LookaheadError` or get caught by invariants”
* **Add cost sensitivity + capacity plots** (even coarse):

  * Sharpe vs cost multiplier
  * Sharpe vs turnover cap / ADV clamp
* **Replace CONFIG_REFERENCE absolute paths with repo‑relative paths**, and add a one‑page “How to reproduce flagship WRDS run” doc with exact commands (PIPELINE_FLOW.md already has the skeleton).

---

## 8. Roadmap (1–2 weeks, 4–8 weeks, longer-term)

### Next 1–2 weeks: validity + minimum impressive demo run

* **WRDS flagship rerun (tightened caps)** (OPEN_QUESTIONS.md + ROADMAP.md):

  * implement/confirm: max gross, max name, vol targeting, turnover cap binds, realistic borrow/cost
  * rerun WFV once under locked protocol
  * update `docs/results_wrds.md` + `CURRENT_RESULTS.md` with the new run id + full metrics breakdown
* **Protocol hardening**

  * add a **final holdout** period config (never touched during tuning)
  * ensure artifacts contain explicit `train_windows`, `test_windows`, and “selected params rationale”
* **Fix analytics trust issues**

  * reconcile factor sample frequency; enforce alignment in code/tests; update docs site page accordingly ([Mateo Bodon][5])
* **Add “baseline + honesty”**

  * implement canonical momentum baseline (simple 12‑1, monthly rebalance) and compare to flagship enhancements in one table

### Next 4–8 weeks: full experiment grid + robustness

* **Robustness matrix on WRDS**

  * universes: top 500 / 1000 by mkt cap; NYSE-only; liquidity buckets
  * rebalance freq: monthly vs weekly
  * neutralization variants: sector neutral, beta neutral, dollar neutral
* **Inference + multiple testing discipline**

  * pre‑register the model zoo you compare
  * report White reality check + SPA + deflated Sharpe (or at least adjust narrative for selection)
* **Execution realism tuning**

  * calibrate spread/impact parameters from WRDS fields (ADV, price, volume) and publish assumptions
  * add borrow/short constraints realistically
* **Experiment registry**

  * create a `runs/` or `experiments/` index auto-generated from manifests, with a “do not cherry-pick” policy

### Longer-term: “institution-grade”

* **Data pipeline versioning**

  * dataset manifests (schema checksums, row counts, coverage stats)
  * QA reports as gating steps (fail build if schema/coverage drifts)
* **Reproducible environments**

  * lockfile (`uv.lock` / `poetry.lock`) + docker image for deterministic CI
* **Performance + scale**

  * fast IO for Parquet, vectorized event loop improvements, incremental caching
* **Audit-grade reporting**

  * full tear sheet: net/gross, exposures over time, factor betas rolling, capacity, stress periods

---

## 9. Resume-grade deliverables (figures/tables/artifacts + how to present)

Keep these **in-repo** (plots + markdown tables), generated from a **single locked WRDS run** plus the reproducible sample run:

1. **End-to-end pipeline diagram + invariants table**

   * “What guarantees exist?” (monotonic timestamps, t+1, portfolio guardrails, LOB FIFO) with pointers to the tests. ([Mateo Bodon][2])
2. **Out-of-sample equity curve (WRDS)**

   * show **gross vs net**, plus drawdown curve, and a caption with exact costs/leverage caps used.
3. **WFV fold stability figure**

   * distribution of per‑fold Sharpe/return/drawdown + selected params per fold (shows you didn’t overfit one window).
4. **Cost sensitivity heatmap**

   * Sharpe (or CAGR) vs {impact multiplier × spread multiplier} and/or vs turnover cap.
5. **Factor regression table (FF3/FF5+MOM)**

   * alpha, t‑stat (HAC), betas; plus a “this is mostly momentum beta” honesty line if that’s the truth. ([Mateo Bodon][5])
6. **Reality check + SPA summary table**

   * show p‑values for the strategy family you actually searched (don’t hide the selection step).
7. **Reproducibility evidence**

   * one snippet of `manifest.json` fields + hash of config + deterministic rerun claim backed by a CI check. ([Mateo Bodon][3])

How to present (so you don’t get grilled):

* Lead with: **“I built a leakage‑safe research backtester with deterministic artifacts + WFV + inference.”**
* Then show: **one** real-data result with **explicit protocol** + **baselines** + **cost assumptions**.
* Avoid: bragging about LOB microstructure realism if your flagship is a daily factor strategy—frame LOB as a modular capability, not the reason the alpha exists.

---

## 10. HANDOFF FOR CODEX (machine-readable)

```yaml
top_priority_tasks:
  - goal: "Publish a locked, rerun WRDS flagship walk-forward result with tightened risk + cost caps and updated docs (replace 'pre-tightening' metrics)."
    files_likely_touched:
      - "configs/wfv_flagship_wrds.yaml"
      - "configs/wfv_flagship_wrds_smoke.yaml"
      - "docs/results_wrds.md"
      - "project_state/CURRENT_RESULTS.md"
      - "reports/render_wrds_flagship.py"
      - "reports/analytics.py"
      - "Makefile"
    acceptance_criteria:
      - "A new WRDS run_id is documented in docs/results_wrds.md with: net & gross metrics, drawdown, turnover, cost breakdown, and inference (reality check + SPA)."
      - "Max drawdown is materially reduced vs the current documented ~82% (target: < 35–45% unless the strategy is explicitly levered; document caps if not)."
      - "docs/results_wrds.md explicitly states the evaluation protocol (train/val/test or WFV+holdout) and cost assumptions."
      - "No WRDS raw data is committed; only derived plots/tables."
    recommended_tests_or_commands:
      - "WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds"
      - "WRDS_DATA_ROOT=/path/to/wrds make report-wrds"
      - "pytest -q"

  - goal: "Add a final holdout evaluation path to prevent p-hacking (separate model selection from final reporting)."
    files_likely_touched:
      - "src/microalpha/walkforward.py"
      - "src/microalpha/config_wfv.py"
      - "configs/wfv_flagship_wrds.yaml"
      - "docs/reproducibility.md (or mkdocs page source)"
      - "tests/test_walkforward.py"
    acceptance_criteria:
      - "WFV config supports an explicit holdout window (date range) that is excluded from parameter optimization."
      - "Artifacts include an 'oos_holdout_metrics.json' and/or explicit tagging of holdout results."
      - "Tests confirm optimizer never reads holdout returns (fails if it does)."
    recommended_tests_or_commands:
      - "pytest -q tests/test_walkforward.py"
      - "microalpha wfv --config configs/wfv_flagship_sample.yaml --out artifacts/sample_wfv"

  - goal: "Fix factor regression frequency/alignment and eliminate documentation inconsistency (daily vs weekly sample factors)."
    files_likely_touched:
      - "data/factors/ff3_sample.csv"
      - "reports/factors_ff.py"
      - "src/microalpha/reporting/summary.py"
      - "docs/factors.md (or mkdocs page source)"
      - "tests/test_reporting_analytics.py"
    acceptance_criteria:
      - "Factor regression script detects factor/return frequency and aligns via explicit resampling (logged in output)."
      - "Docs state the true frequency of ff3_sample.csv and how alignment is handled."
      - "A test fails if factors and returns indexes are misaligned or if resampling silently changes sample length without reporting."
    recommended_tests_or_commands:
      - "python reports/factors_ff.py artifacts/sample_wfv/<RUN_ID> --factors data/factors/ff3_sample.csv --output /tmp/factors.md"
      - "pytest -q tests/test_reporting_analytics.py"

  - goal: "Add two red-team leakage tests that would catch common 'peek into the future' failure modes."
    files_likely_touched:
      - "tests/test_no_lookahead.py"
      - "tests/test_time_ordering.py"
      - "src/microalpha/engine.py"
      - "src/microalpha/portfolio.py"
    acceptance_criteria:
      - "Test 1: using a future-return-derived signal raises LookaheadError or fails an invariant deterministically."
      - "Test 2: disabling t+1 semantics (where possible) requires explicit unsafe flag; without it, run errors or warns and sets manifest.unsafe_execution=true."
    recommended_tests_or_commands:
      - "pytest -q tests/test_no_lookahead.py tests/test_time_ordering.py"

  - goal: "Make transaction cost reporting audit-grade: explicit net vs gross returns, cost breakdown, and cost sensitivity sweep."
    files_likely_touched:
      - "src/microalpha/metrics.py"
      - "src/microalpha/reporting/summary.py"
      - "src/microalpha/slippage.py"
      - "reports/analytics.py"
      - "tests/test_capital_and_slippage_integration.py"
    acceptance_criteria:
      - "Artifacts include a machine-readable cost breakdown (commission, slippage/impact, borrow) per day and in total."
      - "Summary markdown includes a cost table and net/gross Sharpe/CAGR/drawdown."
      - "A simple cost-multiplier sweep utility exists and writes a CSV/plot (not required in CI)."
    recommended_tests_or_commands:
      - "pytest -q tests/test_capital_and_slippage_integration.py"
      - "microalpha report --artifact-dir artifacts/sample_flagship"

  - goal: "Fix CONFIG_REFERENCE.md to use repo-relative paths and include a short per-config 'what this config is for' note."
    files_likely_touched:
      - "tools/render_project_state_docs.py"
      - "project_state/CONFIG_REFERENCE.md"
      - "configs/*.yaml"
    acceptance_criteria:
      - "CONFIG_REFERENCE.md contains paths like 'configs/wfv_flagship_wrds.yaml' (no '/Users/...')."
      - "Each config row includes: purpose tag (single-run vs wfv vs wrds) and the key risk/cost parameters surfaced (turnover cap, leverage cap, exec type)."
    recommended_tests_or_commands:
      - "python tools/render_project_state_docs.py"
      - "pytest -q"

  - goal: "Create a benchmark baseline strategy and report comparison table (flagship vs canonical momentum vs market/neutral baseline)."
    files_likely_touched:
      - "src/microalpha/strategies/cs_momentum.py"
      - "src/microalpha/strategies/flagship_mom.py"
      - "reports/analytics.py"
      - "docs/flagship_strategy.md (or mkdocs page source)"
      - "tests/test_strategies.py"
    acceptance_criteria:
      - "Repo can generate a baseline momentum backtest with minimal params (e.g., pure 12-1 ranking, equal-weight, monthly rebalance)."
      - "Report includes a table comparing net performance metrics + factor regression alpha for baseline vs flagship."
      - "Baseline implementation is simple and clearly documented to avoid accusations of cherry-picking."
    recommended_tests_or_commands:
      - "pytest -q tests/test_strategies.py"
      - "microalpha run --config configs/flagship_sample.yaml --out artifacts/sample_flagship"

  - goal: "Add a lightweight experiment registry (manifest index) to prevent cherry-picking and document what was tried."
    files_likely_touched:
      - "src/microalpha/manifest.py"
      - "reports/generate_summary.py"
      - "reports/wfv_report.py"
      - "docs/reproducibility.md (or mkdocs page source)"
    acceptance_criteria:
      - "A script can scan artifacts/*/manifest.json and emit a runs_index.csv with run_id, git_sha, config_sha256, key metrics."
      - "Docs include 'how to interpret runs_index' and encourage committing the index for sample runs."
      - "Index generation is deterministic and CI-safe for sample artifacts."
    recommended_tests_or_commands:
      - "python reports/generate_summary.py --artifacts-root artifacts --output reports/summaries/runs_index.csv"
      - "pytest -q"

  - goal: "CI hardening: ensure sample 'make sample', 'make wfv', and 'make report' produce deterministic artifacts and docs build."
    files_likely_touched:
      - ".github/workflows/*.yml"
      - "Makefile"
      - "tests/test_determinism.py"
      - "mkdocs.yml"
    acceptance_criteria:
      - "CI runs pytest, then executes sample run + report, and fails if key artifact hashes drift unexpectedly."
      - "MkDocs build succeeds and includes updated summaries."
      - "CI does NOT attempt WRDS targets."
    recommended_tests_or_commands:
      - "make test"
      - "make sample"
      - "make wfv"
      - "make report"
      - "mkdocs build"
```

[1]: https://mateobodon.github.io/microalpha/flagship_strategy/ "Flagship Strategy - Microalpha"
[2]: https://mateobodon.github.io/microalpha/leakage-safety/ "Leakage Safety - Microalpha"
[3]: https://mateobodon.github.io/microalpha/reproducibility/ "Reproducibility - Microalpha"
[4]: https://mateobodon.github.io/microalpha/wrds/ "WRDS & Real Data - Microalpha"
[5]: https://mateobodon.github.io/microalpha/factors/ "Factors - Microalpha"
