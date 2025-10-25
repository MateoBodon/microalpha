# microalpha/strategies/breakout.py
from ..events import SignalEvent


class BreakoutStrategy:
    """Breakout momentum strategy with simple exits.

    - Entry: price breaks above prior N-day high
    - Exit: price crosses below prior N-day low or time stop M bars
    """

    def __init__(
        self,
        symbol: str,
        lookback: int = 20,
        exit_lookback: int | None = None,
        time_stop: int | None = None,
    ):
        self.symbol = symbol
        self.lookback = lookback
        self.exit_lookback = exit_lookback or lookback
        self.time_stop = time_stop or (lookback // 2)
        self.prices: list[float] = []
        self.invested = False
        self.bars_in_trade = 0

    def on_market(self, event) -> list[SignalEvent]:
        if event.symbol != self.symbol:
            return []

        self.prices.append(event.price)
        signals: list[SignalEvent] = []

        if len(self.prices) >= self.lookback:
            window = self.prices[-self.lookback :]
            current_price = window[-1]
            lookback_high = max(window[:-1])

            if not self.invested and current_price > lookback_high:
                self.invested = True
                self.bars_in_trade = 0
                signals.append(SignalEvent(event.timestamp, self.symbol, "LONG"))

        if self.invested:
            self.bars_in_trade += 1
            exit_window = self.prices[-self.exit_lookback :]
            if len(exit_window) >= self.exit_lookback:
                exit_level = min(exit_window[:-1])
                if exit_window[-1] < exit_level:
                    self.invested = False
                    self.bars_in_trade = 0
                    signals.append(SignalEvent(event.timestamp, self.symbol, "EXIT"))
                    return signals

            if self.time_stop and self.bars_in_trade >= self.time_stop:
                self.invested = False
                self.bars_in_trade = 0
                signals.append(SignalEvent(event.timestamp, self.symbol, "EXIT"))

        return signals
