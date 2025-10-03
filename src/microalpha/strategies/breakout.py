# microalpha/strategies/breakout.py
from ..events import SignalEvent


class BreakoutStrategy:
    """Breakout momentum strategy."""

    def __init__(self, symbol: str, lookback: int = 20):
        self.symbol = symbol
        self.lookback = lookback
        self.prices: list[float] = []
        self.invested = False

    def on_market(self, event) -> list[SignalEvent]:
        if event.symbol != self.symbol:
            return []

        self.prices.append(event.price)
        if len(self.prices) < self.lookback:
            return []

        self.prices = self.prices[-self.lookback :]
        current_price = self.prices[-1]
        lookback_high = max(self.prices[:-1])

        if current_price > lookback_high and not self.invested:
            self.invested = True
            return [SignalEvent(event.timestamp, self.symbol, "LONG")]

        return []
