# microalpha/strategies/mm.py
from ..events import SignalEvent

class NaiveMarketMakingStrategy:
    """
    A simple market-making strategy that continuously places a buy (bid)
    and a sell (ask) order around the current market price.
    It aims to profit from the bid-ask spread.
    """
    def __init__(self, symbol: str, spread: float = 0.5):
        self.symbol = symbol
        # The desired spread in dollars (e.g., $0.50)
        self.spread = spread
        # We'll use this to cancel and replace orders
        self.last_order_id = None 

    def calculate_signals(self, event, events_queue):
        """
        On every market update, generate new buy and sell signals.
        """
        if event.symbol != self.symbol:
            return

        # Calculate our desired bid and ask prices
        bid_price = event.price - self.spread / 2.0
        ask_price = event.price + self.spread / 2.0

        # Note: A true market-making system would use Limit Orders (LMT).
        # Since our simple broker only handles Market Orders (MKT), we'll simulate
        # this by sending LONG and SHORT signals. The key is that we are always
        # in the market, ready to both buy and sell. In this simplified version,
        # we'll just send a signal to go long, assuming we want to capture any
        # upward movement from our bid.
        
        # For simplicity, we'll just fire a LONG signal.
        buy_signal = SignalEvent(event.timestamp, self.symbol, 'LONG')
        sell_signal = SignalEvent(event.timestamp, self.symbol, 'SHORT') # or 'EXIT'
        
        # In this naive version, we'll just alternate for demonstration
        # We will just put a LONG signal on the queue to show the logic can be plugged in.
        events_queue.put(buy_signal)
        
        print(f"  STRATEGY (MM): Quoting Bid: {bid_price:.2f}, Ask: {ask_price:.2f}")