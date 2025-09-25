# microalpha/strategies/breakout.py
from ..events import SignalEvent


class BreakoutStrategy:
    """
    A simple momentum strategy that enters a long position when the price
    breaks above a recent high.
    """

    def __init__(self, symbol: str, lookback: int = 20):
        self.symbol = symbol
        self.lookback = lookback
        self.prices = []
        self.invested = False

    def calculate_signals(self, event, events_queue):
        """
        Calculates a signal on a new MarketEvent.
        """
        if event.symbol != self.symbol:
            return

        self.prices.append(event.price)

        if len(self.prices) < self.lookback:
            return  # Not enough data yet

        # Keep our price list at the lookback length
        self.prices.pop(0)

        current_price = self.prices[-1]
        # Highest price in the lookback window, excluding the current price
        lookback_high = max(self.prices[:-1])

        # --- TRADING LOGIC ---
        # If the current price breaks above the recent high and we're not invested, buy.
        if current_price > lookback_high and not self.invested:
            signal = SignalEvent(event.timestamp, self.symbol, "LONG")
            events_queue.put(signal)
            self.invested = True
            print(
                f"  STRATEGY: Firing LONG signal. Price {current_price:.2f} broke high of {lookback_high:.2f}"
            )

        # Simple exit logic: if we are invested, we'll just hold.
        # A more complex strategy would have a sell condition (e.g., trailing stop).
