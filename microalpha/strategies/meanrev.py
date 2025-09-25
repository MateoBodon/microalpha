# microalpha/strategies/meanrev.py
import pandas as pd
from ..events import SignalEvent

class MeanReversionStrategy:
    """
    A simple mean reversion strategy based on z-scores.
    """
    def __init__(self, symbol: str, lookback: int = 5, z_threshold: float = 1.0):
        self.symbol = symbol
        self.lookback = lookback
        self.z_threshold = z_threshold
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
            return # Not enough data yet

        # Keep the price list to the lookback size
        self.prices.pop(0)

        price_series = pd.Series(self.prices)
        mean = price_series.mean()
        std = price_series.std()

        if std == 0: # Avoid division by zero
            return

        z_score = (price_series.iloc[-1] - mean) / std

        # Go long
        if z_score < -self.z_threshold and not self.invested:
            signal = SignalEvent(event.timestamp, self.symbol, 'LONG')
            events_queue.put(signal)
            self.invested = True
            print(f"  STRATEGY: Firing LONG signal. z-score={z_score:.2f}")
        # Go short (or flat)
        elif z_score > self.z_threshold and self.invested:
            signal = SignalEvent(event.timestamp, self.symbol, 'EXIT')
            events_queue.put(signal)
            self.invested = False
            print(f"  STRATEGY: Firing EXIT signal. z-score={z_score:.2f}")