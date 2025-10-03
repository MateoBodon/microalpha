# microalpha/strategies/mm.py
from ..events import SignalEvent


class NaiveMarketMakingStrategy:
    """Toy market-making strategy that oscillates inventory."""

    def __init__(self, symbol: str, spread: float = 0.5, inventory_limit: int = 100):
        self.symbol = symbol
        self.spread = spread
        self.inventory_limit = inventory_limit
        self.inventory = 0

    def on_market(self, event) -> list[SignalEvent]:
        if event.symbol != self.symbol:
            return []

        if self.inventory < self.inventory_limit:
            self.inventory += 1
            return [SignalEvent(event.timestamp, self.symbol, "LONG")]

        self.inventory = 0
        return [SignalEvent(event.timestamp, self.symbol, "EXIT")]
