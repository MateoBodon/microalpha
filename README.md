# microalpha

**Leakage-safe, event-driven backtesting engine with walk-forward cross-validation, parameter optimization, and advanced execution modeling.**

[![CI](https://github.com/mateobodon/microalpha/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mateobodon/microalpha/actions/workflows/ci.yml?query=branch%3Amain)
![Coverage](https://img.shields.io/badge/coverage-%3E85%25-brightgreen.svg)

**TL;DR:** An opinionated, research-hygienic backtester that enforces strict time-ordering, offers out-of-sample walk-forward evaluation with per-fold parameter selection, and includes realistic market frictions including TWAP + linear/√-impact/Kyle-λ execution modeling, slippage, and commission costs.

📚 **Documentation:** https://mateobodon.github.io/microalpha (build locally with `mkdocs serve`).

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

### 📊 **Advanced Analytics**
- **Walk-forward cross-validation** with automatic parameter optimization
- **Bootstrap statistical significance testing** for Sharpe ratios
- **Comprehensive performance metrics** (Sharpe, max drawdown, turnover)
- **Professional tearsheet generation** with equity curves and risk analysis

### ⚡ **Execution Modeling**
- **TWAP + linear/√-impact/Kyle-λ execution** splitting large orders across multiple time periods
- **Volume-based slippage modeling** with configurable price impact
- **Commission costs** and realistic transaction costs
- **Instant vs. TWAP execution modes**
- **Level-2 limit order book** with FIFO queues, configurable depth, and latency modelling

### 🎯 **Strategy Framework**
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
    total_quantity = order_event.quantity
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
            quantity=qty,
            direction=order_event.direction
        )
```

### Volume-Based Slippage Model

Realistic market impact modeling:

```python
def calculate_slippage(self, quantity: int, price: float) -> float:
    """Slippage grows with the square of order size."""
    return self.price_impact * (quantity ** 2)
```

### Cost Components
- **Slippage**: Quadratic relationship with order size
- **Commission**: Fixed $1.00 per trade
- **Market Impact**: Simulated through price movement

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

### Bootstrap Analysis

The engine includes sophisticated statistical testing to validate strategy performance:

```python
def bootstrap_sharpe_ratio(returns, num_simulations=5000, periods=252):
    """Bootstrap analysis for Sharpe ratio significance."""
    
    for _ in range(num_simulations):
        # Create bootstrap sample
        bootstrapped_returns = returns.sample(n=len(returns), replace=True)
        
        # Calculate Sharpe for random sample
        sim_sharpe = create_sharpe_ratio(bootstrapped_returns, periods)
        sharpe_dist.append(sim_sharpe)
    
    # Calculate p-value and confidence intervals
    p_value = sum(1 for s in sharpe_dist if s <= 0.0) / num_simulations
    confidence_interval = (
        np.percentile(sharpe_dist, 2.5),
        np.percentile(sharpe_dist, 97.5)
    )
```

### Metrics Provided
- **P-value**: Probability of observing Sharpe ≤ 0 by random chance
- **95% Confidence Interval**: Range of plausible Sharpe ratios
- **Bootstrap Distribution**: Full distribution of resampled Sharpe ratios

---

## Determinism & Reproducibility

### Seed-Based Reproducibility
```python
# In run.py
seed = config.get('random_seed')
if seed is not None:
    np.random.seed(seed)
    print(f"Set random seed to {seed} for reproducibility.")
```

### Configuration-Driven Execution
- All parameters specified in YAML configuration files
- Deterministic execution paths with no hidden randomness
- Version-controlled configurations for experiment tracking

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
black microalpha/
ruff check microalpha/
```

---

## Quickstart

```bash
pip install -e ".[dev]" && bash scripts/demo.sh
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
  aln: 0.5
  price_impact: 0.00005
  slices: 4

strategy:
  name: "MeanReversionStrategy"
  lookback: 3
  z: 0.5
```

### Supported Strategies
- `MeanReversionStrategy`: Z-score based mean reversion
- `BreakoutStrategy`: Momentum breakout detection
- `NaiveMarketMakingStrategy`: Bid-ask spread capture

### Execution Styles
- `INSTANT`: Immediate order execution
- `TWAP`: Time-weighted average price execution over multiple periods

---

## Data Format

### CSV Structure
```csv
Date,close
2025-01-01,100.0
2025-01-02,101.5
2025-01-03,99.8
```

### Requirements
- **Index**: Datetime index (parsed automatically)
- **Columns**: `close` price column required
- **Format**: Standard CSV with date in first column
- **Frequency**: Daily data recommended (any frequency supported)

### Data Loading
```python
data_handler = CsvDataHandler(csv_dir=Path("data"), symbol="SPY")
data_handler.set_date_range("2025-01-01", "2025-01-31")
```

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

Render a quick report from any run:
```bash
python reports/tearsheet.py artifacts/<run-id>/equity_curve.csv --output tearsheet.png
```

### Example Output
```
--- Performance Metrics ---
Sharpe Ratio: 5.23
Maximum Drawdown: 0.00%
Total Turnover: $1,234,567.89
Average Exposure: 85.4%
-------------------------

--- Statistical Significance ---
Bootstrap p-value (Prob. of Sharpe <= 0): 0.001
95% Confidence Interval for Sharpe: (2.15, 8.31)
------------------------------
```

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

### CI/CD Pipeline
- **Automated Testing**: pytest execution on every commit
- **Code Quality**: ruff linting and black formatting
- **Type Checking**: Static analysis for code quality

---

## Benchmarks

### Local Results

| Host | Python | Command | Events | Runtime (s) | Events/sec |
| --- | --- | --- | --- | --- | --- |
| Apple M2 Pro (32GB, macOS 14.6.1) | 3.12.2 | `python benchmarks/bench_engine.py` | 1,000,000 | 0.773 | 1,294,141 |

Numbers will vary with hardware; use the benchmark harness to gather comparable stats on your system.

---

## Limitations

### Current Constraints
- **Single Asset**: Strategies operate on one symbol at a time
- **Simplified L2 Order Book**: FIFO queue with latency/partial fill modeling for a single asset; execution models are stylized and the full Almgren–Chriss schedule is not implemented.
- **Daily Frequency**: Optimized for daily data (intraday possible)
- **Static Parameters**: No dynamic parameter adjustment during backtest

### Known Issues
- TWAP execution may not complete if insufficient future data
- No position sizing based on volatility or risk metrics

---

## Roadmap

### Near Term (v0.2)
- [ ] Multi-asset portfolio support
- [ ] Limit order implementation
- [ ] Advanced position sizing (Kelly criterion, volatility targeting)
- [ ] Real-time data feed integration

### Medium Term (v0.3)
- [ ] Machine learning strategy framework
- [ ] Advanced execution algorithms (VWAP, Implementation Shortfall)
- [ ] Risk management module (VaR, stress testing)
- [ ] Web-based dashboard

### Long Term (v1.0)
- [ ] Live trading integration
- [ ] Cloud deployment options
- [ ] Strategy marketplace
- [ ] Institutional-grade reporting

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
