# microalpha — MASTER PLAN (control tower)

## Verified current state (from repo/docs)

- Core system is an **event-driven backtesting engine** with canonical boundaries: DataHandler → Engine → Strategy → Portfolio → Broker/Execution. (`project_state/ARCHITECTURE.md`)
- Supports **walk-forward validation (WFV)** with per-fold grid search + bootstrapped reality-check. (`project_state/PIPELINE_FLOW.md`, `project_state/RESEARCH_NOTES.md`)
- Reporting already produces **artifact-backed outputs**: metrics/bootstraps/equity/trades + PNG/Markdown summaries; WRDS pipeline has analytics + factor regressions + SPA tooling (guarded). (`project_state/PIPELINE_FLOW.md`, `project_state/DATAFLOW.md`)
- Repo emphasizes **research hygiene**: chronology enforcement, t+1 fills, lookahead guards, deterministic sample fixtures, and a broad pytest suite (~70 tests; ~78% coverage reported). (`project_state/RESEARCH_NOTES.md`, `project_state/TEST_COVERAGE.md`, `project_state/CURRENT_RESULTS.md`)
- Credibility gaps are explicitly documented:
  - WRDS artifacts are **stale/incomplete** (latest `artifacts/wrds_flagship/*` missing `metrics.json`/`folds.json`); docs reference pre-tightening runs. (`project_state/KNOWN_ISSUES.md`, `project_state/CURRENT_RESULTS.md`)
  - **Transaction-cost realism is fragile** when metadata is missing (fallback defaults). (`project_state/KNOWN_ISSUES.md`, `project_state/OPEN_QUESTIONS.md`)
  - **SPA vs Reality Check coherence** is an open question (selection vs evaluation ambiguity). (`project_state/OPEN_QUESTIONS.md`)

## Targets / Plan (what “resume-grade” means here)

**North star:** ship a *reviewer-runnable* research platform **plus** a *defensible real-data case study* with artifact-backed metrics that survive skeptical interview scrutiny:
- net of costs (and cost sensitivity)
- leakage-safe (explicit delays + survivorship/delisting handling)
- out-of-sample + locked-box holdout
- baselines + incremental value
- stability across time buckets/regimes
- reproducible run manifests + committed derived artifacts (never licensed raw data)

---

## North-star evaluation protocol (defensible, leakage-safe)

### Dataset / universe definition (WRDS/CRSP)
- **Primary dataset:** WRDS CRSP DSF daily stock file exports + security master; include delisting returns in total return series (export pipeline already exists). (`project_state/DATAFLOW.md`)
- **Universe contract (example, pre-registered):**
  - Common stocks only (e.g., CRSP SHRCD 10/11; exchanges 1/2/3) — exact filter must be recorded in the run manifest.
  - Liquidity + price filters applied with **as-of availability** (e.g., ADV/price computed from trailing windows, not future data).
  - Sector classification: whichever mapping you use (SIC→industry / GICS if available) must be *time-consistent* and documented.
- **Data delays (hard rule):**
  - Signals built using data up to *t*; trades fill at *t+1* (already supported/tested in engine semantics). (`project_state/RESEARCH_NOTES.md`, `project_state/TEST_COVERAGE.md`)

### Leakage controls (must be explicit)
- No lookahead: monotonic timestamps + explicit “no peek” tests (already exists).
- No survivorship bias: universe formation must be reproducible from security master; delist handling must be audited and surfaced.
- No parameter leakage: parameter selection confined to training folds; locked-box holdout never used for tuning.

### Out-of-sample design (WFV + locked-box)
- **WFV (rolling):** fixed schedule (e.g., 5y train / 1y test) with parameters selected *inside* each training window only.
- **Locked-box holdout:** final period (e.g., last 2–3 years) excluded from any iteration; only evaluated once the pipeline is “frozen”.
- **Pre-registration artifact:** commit config + grid + fold schedule hash in each run’s `manifest.json`.

### Costs + realism contract (must be reported)
- Report **net-of-cost** metrics by default (already true in engine).
- Publish **cost sensitivity** (spread/impact/borrow multipliers) and **metadata coverage** (how often fallbacks were used).
- Report **capacity/participation** (%ADV) and concentration (largest positions, sector heat).

### Baseline ladder (must always be shown)
At minimum, compare against:
1) buy/hold benchmark (or market index proxy),
2) naive long-only momentum (same signal, long-only, monthly),
3) naive market-neutral momentum (equal-weight long-short, same universe),
4) “no-cost” vs “with-cost” variants,
5) random-signal placebo (sanity).

---

## Roadmap milestones (prioritized for resume impact + interview defensibility)

### Phase 0 (Week 0–2): Credibility scaffolding (reviewer-friendly, no new alpha claims)

#### M0.1 — Make “fixtures vs research” distinction unavoidable
- Goal + rationale:
  - Prevent first-impression damage from the intentionally poor sample fixture metrics; make the repo read as a **research platform** first, and a **case study** second.
- Scope boundaries:
  - No new strategy logic; no WRDS rerun required.
- Risks / failure modes:
  - Over-indexing on presentation without improving defensibility metrics.
- Validation:
  - Docs build (`mkdocs build`) and README link checks (already tested).
- Artifact-backed metric(s) produced:
  - “Results index” page that enumerates artifact runs with labels: `fixture` vs `research` + config hash.

#### M0.2 — Default cost sensitivity + metadata coverage reporting (core defensibility)
- Goal + rationale:
  - Make it impossible to overclaim alpha by hiding optimistic costs; expose fragility early.
- Scope boundaries:
  - Do **not** calibrate execution/queue models yet; do not re-run WFV inside this milestone.
- Risks / failure modes:
  - Reveals strategy is cost-fragile (acceptable; improves honesty/defensibility).
  - Implementation becomes “post-hoc re-run” instead of transparent sensitivity.
- Validation:
  - New unit tests for report schema + deterministic sample report regeneration.
- Artifact-backed metric(s) produced:
  - `cost_sensitivity.json` (net SR / MaxDD / cost drag across multipliers).
  - `metadata_coverage.json` (ADV/spread/borrow coverage and fallback rates).

#### M0.3 — Data hygiene report (survivorship, missingness, monotonicity)
- Goal + rationale:
  - Answer the skeptical interviewer: “How do you know your data isn’t broken / biased?”
- Scope boundaries:
  - Only schema + sanity validation; not rewriting the WRDS exporter.
- Risks / failure modes:
  - Uncovers issues that require pipeline refactors (good to surface early).
- Validation:
  - CI runnable using bundled sample/public data; WRDS checks run when data present.
- Artifact-backed metric(s) produced:
  - `data_hygiene.json` + a short Markdown summary embedded into WRDS results docs.

---

### Phase 1 (Weeks 2–6): Refresh a real-data WRDS flagship case study (one “resume run”)

#### M1.1 — Complete WRDS smoke WFV run under tightened caps (fast loop)
- Goal + rationale:
  - Prove the pipeline is end-to-end healthy on realistic data before spending hours on full 2005–2024.
- Scope boundaries:
  - Fixed (smoke) window only; small grid only; no new models.
- Risks / failure modes:
  - Runtime still too slow; zero-trade silent failures.
- Validation:
  - Fail-fast diagnostics for “no trades / no signals”; store diagnostics in artifacts.
- Artifact-backed metric(s) produced:
  - OOS net Sharpe_HAC, MaxDD, turnover, cost drag + sensitivity table.

#### M1.2 — Full WRDS WFV run (2005–2024) with complete artifacts
- Goal + rationale:
  - Produce the *one* defensible headline results bundle: WFV folds + SPA + factor attribution + cost/capacity robustness.
- Scope boundaries:
  - No strategy fishing: keep the grid small and pre-registered; do not iterate on holdout.
- Risks / failure modes:
  - Long runtime / abort leaving partial artifacts (known issue).
  - Large drawdowns persist (needs risk-control follow-up).
- Validation:
  - Ensure artifacts include `metrics.json`, `folds.json`, `grid_returns.csv`, `spa.json`, factor regression MD, and plots.
  - Sanity: folds > 0 trades; no NaNs in returns; cost drag non-zero.
- Artifact-backed metric(s) produced:
  - Fold distribution: median/worst Sharpe, %folds positive, worst drawdown.
  - SPA p-value + Reality Check p-value (selection stage only).
  - Factor alpha (FF5+MOM) with HAC t-stats.

---

### Phase 2 (Months 2–3): Statistical inference contract + locked-box holdout

#### M2.1 — Write and enforce the “selection vs evaluation” inference contract
- Goal + rationale:
  - Make SPA / Reality Check ungameable by clearly defining what object each test is applied to and when.
- Scope boundaries:
  - No new statistical tests beyond consolidating usage; no fishing for lower p-values.
- Risks / failure modes:
  - Realizing one test is redundant or misapplied; may need to drop/re-scope.
- Validation:
  - Unit test asserting: selection inference uses training-only grid returns; OOS metrics are reported separately.
- Artifact-backed metric(s) produced:
  - `inference_contract.json` (config + hashes + which tests ran on which data slices).

#### M2.2 — Add locked-box holdout and report it separately
- Goal + rationale:
  - Prevent subtle overfitting through repeated WFV iteration; improve interview defensibility dramatically.
- Scope boundaries:
  - Holdout is *read-only* until the pipeline is frozen.
- Risks / failure modes:
  - Holdout underperforms (still valuable; shows honesty and proper process).
- Validation:
  - Run manifest must tag holdout dates; tests ensure holdout data never appears in training folds.
- Artifact-backed metric(s) produced:
  - `holdout_metrics.json` + plots; displayed as separate section in docs/results.

---

### Phase 3 (Months 3–6): Robustness + capacity (what skeptics ask next)

#### M3.1 — Regime / time-bucket stability suite
- Goal + rationale:
  - Show robustness across decades and major regimes (2008, 2020, rate regimes, etc.).
- Scope boundaries:
  - No new signals; purely reporting + slicing.
- Risks / failure modes:
  - Results dominated by one era; must be shown transparently.
- Validation:
  - Deterministic slicing from `equity_curve.csv`; tests for slice boundary correctness.
- Artifact-backed metric(s) produced:
  - `regime_metrics.csv` (Sharpe/MaxDD/turnover by era) + summary plots.

#### M3.2 — Capacity & liquidity stress test
- Goal + rationale:
  - Demonstrate scaling realism: participation rates, concentration, and cost convexity.
- Scope boundaries:
  - Not calibrating to real LOB data; stick to conservative stress assumptions.
- Risks / failure modes:
  - Requires reliable ADV/spread coverage; may trigger data pipeline work.
- Validation:
  - Report `% trades > X% ADV`, and ensure missing ADV is surfaced as “unknown” not silently defaulted.
- Artifact-backed metric(s) produced:
  - `capacity_report.json` + plots: participation distribution, cost drag vs AUM scale.

---

### Phase 4 (Months 6–12): Performance engineering + optional C++ “credibility booster”

#### M4.1 — Publish and guard performance baselines
- Goal + rationale:
  - Quant-dev credibility: events/sec, runtime per fold, memory; prevent regressions.
- Scope boundaries:
  - No premature optimization; focus on measurement + guardrails first.
- Risks / failure modes:
  - Noisy benchmarks; mitigate via relative thresholds and fixed dataset sizes.
- Validation:
  - Benchmarks runnable locally; optional nightly CI job.
- Artifact-backed metric(s) produced:
  - `benchmarks/results.json` (events/sec, runtime, memory) compared to last tagged baseline.

#### M4.2 (Optional) — C++ acceleration module for a hot path
- Goal + rationale:
  - If targeting C++ quant dev roles: demonstrate API design + performance profiling + integration discipline.
- Scope boundaries:
  - One small component only (e.g., bootstrap resampling kernel, rolling stats, or order-book simulator).
- Risks / failure modes:
  - Build portability complexity; distraction from research outputs.
- Validation:
  - Micro-benchmark speedup + correctness parity tests.
- Artifact-backed metric(s) produced:
  - “Speedup vs pure Python” benchmark with CI-visible results.

---

## “Done means done” (artifact-backed metrics contract)

A milestone is only “done” when:
- a **new artifact file** exists under `artifacts/<run>/<RUN_ID>/` or `reports/` (JSON/CSV/PNG/MD),
- the artifact is **linked** from docs/README (or results index),
- tests validate presence + schema (when applicable),
- and the metric is explicitly labeled **fixture** vs **research** and **current** vs **target**.
