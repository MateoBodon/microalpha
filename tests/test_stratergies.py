# tests/test_strategies.py
import queue
import pandas as pd
from microalpha.events import MarketEvent, SignalEvent
from microalpha.strategies.breakout import BreakoutStrategy

def test_breakout_strategy_generates_long_signal():
    """
    Tests if the BreakoutStrategy correctly identifies a breakout
    and places a LONG signal onto the events queue.
    """
    # 1. Arrange
    symbol = "TEST"
    events_q = queue.Queue()
    strategy = BreakoutStrategy(symbol=symbol, lookback=5)

    # Create a series of market events where the last one is a breakout
    prices = [100, 101, 102, 101, 100, 103] # Breakout at 103
    for i, price in enumerate(prices):
        timestamp = pd.Timestamp(f'2025-01-0{i+1}')
        market_event = MarketEvent(timestamp, symbol, price)

        # 2. Act
        strategy.calculate_signals(market_event, events_q)

    # 3. Assert
    # Check that one signal was generated
    assert not events_q.empty()
    assert events_q.qsize() == 1

    signal = events_q.get()
    assert isinstance(signal, SignalEvent)
    assert signal.direction == 'LONG'
    assert signal.symbol == symbol