# microalpha/strategies/meanrev.py
import pandas as pd

from ..events import SignalEvent


class MeanReversionStrategy:
    """A simple mean-reversion strategy based on z-scores."""

    def __init__(
        self,
        symbol: str,
        lookback: int = 5,
        z_threshold: float = 1.0,
        warmup_prices=None,
    ):
        self.symbol = symbol
        self.lookback = lookback
        self.z_threshold = z_threshold
        self.prices = [] if warmup_prices is None else list(warmup_prices)
        self.invested = False

    def on_market(self, event) -> list[SignalEvent]:
        if event.symbol != self.symbol:
            return []

        self.prices.append(event.price)
        if len(self.prices) < self.lookback:
            return []

        self.prices = self.prices[-self.lookback :]
        price_series = pd.Series(self.prices)
        mean = price_series.mean()
        std = price_series.std()
        if std == 0:
            return []

        z_score = (price_series.iloc[-1] - mean) / std
        signals: list[SignalEvent] = []

        if z_score < -self.z_threshold and not self.invested:
            signals.append(SignalEvent(event.timestamp, self.symbol, "LONG"))
            self.invested = True
        elif z_score > self.z_threshold and self.invested:
            signals.append(SignalEvent(event.timestamp, self.symbol, "EXIT"))
            self.invested = False

        return signals
