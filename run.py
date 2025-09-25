# run.py
from pathlib import Path
from microalpha.engine import Engine
from microalpha.data import CsvDataHandler
from microalpha.strategies.meanrev import MeanReversionStrategy
from microalpha.portfolio import Portfolio
from microalpha.broker import SimulatedBroker

def main():
    """
    Main function to run the backtest.
    """
    data_dir = Path("data")
    symbol = "SPY"
    initial_cash = 100000.0

    # Initialize the components
    data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    strategy = MeanReversionStrategy(symbol=symbol, lookback=5, z_threshold=1.0)
    portfolio = Portfolio(initial_cash=initial_cash)
    broker = SimulatedBroker()

    # Initialize and run the engine
    engine = Engine(
        data_handler=data_handler,
        strategy=strategy,
        portfolio=portfolio,
        broker=broker
    )
    engine.run()

if __name__ == "__main__":
    main()