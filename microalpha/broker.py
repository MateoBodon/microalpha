# microalpha/broker.py
from .events import FillEvent
from .slippage import VolumeSlippageModel 

class SimulatedBroker:
    def __init__(self, data_handler, slippage_model=None):
        """
        The broker can now accept a slippage model.
        If no model is provided, it defaults to our VolumeSlippageModel.
        """
        self.data_handler = data_handler
        self.slippage_model = slippage_model if slippage_model else VolumeSlippageModel()

    def execute_order(self, order_event, events_queue):
        """
        Simulates filling an order, now with slippage applied.
        """
        symbol = order_event.symbol
        timestamp = order_event.timestamp
        quantity = order_event.quantity
        direction = order_event.direction

        current_price = self.data_handler.get_latest_price(symbol, timestamp)

        if current_price is None:
            print(f"      BROKER: No price for {symbol} at {timestamp}. Order rejected.")
            return

        # --- SLIPPAGE CALCULATION ---
        slippage = self.slippage_model.calculate_slippage(quantity, current_price)

        if direction == 'BUY':
            # For buys, slippage increases the price
            fill_price = current_price + slippage
            fill_cost = quantity * fill_price
        elif direction == 'SELL':
            # For sells, slippage decreases the price
            fill_price = current_price - slippage
            # Cost is negative (cash comes in)
            fill_cost = - (quantity * fill_price)
        # ----------------------------

        commission = 1.0

        fill = FillEvent(
            timestamp, symbol, quantity, direction,
            fill_cost=fill_cost, commission=commission
        )
        events_queue.put(fill)
        print(f"      BROKER: Order for {quantity} {symbol} filled at ${fill_price:.2f} (slippage: ${slippage:.4f}/share).")