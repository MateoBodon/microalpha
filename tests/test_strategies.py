# tests/test_strategies.py
from microalpha.events import MarketEvent, SignalEvent
from microalpha.strategies.breakout import BreakoutStrategy


def test_breakout_strategy_generates_long_signal():
    symbol = "TEST"
    strategy = BreakoutStrategy(symbol=symbol, lookback=5)

    prices = [100, 101, 102, 101, 100, 103]
    signals: list[SignalEvent] = []

    for ts, price in enumerate(prices):
        market_event = MarketEvent(timestamp=ts, symbol=symbol, price=price, volume=1.0)
        signals.extend(strategy.on_market(market_event))

    assert len(signals) == 1
    signal = signals[0]
    assert signal.side == "LONG"
    assert signal.symbol == symbol
