# microalpha – Long‑Term Repo Plan

## 0. Context and current state

microalpha is a leakage‑safe, event‑driven backtesting engine with walk‑forward cross‑validation, bootstrap reality checks, and a reporting/Docs pipeline (MkDocs + GitHub Pages). Sample runs are wired up with deterministic artefacts under `artifacts/`, and the README exposes bundled sample metrics and FF3 factor regressions. :contentReference[oaicite:0]{index=0}  

### Current strengths

- Event‑driven engine with `DataHandler → Engine → Strategy → Portfolio → Broker`, t+1 semantics, and leakage tests. :contentReference[oaicite:1]{index=1}  
- Walk‑forward CV, Politis–White bootstrap, HAC Sharpe, and factor regression tooling. :contentReference[oaicite:2]{index=2}  
- Sample and public data bundles, WRDS config stubs, FF3 factor sample. :contentReference[oaicite:3]{index=3}  
- MkDocs docs site (flagship strategy, leakage safety, WRDS guide, factors, API), plus 70+ tests and CI gates. :contentReference[oaicite:4]{index=4}  
- Codex integration already started (`.codex/` directory, existing `AGENTS.md`, `Plan.md`). :contentReference[oaicite:5]{index=5}  

### Latest visible run data (sample bundle)

From `README.md` (sample data bundle): :contentReference[oaicite:6]{index=6}  

- Single flagship backtest (sample config):
  - Sharpe (HAC): **−0.66**
  - MAR: **−0.41**
  - Max DD: **17.26%**
  - RealityCheck p‑value: **0.861**
  - Turnover: **\$1.21M**
- Walk‑forward flagship (sample config):
  - Sharpe (HAC): **0.22**
  - MAR: **0.03**
  - Max DD: **34.79%**
  - RealityCheck p‑value: **1.000**
  - Turnover: **\$28.53M**

Factor regression on FF3 sample:

- Alpha ≈ −0.55% (t ≈ −1.42), modest/inconclusive exposures to Mkt_RF, SMB, HML.

These are demo‑metrics on toy panels, not “showcase this on a resume” numbers. Real WRDS results are architected but not surfaced prominently.

---

## 1. High‑level goals (6–12 months)

1. **Turn microalpha into a canonical example of serious quant research hygiene**  
   – leakage‑safe engine, walk‑forward, bootstrap reality checks, factor regressions.

2. **Anchor the repo around 1–2 WRDS case studies with credible numbers**  
   – e.g., CRSP momentum study with out‑of‑sample Sharpe, factor‑neutralised alphas, and SPA/reality‑check p‑values.

3. **Demonstrate engine generality with multiple strategies**  
   – momentum, value, quality / low‑vol, all sharing the same infra.

4. **Make the repo “agent‑native”**  
   – Codex‑friendly `AGENTS.md`, a clear `Plan.md`, and a Codex config that lets GPT‑5.1‑Codex‑Max iterate, test, and commit safely.

5. **Package the story for hiring managers**  
   – polished docs page + notebook, plus bullet‑ready metrics and methodology.

---

## 2. Phase 0 – Scaffolding & agent setup (NOW)

**Objective:** Give both you and Codex a clear, up‑to‑date map of the project and expectations.

### 2.1 Align plan & docs

- Replace the existing `Plan.md` with this long‑term plan (or move this to `docs/plan.md` and keep `Plan.md` as a slim “current sprint” file).
- Add cross‑link from README → full plan (`docs/plan.md`) for humans.
- Add link from `AGENTS.md` → `docs/plan.md` so agents can find the roadmap.

**Deliverables**

- `Plan.md` (or `docs/plan.md`) updated.
- README “Project roadmap” section with a single link.
- `AGENTS.md` “Project roadmap” bullet linking to the plan.

### 2.2 Agent‑native instructions

You already have an `AGENTS.md` file; we’ll replace it with a tighter, Codex‑optimized version (see section 3 below):

- Clear sections: Core commands, Project structure, Code style, Tests, WRDS data rules, Git workflow, Agent behaviour, Boundaries.
- Make sure it:
  - Explicitly tells agents to read `AGENTS.md` + `Plan.md` before touching code.
  - Defines which tests to run by default (`pytest -q`, `make sample`, etc.).
  - Defines additional tests for WRDS (e.g., `pytest -m wrds` and/or `make wfv-wrds` for local‑only).

**Deliverables**

- New `AGENTS.md` in repo root, agent‑focused, concise, and up to date.

---

## 3. Phase 1 – WRDS flagship momentum study

**Objective:** One serious WRDS/CRSP momentum case study that is clean enough to show on a resume.

### 3.1 Data pipeline & contracts

**Tasks**

1. Finalize WRDS export spec:
   - CRSP daily or monthly returns for US common shares.
   - Universe filter (e.g., `SHRCD` ∈ {10, 11}, `EXCHCD` in {1, 2, 3}, price > \$5, ADV filter).
   - Include delisting returns, sector/industry classification.
2. Document this contract in `docs/wrds.md` and reference in `configs/wfv_flagship_wrds.yaml`.
3. Add a thin `scripts/export_wrds_*.py` or just a docs snippet for the WRDS SQL you actually use (without credentials).

**Deliverables**

- `docs/wrds.md` updated with exact schema and universe filters.
- `configs/wfv_flagship_wrds.yaml` matching real file paths and schema.
- If you want: a private `scripts/wrds_export.sql` (ignored by git).

### 3.2 Strategy specification (flagship momentum)

Use your current flagship as the canonical study, but *pin it down precisely*:

- 12–1 momentum, monthly rebalance.
- Sector‑neutral, equal or risk‑parity weights.
- Constraints:
  - Max weight per name (e.g., 2%).
  - ADV capacity (e.g., trade ≤ 5% of ADV/day).
  - Borrow constraints for shorts (e.g., skip non‑shortable names).
- Execution model:
  - TWAP over N slices with square‑root or Kyle impact.
  - Fee model + spread.

**Tasks**

1. Encode this clearly in `configs/wfv_flagship_wrds.yaml`.
2. Add a small doc section `docs/flagship_momentum_wrds.md` describing exactly this design.

**Deliverables**

- Updated WRDS config with explicit hyperparams.
- Short doc page describing the WRDS flagship strategy.

### 3.3 Walk‑forward and hyperparameter search

**Tasks**

1. Choose a realistic timeframe, e.g.:

   - In‑sample start: 2005‑01‑01  
   - Out‑of‑sample end: 2024‑12‑31  
   - Train window: 36 months, Test window: 12 months.

2. Define a small hyperparameter grid, e.g.:

   - Lookback: {9, 12, 18 months}
   - Skip (formation gap): {1, 2 months}
   - Top quantile: {20%, 30%}
   - Weighting: {equal, risk‑parity}

3. Configure `microalpha wfv` (through YAML) to:

   - Run walk‑forward over the entire period.
   - Log per‑fold metrics, exposures, turnover.
   - Save grid results somewhere like `artifacts/wrds_flagship/<RUN_ID>/grid_results.csv`.

4. Optionally, add a thin `scripts/run_wfv_wrds.py` that just calls into your CLI runner with the correct config.

**Deliverables**

- Reproducible command (e.g., `make wfv-wrds`) that runs full WRDS momentum WFV and writes artefacts under `artifacts/wrds_flagship/<RUN_ID>`.

### 3.4 Statistical analysis & robustness

**Tasks**

1. For the chosen “winner” configuration (based on train folds only):

   - Compute **out‑of‑sample only** performance:
     - Annualised return, vol, Sharpe (HAC).
     - Max drawdown, Calmar, Sortino.
     - Turnover, average holding period.
   - Compute SPA / reality‑check p‑value across the grid using your bootstrap tooling.
   - Run factor regression vs at least FF5 + momentum using HAC standard errors.

2. Save outputs:

   - `metrics.json` (per‑run summary).
   - `bootstrap.json` (distribution of Sharpe / alpha).
   - `factor_exposure.csv` (alpha + factor betas, t‑stats).
   - `exposures.csv` (sector/style exposures).

3. Add a summary Markdown file:

   - `reports/summaries/wrds_flagship_mom_wfv.md`  
   - This should aggregate metrics, p‑values, factor exposures, and embed image links.

**Deliverables**

- Complete metrics/factors in `artifacts/wrds_flagship/<RUN_ID>/`.
- One summary Markdown report wired into docs.

### 3.5 Docs and notebooks

**Tasks**

1. Create `docs/results_wrds.md` (or update the existing stub) to:

   - Describe the WRDS experiment (universe, period, strategy).
   - Show key tables and plots (equity curve, drawdowns, factor table, SPA p‑values).
   - Link to artefact directory (paths only; no data).

2. Add a notebook `notebooks/wrds_flagship_mom.ipynb` that:

   - Loads `metrics.json`, `bootstrap.json`, `factor_exposure.csv`.
   - Produces the key plots locally.
   - Reads test/train windows from WFV output and verifies out‑of‑sample splits.

**Deliverables**

- Docs page summarising the WRDS flagship.
- Notebook for interactive exploration.

---

## 4. Phase 2 – Additional strategies & cross‑strategy comparison

**Objective:** Show that microalpha supports multiple strategies with shared infra.

### 4.1 Implement 1–2 additional WRDS strategies

Candidates:

- **Value**: B/M or E/P, sector‑neutral, rebalanced annually or quarterly.
- **Quality**: profitability / accruals / ROE.
- **Low‑Vol**: low‑beta, min‑vol portfolio with leverage caps.

**Tasks**

1. Add configs:

   - `configs/wfv_value_wrds.yaml`
   - `configs/wfv_quality_wrds.yaml`

2. Reuse the same WFV set‑up as momentum (period, train/test windows).

3. Run full WFV and reporting for each strategy.

**Deliverables**

- Artefacts for each strategy under `artifacts/wrds_value/…`, `artifacts/wrds_quality/…`.
- Summary Markdown reports in `reports/summaries/`.

### 4.2 Cross‑strategy comparison report

**Tasks**

1. Add a doc page `docs/strategy_comparison_wrds.md`:

   - Table comparing: momentum vs value vs quality (return, vol, Sharpe, DD, turnover).
   - Factor exposures table per strategy.
   - SPA / reality‑check output summarised (which strategies survive).
   - Commentary on capacity and robustness.

2. Optionally, add a combined portfolio config (e.g., equal‑risk blend of the top two strategies) and treat that as another experiment.

**Deliverables**

- Cross‑strategy comparison doc.
- (Optional) Config and artefacts for a combined portfolio.

---

## 5. Phase 3 – Microstructure & execution modelling

**Objective:** Demonstrate that microalpha can handle more realistic execution (LOB, queueing, impact).

### 5.1 LOB / intraday example

If your engine already supports an LOB executor, create:

- `data_sp500` or similar intraday snapshot / TAQ‑like sample (non‑proprietary or synthetic).
- `configs/flagship_lob_sample.yaml` using that data.

**Tasks**

1. Build a small LOB backtest (maybe on public data or a synthetic orderbook):

   - Basic market‑making or liquidity‑seeking strategy with queue position tracking.
   - Latency assumptions, partial fills.

2. Add relevant tests:

   - `test_lob_fifo`, `test_lob_partial_fills`, `test_lob_tplus1`.

3. Write a doc `docs/lob_execution.md` that:

   - Explains assumptions and queue model.
   - Shows a few metrics (slippage, fill rates, queue cancellation rates).

**Deliverables**

- LOB sample config and artefacts.
- LOB execution docs + tests.

---

## 6. Phase 4 – Performance, CI & observability

**Objective:** Make the project feel robust and “production‑adjacent”.

### 6.1 Test suite & coverage

**Tasks**

1. Add test markers:

   - `@pytest.mark.wrds` for tests that require WRDS/CRSP.
   - `@pytest.mark.slow` for heavy WFV runs.

2. Update `pytest.ini` to:

   - Skip `wrds` and `slow` by default.
   - Provide instructions (`pytest -m wrds` etc.).

3. Add Make targets:

   - `make test` → fast unit tests, no WRDS.
   - `make test-all` → includes slow WFV but still synthetic/public.
   - `make test-wrds` → local‑only WRDS tests (skipped in CI).

**Deliverables**

- Clear separation between CI‑safe tests and local heavy tests.
- Higher coverage on critical components (engine, strategies, reports).

### 6.2 Observability & logging

**Tasks**

1. Ensure each run writes:

   - `metrics.json`
   - `bootstrap.json`
   - `factor_exposure.csv`
   - `trades.jsonl`

2. Add per‑run `manifest.json` including:

   - Git SHA.
   - Config path.
   - Run timestamp.
   - Model hyperparameters.

3. If desired, enable Codex’s OpenTelemetry logging for your own runs (see config snippet below). :contentReference[oaicite:7]{index=7}  

**Deliverables**

- Standardised artefact schema and manifest.
- Easier offline analysis for you (and for Codex to reason about runs).

---

## 7. Phase 5 – Docs, notebooks, and “interview ready” story

**Objective:** Make it trivial for a hiring manager to understand what you’ve built and what the results are.

### 7.1 Docs clean‑up

**Tasks**

1. Update `README.md`:

   - Keep current sample results.
   - Add a new “WRDS results (flagship momentum)” table with key metrics and a link to the full report.
   - Add a “Multi‑strategy WRDS comparison” section that briefly summarises differences.

2. Ensure docs nav includes:

   - Flagship WRDS page.
   - Strategy comparison page.
   - LOB execution (if implemented).
   - Plan/roadmap page.

**Deliverables**

- README that clearly surfaces the WRDS story.
- Docs nav that supports an interviewer skimming in 2–3 minutes.

### 7.2 Notebooks as “visual CV”

**Tasks**

- For each major study, produce a notebook:

  - `notebooks/wrds_flagship_mom.ipynb`
  - `notebooks/wrds_value_vs_mom.ipynb`

- Each should:
  - Load artefacts and generate plots.
  - Include a short narrative.

**Deliverables**

- A small set of polished notebooks you can screenshare in interviews.

---

## 8. Phase 6 – Automation with Codex

**Objective:** Build a workflow where GPT‑5.1‑Codex‑Max can implement roadmap tasks safely.

**Tasks**

1. Maintain `AGENTS.md` and `Plan.md` as the “source of truth” for Codex.
2. Configure `~/.codex/config.toml` with:
   - Default model `gpt-5.1-codex-max`.
   - Reasoning effort tuned for long tasks (`medium` or `high`).
   - Sandbox/workspace settings appropriate for your comfort level (see config in section 4).
   - `web_search_request = true` for model‑initiated web access. :contentReference[oaicite:8]{index=8}  
3. Optionally add `.codex/policy/*.codexpolicy` to gate dangerous commands (`git push`, mass deletes, etc.). :contentReference[oaicite:9]{index=9}  

**Deliverables**

- Codex profile dedicated to `microalpha`.
- Policies so Codex can run tests, edit files, and commit—but doesn’t silently do anything insane.

---

## 9. Phase 7 – Resume / narrative polish

Once the above is done, you have enough to:

- Write ~2–3 strong bullets for your quant CV.
- Link directly to:
  - README,
  - WRDS results page,
  - a flagship notebook.

This is where you harvest the work.

