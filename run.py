# run.py
import pandas as pd
from pathlib import Path
from microalpha.engine import Engine
from microalpha.data import CsvDataHandler
from microalpha.strategies.meanrev import MeanReversionStrategy
from microalpha.portfolio import Portfolio
from microalpha.broker import SimulatedBroker
from microalpha.risk import create_sharpe_ratio, create_drawdowns

def main():
    data_dir = Path("data")
    symbol = "SPY"
    initial_cash = 100000.0

    # Initialize components
    data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    strategy = MeanReversionStrategy(symbol=symbol, lookback=3, z_threshold=0.5)
    portfolio = Portfolio(data_handler=data_handler, initial_cash=initial_cash)
    broker = SimulatedBroker(data_handler=data_handler)

    # Initialize and run the engine
    engine = Engine(
        data_handler=data_handler,
        strategy=strategy,
        portfolio=portfolio,
        broker=broker
    )
    engine.run()

    # --- Performance Analysis ---
    print("\n--- Performance Metrics ---")
    equity_df = pd.DataFrame(portfolio.equity_curve).set_index('timestamp')
    equity_df['returns'] = equity_df['equity'].pct_change().fillna(0.0)

    sharpe = create_sharpe_ratio(equity_df['returns'])
    _, max_dd = create_drawdowns(equity_df['equity'])

    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Maximum Drawdown: {max_dd:.2%}")
    print("-------------------------")


if __name__ == "__main__":
    main()