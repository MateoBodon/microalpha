# run.py
# run.py
import pandas as pd
from pathlib import Path
from microalpha.engine import Engine
from microalpha.data import CsvDataHandler
from microalpha.strategies.meanrev import MeanReversionStrategy
from microalpha.strategies.breakout import BreakoutStrategy
from microalpha.portfolio import Portfolio
from microalpha.broker import SimulatedBroker
from microalpha.risk import create_sharpe_ratio, create_drawdowns

def main():
    data_dir = Path("data")
    symbol = "SPY"
    initial_cash = 100000.0

    # --- CHOOSE STRATEGY ---
    # strategy = MeanReversionStrategy(symbol=symbol, lookback=3, z_threshold=0.5)
    strategy = BreakoutStrategy(symbol=symbol, lookback=5)
    # ----------------------------

    data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    portfolio = Portfolio(data_handler=data_handler, initial_cash=initial_cash)
    broker = SimulatedBroker(data_handler=data_handler)

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
    equity_df.to_csv("equity_curve.csv") # Save the results for the notebook

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