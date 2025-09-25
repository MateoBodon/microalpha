# microalpha/strategies/mm.py
from ..events import SignalEvent


class NaiveMarketMakingStrategy:
    """
    A simple market-making strategy that continuously places a buy (bid)
    and a sell (ask) order around the current market price.
    It aims to profit from the bid-ask spread.
    """

    def __init__(self, symbol: str, spread: float = 0.5, inventory_limit: int = 100):
        self.symbol = symbol
        self.spread = spread
        self.inventory_limit = inventory_limit
        self.invested = 0  # Track our current inventory (can be positive or negative)

    def calculate_signals(self, event, events_queue):
        """
        On every market update, generate buy/sell signals based on our
        desired spread and current inventory.
        """
        if event.symbol != self.symbol:
            return

        mid_price = event.price
        bid_price = mid_price - self.spread / 2.0
        ask_price = mid_price + self.spread / 2.0

        # --- TRADING LOGIC ---
        # If we have room to buy (not at our long inventory limit)
        # we send a signal. A real MM would place a limit order at the bid.
        # We simulate this by sending a LONG signal, hoping to get filled
        # at a price below the mid-price.
        if self.invested < self.inventory_limit:
            # For simplicity, we'll just use a generic 'LONG' signal.
            # A more advanced engine would support order types (LIMIT vs MARKET).
            signal = SignalEvent(event.timestamp, self.symbol, "LONG")
            events_queue.put(signal)

        # If we have room to sell (not at our short inventory limit)
        # we send a signal to get out of our long position or go short.
        elif self.invested > -self.inventory_limit:
            signal = SignalEvent(event.timestamp, self.symbol, "EXIT")  # or 'SHORT'
            events_queue.put(signal)

        print(
            f"  STRATEGY (MM): Mid: {mid_price:.2f}, Quoting Bid: {bid_price:.2f}, Ask: {ask_price:.2f}"
        )
