# walk_forward.py
from itertools import product
from pathlib import Path

import pandas as pd

from microalpha.broker import SimulatedBroker
from microalpha.data import CsvDataHandler
from microalpha.engine import Engine
from microalpha.portfolio import Portfolio
from microalpha.risk import create_drawdowns, create_sharpe_ratio
from microalpha.strategies.meanrev import MeanReversionStrategy


def optimize_strategy_parameters(
    data_handler, train_start, train_end, strategy_class, param_grid, symbol
):
    """
    Finds the best strategy parameters by backtesting on the training data.
    """
    print(
        f"  Optimizing parameters on training data: {train_start.date()} to {train_end.date()}..."
    )

    best_params = None
    best_sharpe = -float("inf")

    # --- GRID SEARCH ---
    # `product` creates all combinations of the parameter values
    for params_tuple in product(*param_grid.values()):
        # Create a dictionary of the current parameter combination
        current_params = dict(zip(param_grid.keys(), params_tuple))

        # --- RUN A BACKTEST ON THE TRAINING DATA ---
        data_handler.set_date_range(train_start, train_end)

        strategy = strategy_class(symbol=symbol, **current_params)
        portfolio = Portfolio(data_handler=data_handler, initial_cash=100000.0)
        broker = SimulatedBroker(data_handler=data_handler)

        engine = Engine(data_handler, strategy, portfolio, broker)
        engine.run()
        # ------------------------------------------

        if portfolio.equity_curve:
            equity_df = pd.DataFrame(portfolio.equity_curve).set_index("timestamp")
            equity_df["returns"] = equity_df["equity"].pct_change().fillna(0.0)

            sharpe = create_sharpe_ratio(equity_df["returns"])

            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_params = current_params

    print(f"  --> Optimal Params Found: {best_params} (Sharpe: {best_sharpe:.2f})")
    return best_params


def run_walk_forward_validation(
    data_dir,
    symbol,
    strategy_class,
    param_grid,
    start_date,
    end_date,
    training_days,
    testing_days,
):
    """
    Orchestrates the walk-forward validation process with parameter optimization.
    """
    print("--- Starting Walk-Forward Validation with Optimization ---")

    data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)

    all_equity_curves = []
    current_date = pd.Timestamp(start_date)

    while current_date + pd.Timedelta(
        days=training_days + testing_days
    ) <= pd.Timestamp(end_date):
        train_start = current_date
        train_end = train_start + pd.Timedelta(days=training_days)
        test_start = train_end + pd.Timedelta(days=1)
        test_end = test_start + pd.Timedelta(days=testing_days)

        print(
            f"\nProcessing Fold: Train {train_start.date()} to {train_end.date()}, Test {test_start.date()} to {test_end.date()}"
        )

        # --- 1. OPTIMIZE on training data ---
        optimal_params = optimize_strategy_parameters(
            data_handler, train_start, train_end, strategy_class, param_grid, symbol
        )

        if not optimal_params:
            print("  Skipping test period as no optimal parameters were found.")
            current_date += pd.Timedelta(days=testing_days)
            continue
        # ------------------------------------

        # --- STRATEGY WARMUP ---
        lookback_days = optimal_params.get("lookback", 20)
        warmup_start = train_end - pd.Timedelta(days=lookback_days)

        data_handler.set_date_range(warmup_start, train_end)
        warmup_prices = [event.price for event in data_handler.stream_events()]
        # -----------------------

        # --- 2. TEST on out-of-sample data ---
        print("  Running backtest on testing data with optimal parameters...")
        data_handler.set_date_range(test_start, test_end)

        strategy = strategy_class(
            symbol=symbol, **optimal_params, warmup_prices=warmup_prices
        )
        portfolio = Portfolio(data_handler=data_handler, initial_cash=100000.0)
        broker = SimulatedBroker(data_handler=data_handler)

        engine = Engine(data_handler, strategy, portfolio, broker)
        engine.run()
        # --------------------------------------

        if portfolio.equity_curve:
            all_equity_curves.extend(portfolio.equity_curve)

        current_date += pd.Timedelta(days=testing_days)

    return all_equity_curves


if __name__ == "__main__":
    # --- CONFIGURATION ---
    WF_DATA_DIR = Path("data")
    WF_SYMBOL = "SPY"
    WF_STRATEGY_CLASS = MeanReversionStrategy
    # Define a grid of parameters to search over
    WF_PARAM_GRID = {"lookback": [3, 5], "z_threshold": [0.5, 1.0]}
    WF_START_DATE = "2025-01-01"
    WF_END_DATE = "2025-01-10"
    WF_TRAINING_DAYS = 4
    WF_TESTING_DAYS = 2
    # -------------------

    final_equity_curve = run_walk_forward_validation(
        WF_DATA_DIR,
        WF_SYMBOL,
        WF_STRATEGY_CLASS,
        WF_PARAM_GRID,
        WF_START_DATE,
        WF_END_DATE,
        WF_TRAINING_DAYS,
        WF_TESTING_DAYS,
    )

    if not final_equity_curve:
        print("\nNo trades were made during the walk-forward validation.")
    else:
        print("\n--- Final Walk-Forward Performance ---")
        equity_df = (
            pd.DataFrame(final_equity_curve).set_index("timestamp").drop_duplicates()
        )
        equity_df.to_csv("walk_forward_equity.csv")

        equity_df["returns"] = equity_df["equity"].pct_change().fillna(0.0)
        sharpe = create_sharpe_ratio(equity_df["returns"])
        _, max_dd = create_drawdowns(equity_df["equity"])

        print(f"Sharpe Ratio: {sharpe:.2f}")
        print(f"Maximum Drawdown: {max_dd:.2%}")
        print("------------------------------------")
