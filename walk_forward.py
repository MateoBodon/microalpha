# walk_forward.py
import pandas as pd
from pathlib import Path
from microalpha.engine import Engine
from microalpha.data import CsvDataHandler
from microalpha.strategies.meanrev import MeanReversionStrategy
from microalpha.portfolio import Portfolio
from microalpha.broker import SimulatedBroker
from microalpha.risk import create_sharpe_ratio, create_drawdowns

def run_walk_forward_validation(
    data_dir, symbol, strategy_class, strategy_params,
    start_date, end_date, training_days, testing_days
):
    """
    Orchestrates the walk-forward validation process.
    """
    print("--- Starting Walk-Forward Validation ---")
    
    data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    
    all_equity_curves = []
    current_date = pd.Timestamp(start_date)
    
    while current_date + pd.Timedelta(days=training_days + testing_days) <= pd.Timestamp(end_date):
        train_start = current_date
        train_end = train_start + pd.Timedelta(days=training_days)
        test_start = train_end + pd.Timedelta(days=1)
        test_end = test_start + pd.Timedelta(days=testing_days)
        
        print(f"\nProcessing Fold: Train {train_start.date()} to {train_end.date()}, Test {test_start.date()} to {test_end.date()}")

        # --- STRATEGY WARMUP ---
        # Get the last `lookback` prices from the training data to prime the strategy.
        # This prevents "strategy amnesia" at the start of each test period.
        lookback_days = strategy_params.get('lookback', 20)
        warmup_start = train_end - pd.Timedelta(days=lookback_days)
        
        data_handler.set_date_range(warmup_start, train_end)
        warmup_prices = [event.price for event in data_handler.stream_events()]
        # -----------------------
        
        print("  Running backtest on testing data...")
        data_handler.set_date_range(test_start, test_end)
        
        # Pass the historical prices to the new strategy instance
        strategy = strategy_class(
            symbol=symbol, **strategy_params, warmup_prices=warmup_prices
        )
        portfolio = Portfolio(data_handler=data_handler, initial_cash=100000.0)
        broker = SimulatedBroker(data_handler=data_handler)

        engine = Engine(data_handler, strategy, portfolio, broker)
        engine.run()

        if portfolio.equity_curve:
            all_equity_curves.extend(portfolio.equity_curve)
            
        current_date += pd.Timedelta(days=testing_days)

    return all_equity_curves

if __name__ == "__main__":
    # --- CONFIGURATION ---
    WF_DATA_DIR = Path("data")
    WF_SYMBOL = "SPY"
    WF_STRATEGY_CLASS = MeanReversionStrategy
    WF_STRATEGY_PARAMS = {'lookback': 3, 'z_threshold': 0.5}
    WF_START_DATE = "2025-01-01"
    WF_END_DATE = "2025-01-10"
    WF_TRAINING_DAYS = 4
    WF_TESTING_DAYS = 2
    # -------------------

    final_equity_curve = run_walk_forward_validation(
        WF_DATA_DIR, WF_SYMBOL, WF_STRATEGY_CLASS, WF_STRATEGY_PARAMS,
        WF_START_DATE, WF_END_DATE, WF_TRAINING_DAYS, WF_TESTING_DAYS
    )
    
    if not final_equity_curve:
        print("\nNo trades were made during the walk-forward validation.")
    else:
        print("\n--- Final Walk-Forward Performance ---")
        equity_df = pd.DataFrame(final_equity_curve).set_index('timestamp').drop_duplicates()
        equity_df.to_csv("walk_forward_equity.csv")
        
        equity_df['returns'] = equity_df['equity'].pct_change().fillna(0.0)
        sharpe = create_sharpe_ratio(equity_df['returns'])
        _, max_dd = create_drawdowns(equity_df['equity'])

        print(f"Sharpe Ratio: {sharpe:.2f}")
        print(f"Maximum Drawdown: {max_dd:.2%}")
        print("------------------------------------")