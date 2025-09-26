# run.py
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from microalpha.broker import SimulatedBroker
from microalpha.data import CsvDataHandler
from microalpha.engine import Engine
from microalpha.portfolio import Portfolio
from microalpha.risk import create_drawdowns, create_sharpe_ratio
from microalpha.strategies.breakout import BreakoutStrategy

# --- STRATEGY MAPPING ---
# This allows us to dynamically load the strategy class from the config file.
from microalpha.strategies.meanrev import MeanReversionStrategy
from microalpha.strategies.mm import NaiveMarketMakingStrategy

STRATEGY_MAPPING = {
    "MeanReversionStrategy": MeanReversionStrategy,
    "BreakoutStrategy": BreakoutStrategy,
    "NaiveMarketMakingStrategy": NaiveMarketMakingStrategy,
}
# ------------------------

def main():
    # --- COMMAND-LINE ARGUMENT PARSING ---
    parser = argparse.ArgumentParser(description="Run a backtest for the microalpha engine.")
    parser.add_argument(
        '-c', '--config',
        type=str,
        required=True,
        help='Path to the configuration YAML file.'
    )
    args = parser.parse_args()

    # --- LOAD CONFIGURATION ---
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found at {args.config}")
        return

    print(f"Loaded configuration from {args.config}...")

    # --- ENSURE DETERMINISM ---
    seed = config.get('random_seed')
    if seed is not None:
        np.random.seed(seed)
        print(f"Set random seed to {seed} for reproducibility.")
    # --------------------------

    # --- SETUP COMPONENTS FROM CONFIG ---
    backtest_cfg = config['backtest_settings']
    strategy_cfg = config['strategy']
    broker_cfg = config['broker_settings']

    data_dir = Path(backtest_cfg['data_dir'])
    symbol = backtest_cfg['symbol']
    initial_cash = backtest_cfg['initial_cash']

    # Dynamically select and instantiate the strategy
    strategy_name = strategy_cfg['name']
    strategy_class = STRATEGY_MAPPING.get(strategy_name)
    if not strategy_class:
        print(f"Error: Strategy '{strategy_name}' not found in STRATEGY_MAPPING.")
        return
    strategy = strategy_class(symbol=symbol, **strategy_cfg['params'])

    data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    portfolio = Portfolio(data_handler=data_handler, initial_cash=initial_cash)
    broker = SimulatedBroker(
        data_handler=data_handler,
        execution_style=broker_cfg.get('execution_style', 'INSTANT'),
        num_ticks=broker_cfg.get('num_ticks', 4)
    )

    # --- RUN THE ENGINE ---
    engine = Engine(
        data_handler=data_handler,
        strategy=strategy,
        portfolio=portfolio,
        broker=broker
    )
    engine.run()

    # --- PERFORMANCE ANALYSIS ---
    print("\n--- Performance Metrics ---")
    equity_df = pd.DataFrame(portfolio.equity_curve).set_index('timestamp')
    equity_df.to_csv("equity_curve.csv")

    equity_df['returns'] = equity_df['equity'].pct_change().fillna(0.0)
    sharpe = create_sharpe_ratio(equity_df['returns'])
    _, max_dd = create_drawdowns(equity_df['equity'])

    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Maximum Drawdown: {max_dd:.2%}")
    print(f"Total Turnover: ${portfolio.total_turnover:,.2f}")
    print(f"Average Exposure: {equity_df['exposure'].mean():.2%}")
    print("-------------------------")


if __name__ == "__main__":
    main()
