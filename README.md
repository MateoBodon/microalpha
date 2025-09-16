# microalpha

`microalpha` is a lightweight, event-driven backtesting engine in Python, designed for the rigorous, leakage-safe validation of quantitative trading strategies.

![Tearsheet Screenshot](tearsheet.png)

---

## Core Features

- **Event-Driven Architecture:** Decouples market data, strategy logic, portfolio management, and execution for a clean and scalable design.
- **Leakage-Safe Pipeline:** Employs strict timestamp guards to prevent lookahead bias, validated by a dedicated `pytest` unit test.
- **Realistic Cost Simulation:** Includes models for both commission and trade slippage to provide more credible performance metrics.
- **Robust Validation:** Implements a full walk-forward validation framework, the gold standard for testing strategy robustness on out-of-sample data.
- **Comprehensive Metrics:** Calculates key performance indicators including Sharpe Ratio, Maximum Drawdown, Turnover, and Exposure.
- **Professional Tooling:** Includes a Jupyter tearsheet for visualization, `pytest` for unit testing, and a GitHub Actions CI pipeline for automated code quality checks.

## Strategies Implemented

- **Mean Reversion:** A z-score based strategy that bets on prices reverting to their recent mean.
- **Momentum (Breakout):** A strategy that enters positions when prices break above a recent high, betting on continued momentum.

---

## Getting Started

### 1. Setup

First, clone the repository and set up the Python virtual environment.

```bash
git clone https://github.com/YourUsername/microalpha.git
cd microalpha
python3 -m venv venv
source venv/bin/activate
```

### 2. Installation

Install the project and its dependencies in editable mode. To include the packages for the analysis notebook, use the `[notebook]` option.

```bash
# Install core engine + notebook dependencies
pip install -e .[notebook]
```

### 3. Running a Backtest

You can run a simple backtest using `run.py` or the more advanced walk-forward validation using `walk_forward.py`.

```bash
# Run a single backtest on the sample data
python3 run.py

# Run the full walk-forward validation
python3 walk_forward.py
```

### 4. Viewing Results

After running a backtest, launch Jupyter to view the performance tearsheet.

```bash
jupyter notebook
```

Navigate to `notebooks/tearsheet.ipynb` and run the cells.

