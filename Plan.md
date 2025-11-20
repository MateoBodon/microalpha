## A. What “success” looks like (acceptance criteria)

**Public deliverables to feature on your resume:**

1. **CRSP Daily Equities – Flagship Momentum (12–1, sector‑neutral):**

   * Period: ≥ 2000–2025; Universe: top ~1,000 by mkt cap, delistings included.
   * Costs: commissions, spread floor, square‑root impact; borrow fees on shorts.
   * **Walk‑Forward CV** (3–5y train / 6–12m test) with **White’s Reality Check / SPA** across key hyper‑params.
   * **Attribution**: Carhart 4F and FF5 (+ MOM) with HAC SEs; rolling betas; residual alpha.
   * **Capacity & Turnover** vs ADV with LOB option.
   * **Tearsheet & reproducible artifacts** (manifest + JSONL logs + figures).

2. **Two orthogonal strategies (each with WFV, costs, attribution, SPA/MCS):**

   * Post‑Earnings Announcement Drift (PEAD) and Weekly Reversal (liquidity/impact constrained).

3. **Hygiene:** ≥80% test coverage, **CI** (tests+docs), **AGENTS.md**, **Codex configured**, canonical artifacts checked in (no WRDS data).

---

## B. Short‑term plan (next 1–2 weeks)

> The tasks are sequenced so Codex can do most of the work unattended with **`codex exec`** and the config/prompt I provide below. Use Homebrew/npm to install the CLI. ([OpenAI Developer Portal][1])

### 1) Repo scaffolding & guardrails

* **Add CI**: GitHub Actions matrix (Py 3.10–3.12) → `pytest -vv --maxfail=1 --durations=25 --log-cli-level=INFO --cov=...`, `mkdocs build`, coverage gate.
* **Mark integration tests** that require WRDS with `@pytest.mark.wrds`; default CI skips them; local runs include via `-m wrds`.
* **Pre‑commit**: black, isort, ruff/flake8, **detect‑secrets**.
* **.gitignore**: `data/wrds/**`, `artifacts/**` (except whitelisted PNG/MD/JSON), `.env*`, `~/.pgpass` (do not commit).
* **Makefile/Nox**: `make test`, `make test-wrds`, `make wfv-wrds`, `make report-wrds`.

### 2) WRDS access & local caching (no secrets in repo)

* Prefer **`.pgpass`** (host `wrds-pgdata.wharton.upenn.edu`, port `9737`, db `wrds`) so your password is never echoed or stored in env logs; file mode `600`. The `wrds` Python package will then connect without prompting. ([stata.com][2])
* Optional: set `WRDS_USERNAME` only; avoid printing it anywhere.
* Local **ETL**: export CRSP daily panel (OHLCV, shares out, delisting returns), write **columnar Parquet** partitions by year/symbol under `data/wrds/crsp/`.
* Generate **universe snapshots** (monthly top‑N by mkt cap; sector buckets).

### 3) Analytics & reporting modules (first pass)

* **IC/IR & deciles**: rank IC timeseries, rolling IR; P1…P10 decile returns and **P10–P1 LS** with bands.
* **Factor attribution**: Carhart 4F + FF5(+MOM) with **HAC SEs**; rolling betas; inject table in report if factor CSVs present (you already do similar for FF3—extend it).
* **Reality‑check / SPA**: keep White’s Reality Check, add **Hansen SPA** or **MCS** for grid snooping control.

### 4) First canonical WFV on CRSP

* Config `configs/wfv_flagship_wrds.yaml` with realistic costs, sector‑neutral portfolio, square‑root impact, next‑day open or TWAP.
* **Artifacts to commit** (but not WRDS data): manifest, metrics JSON, per‑fold summary MD, PNG plots, factor tables.
* **Docs**: new “Results (WRDS)” page in MkDocs with headline table and figures.

---

## C. Mid‑term plan (weeks 3–6)

* **Execution realism**: LOB executor validation set (1–5 liquid tickers); plot cost vs order size under different impact elasticities.
* **Capacity study**: performance vs notional, 5–20% ADV clamps, slippage floors.
* **More strategies**: PEAD & weekly reversal with WFV/SPA/MCS + attribution; stress to cost grids.
* **Cross‑checks**: sub‑periods (2000–09, 2010–19, 2020–25), high/low vol regimes, sector/country neutrality toggles.
* **CLI polish**: `microalpha report --analytics all` to emit IC/IR, deciles, capacity, rolling betas.
* **Autofix CI**: optional follow‑up job that invokes Codex if CI fails to propose a PR with minimal fixes. ([OpenAI Developer Portal][3])

---

## D. Long‑term plan (quarter+)

* **Release 1.0**: API freeze, type hints, `pipx`‑friendly CLI, perf docs, reproducibility story (manifests + artifacts).
* **Benchmarks & notebooks**: side‑by‑side vs public baselines; reproducible “paper replication” notebooks.
* **Cloud runners**: self‑hosted task that runs **non‑WRDS** public datasets in CI (to show green test/report pipelines) and a documented **local runner** for WRDS.
* **Codex cloud** environments (optional): allow Codex web tasks with **explicit domain allowlists** and methods if you want internet research inside Codex Cloud; keep strict allowlist (GitHub, PyPI, docs) and review logs. ([OpenAI Developer Portal][4])

