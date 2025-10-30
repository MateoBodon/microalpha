# microalpha

**Leakage-safe, event-driven backtesting engine with walk-forward cross-validation, parameter optimization, and advanced execution modeling.**

[![CI](https://github.com/mateobodon/microalpha/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mateobodon/microalpha/actions/workflows/ci.yml?query=branch%3Amain)
[![Docs](https://img.shields.io/badge/docs-pages-blue)](https://mateobodon.github.io/microalpha)
![Coverage](https://img.shields.io/badge/coverage-79%25-blue.svg)

**TL;DR:** An opinionated, research-hygienic backtester that enforces strict time-ordering, offers out-of-sample walk-forward evaluation with per-fold parameter selection, and includes realistic market frictions including TWAP + linear/√-impact/Kyle-λ execution modeling, slippage, and commission costs.

📚 **Documentation:** https://mateobodon.github.io/microalpha (build locally with `mkdocs serve`).

---

## Headline Metrics

| Run | Sharpe_HAC | MAR | MaxDD | RealityCheck_p_value | Turnover |
| --- | ---:| ---:| ---:| ---:| ---:|
| Single backtest ([configs/flagship_sample.yaml](configs/flagship_sample.yaml)) | -0.66 | -0.41 | 17.26% | 0.861 | $1.21M |
| Walk-forward ([configs/wfv_flagship_sample.yaml](configs/wfv_flagship_sample.yaml)) | 0.22 | 0.03 | 34.79% | 1.000 | $28.53M |

_Source artifacts: `artifacts/sample_flagship/2025-10-30T18-39-31Z-a4ab8e7` and `artifacts/sample_wfv/2025-10-30T18-39-47Z-a4ab8e7`._

### Reproduce in One Command

```bash
make sample && make report
make wfv && make report-wfv
```

- The `artifacts/` directories now include `metrics.json`, `bootstrap.json`, `equity_curve.png`, `bootstrap_hist.png`, `exposures.csv`, and `trades.jsonl`.
- `reports/summaries/flagship_mom.md` and `reports/summaries/flagship_mom_wfv.md` are auto-generated from the sample runs.
- Sample data (prices, metadata, risk-free series, universe) ships under `data/sample/`—no external vendors required.
- WRDS/CRSP workflow documentation lives in [`docs/wrds.md`](docs/wrds.md); update [`configs/wfv_flagship_wrds.yaml`](configs/wfv_flagship_wrds.yaml) and run `make wrds` to exercise it.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Leakage-Safe Design](#leakage-safe-design)
- [Included Strategies](#included-strategies)
- [Execution & Costs](#execution--costs)
- [Walk-Forward Cross-Validation](#walk-forward-cross-validation)
- [Statistical Significance Testing](#statistical-significance-testing)
- [Determinism & Reproducibility](#determinism--reproducibility)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Configuration Reference](#configuration-reference)
- [Data Format](#data-format)
- [Performance Analysis](#performance-analysis)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Benchmarks](#benchmarks)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

### 🚀 **Core Engine**
- **Event-driven architecture** with strict chronological processing
- **Leakage-safe design** preventing lookahead bias through timestamp validation
- **Modular components** (DataHandler, Strategy, Portfolio, Broker) for easy extension
- **Real-time equity tracking** with exposure monitoring
- **Scalable multi-asset streaming** using k-way heap merges for large symbol panels

### 📊 **Advanced Analytics**
- **Walk-forward cross-validation** with Politis–White block bootstrap reality checks
- **HAC-aware Sharpe analytics** (`METRICS_HAC_LAGS`) exposing standard errors and confidence bands
- **Rolling factor exposure attribution** via `reports/factor_exposure.py`
- **Comprehensive performance metrics** (Sharpe, Drawdown, turnover, alpha/β, t-stats)
- **Professional tearsheet generation** with equity curves and risk analysis

### ⚡ **Execution Modeling**
- **TWAP + linear/√-impact/Kyle-λ execution** splitting large orders across multiple time periods
- **Volume-based slippage modeling** with configurable price impact
- **Commission costs** and realistic transaction costs
- **Instant vs. TWAP execution modes**
- **Level-2 limit order book** with FIFO queues, configurable depth, and latency modelling

### 🎯 **Strategy Framework**
- **Flagship cross-sectional momentum** with sector-normalised 12-1 sleeves and turnover heat
- **Mean reversion strategy** with z-score based entry/exit signals
- **Breakout momentum strategy** with lookback period optimization
- **Naive market-making strategy** with inventory management
- **Extensible strategy interface** for custom implementations

### 🔧 **Developer Experience**
- **Configuration-driven CLI** with YAML parameter files
- **Deterministic execution** with seed-based reproducibility
- **Comprehensive test suite** with lookahead bias validation
- **Clean, type-hinted codebase** with proper error handling

---

## Architecture

The microalpha engine follows a sophisticated event-driven architecture that mirrors real trading systems:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   DataHandler   │───▶│     Engine       │───▶│   Portfolio     │
│                 │    │                  │    │                 │
│ • CSV loading   │    │ • Event loop     │    │ • Position mgmt │
│ • Date filtering│    │ • Chronological  │    │ • Equity calc   │
│ • Price queries │    │ • processing     │    │ • Order gen     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    Strategy     │◀───│   Event Queue    │───▶│     Broker      │
│                 │    │                  │    │                 │
│ • Signal calc   │    │ • MarketEvent    │    │ • Order exec    │
│ • Entry/exit    │    │ • SignalEvent    │    │ • TWAP modeling │
│ • Risk mgmt     │    │ • OrderEvent     │    │ • Slippage calc │
└─────────────────┘    │ • FillEvent      │    └─────────────────┘
                       └──────────────────┘
```

### Event Flow

1. **MarketEvent**: New price data triggers the processing pipeline
2. **SignalEvent**: Strategy generates buy/sell signals based on market conditions
3. **OrderEvent**: Portfolio converts signals into executable orders
4. **FillEvent**: Broker executes orders with realistic market impact

---

## Leakage-Safe Design

microalpha implements rigorous safeguards against lookahead bias, a critical issue in quantitative finance:

### Timestamp Validation
```python
class LookaheadError(Exception):
    """Custom exception for lookahead bias violations."""

# In Portfolio.on_signal()
if self.current_time and signal_event.timestamp < self.current_time:
    raise LookaheadError("Signal event timestamp is in the past.")
```

### Chronological Processing
- Events are processed in strict timestamp order
- No future data is accessible during signal generation
- Portfolio state updates occur only after market events

### Time-ordering & t+1
- [`tests/test_time_ordering.py`](tests/test_time_ordering.py) enforces event sequencing and ensures strategy logic only consumes data up to the current timestamp.
- [`tests/test_tplus1_execution.py`](tests/test_tplus1_execution.py) verifies that executions settle on the next tick, preserving t+1 accounting for fills and portfolio updates.

### Walk-Forward Validation
- Training and testing periods are strictly separated
- Parameters are optimized only on historical data
- Out-of-sample testing prevents overfitting

---

## Included Strategies

### 1. Mean Reversion Strategy
**Implementation**: Z-score based entry/exit signals

```python
# Entry: When price deviates significantly below mean
if z_score < -self.z_threshold and not self.invested:
    signal = SignalEvent(event.timestamp, self.symbol, 'LONG')

# Exit: When price returns to mean or above
elif z_score > self.z_threshold and self.invested:
    signal = SignalEvent(event.timestamp, self.symbol, 'EXIT')
```

**Key Features**:
- Configurable lookback period and z-score threshold
- Automatic warmup period handling for walk-forward validation
- Robust to zero-variance edge cases

### 2. Breakout Strategy
**Implementation**: Momentum-based breakout detection

```python
# Entry: When current price breaks above recent high
if current_price > lookback_high and not self.invested:
    signal = SignalEvent(event.timestamp, self.symbol, 'LONG')
```

**Key Features**:
- Dynamic lookback window for resistance level calculation
- Simple but effective momentum capture
- Configurable lookback periods for different timeframes

### 3. Naive Market Making Strategy
**Implementation**: Bid-ask spread capture with inventory management

```python
# Continuously quote bid and ask around mid-price
bid_price = mid_price - self.spread / 2.0
ask_price = mid_price + self.spread / 2.0

# Manage inventory limits
if self.invested < self.inventory_limit:
    # Place bid order
elif self.invested > -self.inventory_limit:
    # Place ask order
```

**Key Features**:
- Inventory-based position sizing
- Configurable spread and inventory limits
- Simulates realistic market-making behavior

---

## Execution & Costs

### TWAP + linear/√-impact/Kyle-λ Execution

The broker implements stylized execution models that capture key microstructure effects without claiming a full Almgren–Chriss schedule:

```python
def _schedule_twap_orders(self, order_event):
    """Splits meta-orders into child orders for TWAP execution."""
    total_quantity = order_event.qty
    future_timestamps = self.data_handler.get_future_timestamps(
        start_timestamp=order_event.timestamp,
        n=self.num_ticks
    )
    
    # Distribute quantity across time periods
    child_quantity = total_quantity // effective_num_ticks
    for i in range(effective_num_ticks):
        child_order = OrderEvent(
            timestamp=future_timestamps[i],
            symbol=order_event.symbol,
            qty=qty,
            side=order_event.side
        )
```

### Slippage & Impact Models

Microalpha provides several stylised models:

- Linear impact (default in `Executor`): `slippage = price_impact * |qty|`
- Square-root impact (`SquareRootImpact`): `slippage = k * sqrt(|qty|)`
- Kyle-λ (`KyleLambda`): `slippage = λ * qty`
- Volume-based (`VolumeSlippageModel`): `slippage = impact * qty²`, now selectable via config

Configure via YAML under `exec:` with `type: instant|twap|vwap|is|sqrt|kyle|lob` and `price_impact`/`commission` as needed. Enable volume-aware slippage as:

```yaml
exec:
  type: twap
  price_impact: 0.00005
  slippage:
    type: volume
    impact: 0.0001
```

### Scheduling Models
- `TWAP`: Even time slicing across the next N timestamps (`slices`)
- `VWAP`: Volume-weighted slicing using `get_volume_at` when available
- `IS` (Implementation Shortfall): Front-loaded geometric schedule configured by `urgency`

### Cost Components
- Slippage: as per configured model above
- Commission: per-share (or unit) commission `commission * |qty|`
- Market impact: implied by price slippage and execution scheduling

### Capital Allocation Policies
- `VolatilityScaledPolicy` scales raw order sizes inversely to recent realised volatility to keep dollar risk per trade stable.
- Supply per-symbol sectors and heat limits simultaneously for portfolio-aware sizing.
- Configure in YAML with:

```yaml
capital_policy:
  type: volatility_scaled
  lookback: 5
  target_dollar_vol: 15000
  min_qty: 5
```

---

## Walk-Forward Cross-Validation

microalpha implements rigorous walk-forward validation with automatic parameter optimization:

### Process Flow
1. **Training Phase**: Optimize parameters on historical data using grid search
2. **Warmup Phase**: Initialize strategy with optimal parameters using training data
3. **Testing Phase**: Execute strategy on out-of-sample data
4. **Roll Forward**: Advance window and repeat process

### Implementation
```python
def run_walk_forward_validation(data_dir, symbol, strategy_class, param_grid,
                               start_date, end_date, training_days, testing_days):
    """Orchestrates walk-forward validation with parameter optimization."""
    
    # Grid search optimization on training data
    optimal_params = optimize_strategy_parameters(
        data_handler, train_start, train_end, strategy_class, param_grid, symbol
    )
    
    # Strategy warmup with optimal parameters
    strategy = strategy_class(
        symbol=symbol, **optimal_params, warmup_prices=warmup_prices
    )
    
    # Out-of-sample testing
    engine = Engine(
        data_handler,
        strategy,
        portfolio,
        broker,
        rng=np.random.default_rng(42),
    )
    engine.run()
```

### Benefits
- **Prevents overfitting** through strict train/test separation
- **Realistic performance estimates** using out-of-sample data
- **Parameter adaptation** to changing market conditions
- **Statistical robustness** through multiple validation periods

---

## Statistical Significance Testing

### HAC-aware Sharpe analytics

- `microalpha.risk_stats.sharpe_stats` computes annualised Sharpe together with **standard error**, **t-statistic**, and **95% confidence interval**.
- Enable Newey–West style heteroskedasticity/autocorrelation-consistent (HAC) errors by setting:

```bash
METRICS_HAC_LAGS=6 microalpha run -c configs/meanrev.yaml
```

- The resulting `metrics.json` includes `sharpe_ratio_se`, `sharpe_ratio_ci_low/high`, and `sharpe_ratio_tstat` in addition to the point estimate.

### Block bootstrap inference

- `risk_stats.block_bootstrap` preserves serial dependence through **stationary** or **circular** blocks (Politis–White rule-of-thumb for default block length).
- `microalpha risk.bootstrap_sharpe_ratio` is now a thin wrapper over this helper and emits a warning if legacy IID sampling is requested.
- Walk-forward validation reports a `reality_check_pvalue` in each fold, replacing the old SPA label; the bootstrap method and block length can be overridden via CLI (`microalpha wfv --reality-check-method circular --reality-check-block-len 15`).

### Rolling factor attribution

- `reports/factor_exposure.py` runs rolling OLS on portfolio returns versus user-provided factor CSVs, writing both a `.csv` and `.png` exposure trace to the artifacts directory.
- Use it alongside the new flagship walk-forward run to sanity-check exposures against common style factors.

---

## Determinism & Reproducibility

### Seed-Based Reproducibility
```python
# src/microalpha/manifest.py
def build(seed: Optional[int], config_path: str, run_id: str, config_sha256: str, git_sha: Optional[str] = None) -> Manifest:
    norm_seed = int(seed or 0)
    random.seed(norm_seed)
    np.random.seed(norm_seed)
    ...
    return Manifest(...)
```

### Configuration-Driven Execution
- All parameters specified in YAML configuration files
- Deterministic execution paths with no hidden randomness
- Version-controlled configurations for experiment tracking

### Artifacts

Every run writes a reproducible record to `artifacts/<run_id>/`:

```
artifacts/2025-10-05T19-12-40Z-2f9c1d/
manifest.json
metrics.json
equity_curve.csv
trades.jsonl
```

`manifest.json` includes: `run_id`, `git_sha`, `microalpha_version`, `python`, `platform`, `seed`, `config_sha256`, `numpy_version`, and `pandas_version`.
`metrics.json` contains *only run-invariant stats* (Sharpe, Sortino, max drawdown, turnover, exposure).

```json
{
  "run_id": "2025-10-05T19-12-40Z-2f9c1d",
  "git_sha": "2f9c1db",
  "microalpha_version": "0.1.1",
  "python": "3.11.6",
  "platform": "Ubuntu 22.04",
  "seed": 42,
  "config_sha256": "c1e8...",
  "numpy_version": "1.26.4",
  "pandas_version": "2.2.2"
}
```

---

## Installation

### Requirements
- Python 3.9+
- pandas
- numpy
- pydantic >=2
- pytest (for testing)
- pyyaml (for configuration)

### Install from Source
```bash
git clone https://github.com/mateobodon/microalpha.git
cd microalpha
pip install -e .
```

### Development Setup
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
ruff format src tests reports/generate_summary.py
ruff check src tests reports
```

CI enforces >=85% line coverage:

```bash
pytest -q --cov=microalpha --cov-fail-under=85
```

#### Tool versions

- CI workflow: [ci.yml](https://github.com/MateoBodon/microalpha/actions/workflows/ci.yml?query=branch%3Amain) - run logs list the exact toolchain versions used in CI.

---

## Quickstart

```bash
pip install -e ".[dev]" && bash scripts/demo.sh

# Re-generate the headline summary
python reports/generate_summary.py
cat reports/summaries/quant_summary.md
```

Enable profiling and override output directory:

```bash
microalpha run -c configs/meanrev.yaml --profile --out artifacts_local
```

Market-making visualisation (LOB vs. TWAP):

```bash
pip install -e ".[dev]" && python scripts/plot_mm_spread.py
```

---

## Configuration Reference

### Strategy Configuration (YAML)
```yaml
data_path: "../data"
symbol: "SPY"
cash: 100000.0
seed: 42
max_exposure: 0.6
max_drawdown_stop: 0.25
turnover_cap: 500000.0
kelly_fraction: 0.05

exec:
  type: "twap"
  commission: 0.5
  price_impact: 0.00005
  slices: 4
  slippage:
    type: "volume"
    impact: 0.0001

strategy:
  name: "MeanReversionStrategy"
  lookback: 3
  z: 0.5

capital_policy:
  type: "volatility_scaled"
  lookback: 5
  target_dollar_vol: 15000
  min_qty: 5
```

### Supported Strategies
- `MeanReversionStrategy`: Z-score based mean reversion
- `BreakoutStrategy`: Momentum breakout detection
- `NaiveMarketMakingStrategy`: Bid-ask spread capture

### Execution Styles
- `INSTANT`: Immediate order execution
- `TWAP`: Time-weighted average price execution over multiple periods
- `VWAP`: Volume-weighted execution using forward volume estimates
- `IS`: Implementation shortfall with urgency parameter
- `LOB`: Limit-order-book backed execution with latency simulation

### Risk Sizing
- `capital_policy` (optional): currently supports `volatility_scaled`, which rescales order quantities to target a dollar volatility budget per trade.
- Portfolio-level controls include exposure limits, drawdown halts, turnover caps, Kelly sizing, sector heats, and total portfolio heat.

---

## Data Format

### CSV Structure
```csv
date,close,volume
2025-01-02,400.00,56000000
2025-01-03,402.15,57200000
2025-01-06,401.20,54800000
```

### Requirements
- **Index**: Datetime index (parsed automatically)
- **Columns**: `close` required; include `volume` for VWAP/IS execution or impact modelling
- **Format**: Standard CSV with date in first column (header case-insensitive)
- **Frequency**: Daily data recommended (any frequency supported)

### Data Loading
```python
data_handler = CsvDataHandler(csv_dir=Path("data"), symbol="SPY")
data_handler.set_date_range("2025-01-01", "2025-01-31")
```

#### Bundled Sample Data

| Directory | Description | Notes |
| --- | --- | --- |
| `data/` | Lightweight demo equities (e.g., `SPY.csv`) | Handy for smoke tests and quick strategy iteration. |
| `data_sp500/` | Raw S&P 500-style panel with `close` + `volume` columns | Used by `configs/wfv_cs_mom_small.yaml`; run `scripts/augment_sp500.py` before flagship experiments. |
| `data_sp500_enriched/` | Cleaned panel with positive volume and liquidity metadata | Output of `scripts/augment_sp500.py`. |
| `data/flagship_universe/` | Monthly liquidity-filtered universes for flagship momentum | Generated by `scripts/build_flagship_universe.py`. |

All CSVs expect ISO date strings in the first column and numeric `close` prices. Provide `volume` when using VWAP/Implementation Shortfall execution or volume-aware slippage.

- **Scaling tip:** panels beyond a few hundred symbols benefit from columnar storage. Convert the enriched panel to Parquet (e.g. with `pyarrow`) and point `MultiCsvDataHandler` at sharded daily files or swap in an Arrow/Parquet handler for faster I/O without altering the leak-free semantics.
- **Dataset audit:** `metadata/sp500_enriched.csv` tracks liquidity and sector overrides; run `scripts/augment_sp500.py` to refresh before flagship studies.

- For a full audit, check [docs/data_sp500.md](docs/data_sp500.md) and the generated `reports/data_inventory_sp500.json`.
- The flagship strategy blueprint lives in [docs/flagship_strategy.md](docs/flagship_strategy.md).

---

## Performance Analysis

### Built-in Metrics
- **Sharpe Ratio** (annualised) and **Sortino Ratio** for downside risk
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Total Turnover** and **Traded Days** to gauge activity
- **Average Exposure** and **Final Equity**

### Tearsheet Components
1. **Equity Curve**: Portfolio value over time
2. **Drawdown Series**: Risk visualization
3. **Exposure Tracking**: Position sizing over time
4. **Bootstrap Analysis**: Statistical significance testing
5. **Factor Exposures**: Rolling OLS attribution via `reports/factor_exposure.py`

Render a quick report from any run:
```bash
python reports/tearsheet.py artifacts/<run-id>/equity_curve.csv --output tearsheet.png
```

Interactive HTML report:

```bash
python reports/html_report.py artifacts/<run-id>/equity_curve.csv --trades artifacts/<run-id>/trades.jsonl --output artifacts/<run-id>/report.html
```

Resume-ready overview:

```bash
python reports/generate_summary.py
cat reports/summaries/quant_summary.md
```

The summary script replays highlighted configs, writes fresh artifacts under `reports/summaries/_artifacts/`, and renders a Markdown dashboard of Sharpe, CAGR, drawdown, and fold-level walk-forward stats.

### Sample Results (reproducible)

| Config | Type | Sharpe | CAGR | Max DD | Turnover |
| --- | --- | --- | --- | --- | --- |
| `configs/breakout.yaml` | Single run | **1.38** | 71.7% | 4.4% | $804,710 |
| `configs/wfv_cs_mom_small.yaml` | Walk-forward (13 folds) | 0.00 | -0.0% | 0.2% | $44,351 |

Fold diagnostics (from `reports/summaries/_artifacts/.../folds.json`):
- Average test Sharpe: **-0.29**
- Best test Sharpe: **3.70**

These figures regenerate deterministically via the summary script and serve as resume-ready talking points.

### Flagship Pipeline (long-running)

```bash
# 1. Clean the raw S&P500 panel and emit metadata
python scripts/augment_sp500.py --source data_sp500 --dest data_sp500_enriched \
    --sector-map metadata/sp500_sector_overrides.csv \
    --metadata-output metadata/sp500_enriched.csv \
    --summary-output reports/data_sp500_cleaning.json

# 2. Build monthly liquidity-filtered universes for the flagship strategy
python scripts/build_flagship_universe.py --data-dir data_sp500_enriched \
    --metadata metadata/sp500_enriched.csv \
    --out-dir data/flagship_universe \
    --min-dollar-volume 15000000 --top-n 120 --start-date 2012-01-01

# 3. Run the flagship momentum backtest (tens of minutes on a laptop)
python -m microalpha.cli run -c configs/flagship_mom.yaml --out artifacts/flagship_single
```

See [docs/flagship_strategy.md](docs/flagship_strategy.md) for the research blueprint and tuning checklist.

---

## Testing & Quality Assurance

### Test Coverage
- **Unit Tests**: Individual component functionality
- **Integration Tests**: End-to-end system validation
- **Lookahead Bias Tests**: Timestamp validation verification

### Key Test Cases
```python
def test_portfolio_raises_lookahead_error_on_stale_signal():
    """Validates lookahead bias prevention."""
    with pytest.raises(LookaheadError):
        list(portfolio.on_signal(stale_signal))

def test_breakout_strategy_generates_long_signal():
    """Tests strategy signal generation."""
    assert signal.side == 'LONG'
    assert signal.symbol == symbol
```

### Verification Checklist
```bash
ruff format src tests reports/generate_summary.py
ruff check src tests reports
mypy src
pytest -q --cov=microalpha --cov-fail-under=85
python reports/generate_summary.py
```

CI runs the same sequence on every push (see badge at top).

---

## Benchmarks

### Local Results

| Host | Python | Command | Events | Runtime (s) | Events/sec |
| --- | --- | --- | --- | --- | --- |
| Apple M2 Pro (32GB, macOS 14.6.1) | 3.12.2 | `python benchmarks/bench_engine.py` | 1,000,000 | 0.773 | 1,294,141 |
| Apple M2 Pro (32GB, macOS 14.6.1) | 3.12.2 | `python benchmarks/bench_multi_stream.py` | 2,499,991 | **3.364** (fast) / 31.147 (baseline) | **743,083** / 80,265 |

Numbers will vary with hardware; use the benchmark harness to gather comparable stats on your system.

`benchmarks/bench_multi_stream.py` replays the new k-way heap merge against a legacy union-index implementation and prints events/sec before and after, demonstrating an order of magnitude throughput gain.

To capture a cProfile trace for a run:

```bash
MICROALPHA_PROFILE=1 microalpha run -c configs/meanrev.yaml
```

The profiler output is written to `artifacts/<run_id>/profile.pstats`.

---

## Limitations

### Current Constraints
- **Multi-asset support**: Cross-sectional momentum + shared portfolio sizing are covered; more complex cross-asset risk models (e.g., covariance-aware allocators) remain work-in-progress.
- **Execution realism**: LOB/TWAP/VWAP models are stylised calibrations; they do not ingest live depth or venue-specific microstructure.
- **Data hygiene**: CSV loaders expect already-adjusted OHLCV files (corporate actions / survivorship handled upstream).
- **Parameter search**: Walk-forward optimizer performs brute-force grid sweeps—suitable for small grids but not yet hyper-efficient.

### Known Issues
- TWAP execution may not complete if insufficient future data
- No position sizing based on volatility or risk metrics

---

## Roadmap

### Near Term
- [ ] Covariance-aware cross-asset portfolio optimiser
- [ ] Intraday data adapters (minute-level CSV/Parquet streaming)
- [ ] CLI hooks for custom capital policies and slippage plugins
- [ ] Automated config sweeps with pareto-ranked reporting

### Medium Term
- [ ] Machine-learning strategy templates (alpha combination, feature pipelines)
- [ ] Factor attribution / risk decomposition reports
- [ ] Scenario analysis module (stress, regime shifts)
- [ ] Optional Postgres/Arrow backends for large-scale data

### Long Term
- [ ] Live-trading adaptor layer (broker API integration)
- [ ] Hosted notebook + dashboard experience
- [ ] Workflow orchestration for nightly walk-forward jobs
- [ ] Marketplace for sharing strategies + artifacts

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! Please see our contributing guidelines and code of conduct.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

**Built with ❤️ for the quantitative finance community**

*For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/mateobodon/microalpha).*
