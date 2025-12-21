# PLAN OF RECORD — microalpha

**Date:** 2025-12-20  
**Purpose:** A hard contract for *resume-credible* evidence. If a result is not produced under this protocol, it does **not** get marketed as “alpha.”

---

## 0) What this repo is trying to prove (core claim)

**Core claim (allowed):**
- microalpha is a **leakage-safe, deterministic, event-driven research backtester** with **walk-forward validation** and **proper inference outputs** (e.g., HAC Sharpe, bootstrap reality check/SPA where applicable).
- The repo can produce **reproducible artifacts** (manifested configs + deterministic trade logs) that allow an interviewer to audit *what ran*.

**Core claim (not allowed yet):**
- “I found alpha” on WRDS/CRSP — not until we have **one locked protocol run** with **baselines + costs + risk caps + holdout** and the evidence survives scrutiny.

---

## 1) Estimand + target metrics (what we’re measuring)

**Estimand (primary):**
- **Out-of-sample (OOS) net returns** of a pre-registered strategy family under a fixed execution + cost + risk framework, evaluated via walk-forward + a final holdout.

**Primary metrics (must be reported on OOS stream only):**
- **Sharpe (HAC/Newey–West)**, CAGR, annualized vol
- **Max drawdown**, Calmar/MAR
- **Turnover** (and turnover cap binding %), gross exposure, net exposure
- **Cost breakdown** (spread/impact/fees/borrow) and net vs gross performance

**Inference outputs (must be shown, not hidden):**
- Strategy-family selection guardrail outputs:
  - **Bootstrap “reality check” p-value** over the searched family
  - **SPA** p-value if implemented/available for the same family
- Factor attribution:
  - **FF3/FF5 + MOM** regression: alpha, t-stat (HAC), betas (same frequency alignment)

---

## 2) Baselines (non-negotiable)

We will always compare the “flagship” variant against:

1. **Canonical cross-sectional momentum baseline**
   - Simple 12–1 momentum rank, monthly rebalance, equal-weight long/short (or long-only if shorting constraints)
2. **No-signal baseline**
   - Dollar-neutral random ranks (seeded) or “flat” (no trades) to sanity-check cost/turnover plumbing
3. **Market proxy**
   - SPY / market return (if available), or CRSP value-weighted market return series if already in data exports
4. **Factor benchmark**
   - FF MOM factor exposure / alpha attribution (not “proof”, just honesty)

---

## 3) Evaluation protocol (pre-registered; do not deviate without updating this doc)

### 3.1 Data + bias controls (WRDS/CRSP path)
- **No raw WRDS data committed**. Local-only under `WRDS_DATA_ROOT`.
- Universe construction must be **date-conditional** (no survivorship via “today’s constituents”).
- Corporate actions / delistings must be handled consistently (explicit QA checks in exporter).

### 3.2 Time semantics + leakage constraints
- **t+1 execution** by default for daily strategies.
- Any “unsafe” mode (same-tick fills, etc.) must:
  - require explicit opt-in in config
  - be written into `manifest.json` as `unsafe_execution: true`
  - be flagged in the report header

### 3.3 Costs + constraints (must be explicit in config + reported)
- Execution model: **TWAP/VWAP/IS** (whatever repo supports), but must specify:
  - spread floor
  - impact model (linear / sqrt) and parameters
  - borrow rate model (for shorts)
- Risk controls (hard caps, not vibes):
  - max gross leverage
  - max single-name weight
  - sector exposure caps (if sector neutral)
  - volatility targeting (optional, but strongly recommended)
  - ADV-linked turnover clamp (must show when it binds)

### 3.4 Split logic (WFV + holdout)
We use three tiers:

- **Train**: compute signals/features; fit any needed transforms
- **WFV selection**: optimize over a *pre-declared small grid* using WFV train windows only
- **Final holdout**: a fixed OOS date range **never used for selection**  
  - One-shot evaluation. No reruns after peeking (if rerun needed for bugfix, document “why” and keep the old run).

### 3.5 Robustness checklist (minimum)
For the final “resume run” we must include:
- **Cost sensitivity sweep**: multipliers ∈ {0.5, 1, 2, 4} on spread/impact
- **Universe variants**: at least 2 (e.g., top 500 vs top 1000 by mkt cap/liquidity)
- **Subperiod stability**: at least 3 regimes (pre-crisis / crisis / post-crisis or similar)
- **Capacity proxy**: turnover vs ADV; show if strategy collapses at realistic scale

---

## 4) What counts as “resume-credible” (gating criteria)

A run is “resume-credible” only if ALL are true:

- ✅ Leakage tests pass (timestamp monotonicity, t+1 execution, no backdated signals)
- ✅ Baselines included and run under the same costs/constraints
- ✅ Protocol frozen in-repo (this file + config hashes recorded in manifest)
- ✅ OOS-only metrics reported (no in-sample cherry-picked plots)
- ✅ Real-data smoke run executed (WRDS exports), or explicitly documented as blocked
- ✅ Artifacts reproducible from commands (documented below)
- ✅ Results are not obviously degenerate (e.g., max DD > ~50% without an explicit leverage rationale)

---

## 5) Roadmap with commands + expected artifacts

### 5.1 Next 1–2 weeks (validity + one credible demo run)

**(A) Tighten risk/cost caps + add WRDS smoke config**
- Commands:
  - `pytest -q`
  - `make sample && make report`
  - `WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds` *(or smoke target if available)*
  - `WRDS_DATA_ROOT=/path/to/wrds make report-wrds`
- Expected artifacts:
  - `artifacts/<run_id>/manifest.json` (git SHA, config hash, seeds, unsafe flags)
  - `artifacts/<run_id>/metrics.json` (gross+net)
  - `artifacts/<run_id>/equity_curve.csv`, `trades.jsonl`
  - `artifacts/<run_id>/bootstrap*.json` (reality check / SPA outputs)
  - `artifacts/<run_id>/report/*` (tearsheet plots + summary markdown)

**(B) Add holdout evaluation path**
- Commands:
  - `microalpha wfv --config configs/wfv_flagship_*.yaml --out artifacts/...`
- Expected artifacts:
  - `artifacts/<run_id>/oos_returns.csv` (explicit OOS stream)
  - `artifacts/<run_id>/holdout_metrics.json` (locked)

**(C) Baseline strategy + comparison table**
- Commands:
  - `microalpha run --config configs/baseline_mom_*.yaml --out artifacts/...`
  - `microalpha report --artifact-dir artifacts/...`
- Expected artifacts:
  - `reports/tables/baseline_vs_flagship.md`
  - `reports/figures/equity_overlay.png`

### 5.2 Next 4–8 weeks (full grid + robustness)

- Robustness grid: universe × rebalance freq × neutralization × cost multipliers
- Capacity analysis: turnover vs ADV, slippage calibration
- Multiple testing discipline: pre-register the model family; report reality-check/SPA for the family
- Experiment registry: auto index of manifests to prevent cherry-picking

### 5.3 Longer-term (institution-grade)

- Dataset QA gates + schema checksums
- Fully reproducible environment (lockfile, container, CI parity)
- Audit-grade reporting: rolling betas, exposure heatmaps, stress periods
- Speed/scalability improvements (parquet, caching, vectorized loops)

---

## 6) Canonical “main run” commands (copy/paste)

> Use Make targets where available; prefer `microalpha ...` CLI only when Make is missing.

### Minimal: sample pipeline
- `make test`
- `make sample`
- `make report`

### Walk-forward: sample
- `make wfv`
- `make report-wfv`

### Real-data: WRDS (local only)
- `export WRDS_DATA_ROOT=/abs/path/to/wrds_exports`
- `make wfv-wrds`
- `make report-wrds`

---

## 7) Artifact policy (what can be committed)

✅ Allowed to commit:
- small synthetic datasets already in repo
- **derived** summaries: plots/tables/metrics, run manifests, config hashes
- tiny WRDS-derived **license-safe** samples *only if allowed* (assume “no” by default)

🚫 Never commit:
- raw WRDS exports
- anything that reconstructs raw WRDS data

---

## 8) Related process docs
- `docs/DOCS_AND_LOGGING_SYSTEM.md` (run logs + self-audit protocol)
- `docs/CODEX_SPRINT_TICKETS.md` (next sprint execution)
- `AGENTS.md` (Codex + contributor rules)
