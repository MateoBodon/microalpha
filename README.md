# microalpha

[![CI](https://github.com/mateobodon/microalpha/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mateobodon/microalpha/actions/workflows/ci.yml?query=branch%3Amain)
[![Docs](https://img.shields.io/badge/docs-pages-blue)](https://mateobodon.github.io/microalpha)
![Coverage](https://img.shields.io/badge/coverage-78%25-blue.svg)

**Leakage-safe, event-driven backtesting engine with walk-forward cross-validation, parameter optimisation, and production-grade reporting.**

microalpha focuses on rigorous research hygiene: strict chronology enforcement, automated walk-forward reality checks, reproducible artefacts, and a publishing pipeline (MkDocs + GitHub Pages) ready for stakeholder hand-offs. Out of the box you get deterministic sample runs, a public-data configuration bundle, WRDS stubs, factor analytics, and a full test suite that refuses to pass if documentation links or generated visuals go missing.

---

## Latest Results (bundled sample data)

| Run | Sharpe<sub>HAC</sub> | MAR | Max DD | RealityCheck *p*-value | Turnover |
| --- | ---:| ---:| ---:| ---:| ---:|
| Single backtest ([configs/flagship_sample.yaml](configs/flagship_sample.yaml)) | -0.66 | -0.41 | 17.26% | 0.861 | $1.21M |
| Walk-forward ([configs/wfv_flagship_sample.yaml](configs/wfv_flagship_sample.yaml)) | 0.22 | 0.03 | 34.79% | 1.000 | $28.53M |

_Source artefacts: `artifacts/sample_flagship/2025-10-30T18-39-31Z-a4ab8e7` and `artifacts/sample_wfv/2025-10-30T18-39-47Z-a4ab8e7`._

![Sample Flagship Equity Curve](artifacts/sample_flagship/2025-10-30T18-39-31Z-a4ab8e7/equity_curve.png)
![Sample Flagship Bootstrap Histogram](artifacts/sample_flagship/2025-10-30T18-39-31Z-a4ab8e7/bootstrap_hist.png)

### Factor regression (FF3 sample bundle)

| Factor | Beta | *t*-stat |
| --- | ---:| ---:|
| Alpha | -0.0055 | -1.42 |
| Mkt_RF | 10.7236 | 1.74 |
| SMB | 1.4014 | 0.12 |
| HML | -13.1416 | -0.77 |

Computed automatically against `data/factors/ff3_sample.csv` using HAC (Newey–West) standard errors. The sample factor bundle is weekly; reports explicitly resample returns to match factor frequency and record the frequency + sample size alongside the table. The table is injected into `reports/summaries/flagship_mom_wfv.md` when the factor CSV is present.

---

## Project highlights

- **Leakage-safe engine** – event-driven core (DataHandler ➝ Engine ➝ Portfolio ➝ Broker) with timestamp validation, t+1 fills, and lookahead guards enforced by tests.
- **Out-of-sample discipline** – configurable walk-forward validation with Politis–White stationary bootstraps, per-fold metrics, and aggregated reality-check summaries.
- **Visual + statistical reporting** – CLI renders equity/bootstrapped Sharpe PNGs, Markdown summaries, and optional factor regressions; README embeds the same artefacts.
- **Data bundles for every stage** – deterministic sample universe, public ticker mini-panel, WRDS/CRSP configuration template, and FF3 factor snippets included in-repo.
- **Production hygiene** – MkDocs documentation, GitHub Pages auto-deploy, Ruff/Mypy/Pytest/Coverage gates, schema tests that fail when artefacts disappear.

---

## Getting started

### Requirements
- Python 3.12+
- `pip` (recommended: virtual environment via `venv` or `conda`)
- Optional: WRDS/CRSP exports (see [docs/wrds.md](docs/wrds.md))

### Install
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
```

### Reproduce the flagship notebooks in two commands
```bash
make sample && make report          # single backtest artefacts + summary
make wfv && make report-wfv         # walk-forward artefacts + summary + factors
```
Outputs appear under `artifacts/sample_flagship/<RUN_ID>` and `artifacts/sample_wfv/<RUN_ID>` with:

```
bootstrap.json       equity_curve.csv     equity_curve.png
bootstrap_hist.png   exposures.csv        factor_exposure.csv
metrics.json         trades.jsonl         (plus fold-by-fold CSVs for WFV)
```

`microalpha report` will emit Markdown summaries into `reports/summaries/` and embed HAC factor tables automatically when `data/factors/ff3_sample.csv` is present.

### Public-data quickstart
```bash
microalpha wfv --config configs/wfv_flagship_public.yaml \
  --out artifacts/public_wfv
microalpha report --artifact-dir artifacts/public_wfv/<RUN_ID>
```
Prices live under `data/public/prices/` (AAPL, MSFT, AMZN, GOOGL, TSLA, NVDA); metadata is in `data/public/meta_public.csv`.

### WRDS/CRSP workflow (guarded)
1. Export WRDS DSF prices + security master to local paths.
2. Point [`configs/wfv_flagship_wrds.yaml`](configs/wfv_flagship_wrds.yaml) at `$WRDS_DATA_ROOT` exports (env vars are expanded automatically).
3. Run the guarded pipeline:

   ```bash
   make wfv-wrds && make report-wrds
   python reports/analytics.py artifacts/wrds_flagship/<RUN_ID>
   python reports/factors.py artifacts/wrds_flagship/<RUN_ID> --model ff5_mom
   python reports/spa.py --grid artifacts/wrds_flagship/<RUN_ID>/grid_returns.csv
   ```

4. Drop the resulting PNG/MD/JSON artefacts into git (never WRDS raw data) and link them from [docs/results_wrds.md](docs/results_wrds.md).
5. Consult [docs/wrds.md](docs/wrds.md) for schema tables, licensing notes, and survivorship guidance.

---

## CLI cheatsheet

| Command | Description |
| --- | --- |
| `microalpha run --config <cfg> --out <dir>` | Single backtest over the full sample.
| `microalpha wfv --config <cfg> --out <dir>` | Walk-forward cross-validation with optional reality-check overrides.
| `microalpha report --artifact-dir <dir>` | Produce PNGs + Markdown summary (factor table auto-added when factors set).
| `microalpha info` | Emit environment + package metadata as JSON.

See `microalpha --help` for full argument lists.

---

## Documentation

- Live site: **https://mateobodon.github.io/microalpha** (auto-built via `.github/workflows/docs.yml`).
- Local preview: `mkdocs serve`
- Key pages: project overview (`docs/index.md`), flagship strategy walkthrough, reproducibility guarantees, leakage safety, WRDS guide, factor analytics.

---

## Quality gates & testing

| Command | Purpose |
| --- | --- |
| `ruff check` | Linting + import hygiene.
| `mypy src/microalpha/reporting/factors.py` | Type-check the reporting extension (fast path).
| `pytest -q` | Run the 70+ unit/integration tests.
| `pytest --cov=microalpha --cov-report=term` | Generate coverage (78% with bundled suites).
| `mkdocs build` | Verify docs compile before deployment.

Tests include artefact schema validation (`tests/test_artifacts_schema.py`), CLI contract checks, docs-link verification, factor regression smoke tests, and the original leakage/t+1 safeguards.

---

## Architecture & methodology

### Engine snapshot
```
Market data ➝ DataHandler ➝ Engine loop ➝ Strategy ➝ Portfolio ➝ Broker ➝ Trades
```
- **Strict chronology:** timestamps validated before signal handling; fills posted at `t+1` when configured.
- **Portfolio & risk:** turnover caps, sector heat controls, Kelly-style scaling, pluggable slippage & commission models.
- **Execution models:** TWAP, VWAP, linear/√-impact, Kyle λ, implementation shortfall, and LOB simulation with latency knobs.

### Walk-forward pipeline
1. Split train/test windows according to `walkforward` block.
2. Optimise strategy hyper-parameters on training folds.
3. Evaluate out-of-sample; capture per-fold metrics, exposures, trades.
4. Run Politis–White stationary bootstrap across competing models.
5. Persist a manifest (`folds.json`, `reality_check.json`, `metrics.json`) and summary tables.

### Statistical toolkit
- **HAC Sharpe estimates** with configurable lags.
- **Bootstrap reality checks** aggregated across folds (stored in `bootstrap.json`).
- **Factor regression helper** (`reports/factors_ff.py`) producing HAC *t*-stats for FF3-style alphas.

---

## Data bundles

| Bundle | Location | Contents |
| --- | --- | --- |
| Sample flagship | `data/sample/` | Synthetic-cross section (6 tickers), metadata, risk-free series. Used by default configs.
| Public mini-panel | `data/public/` | 6 recognisable tickers (AAPL, MSFT, AMZN, GOOGL, TSLA, NVDA) with trimmed CSVs + metadata + universe file.
| WRDS template | `configs/wfv_flagship_wrds.yaml` | Paths + schema expectations for CRSP DSF exports; guarded `make wrds` target.
| Factors | `data/factors/ff3_sample.csv` | Weekly FF3 sample spanning 2020–2021 for regression demos.

---

## Repository layout (selected)

```
artifacts/                # Committed sample runs powering the README & tests
configs/                  # YAML configs (sample, public, WRDS)
data/                     # Sample + public data bundles + factor CSV
src/microalpha/           # Engine, strategies, reporting, CLI
reports/                  # CLI entrypoints, summaries, factor utilities
docs/                     # MkDocs content
.tests/                   # Pytest suites guarding CLI, artefacts, leakage
```

---

## Contributing & next steps

- Issues and PRs welcome – ensure `pytest -q`, `ruff check`, and `mkdocs build` succeed locally.
- Ideas for expansion:
  - richer public datasets (e.g., macro factors, option metrics)
  - portfolio attribution dashboards
  - GPU-accelerated simulations for dense intraday data.

---

## License

MIT © Mateo Bodon. See [LICENSE](LICENSE).
