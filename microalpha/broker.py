# microalpha/broker.py
from .events import FillEvent

class SimulatedBroker:
    def __init__(self, data_handler):
        """
        The broker now needs access to the data_handler to get the
        latest price for filling orders.
        """
        self.data_handler = data_handler

    def execute_order(self, order_event, events_queue):
        """
        Simulates filling an order.

        The fill price is now correctly retrieved from the latest market data
        for the given symbol. This removes the lookahead bias.
        """
        symbol = order_event.symbol
        timestamp = order_event.timestamp

        # Get the current market price from the data handler
        # In a more complex system, this would be the OPEN of the next bar
        current_price = self.data_handler.get_latest_price(symbol, timestamp)
        
        if current_price is None:
            print(f"      BROKER: Could not get price for {symbol} at {timestamp}. Order rejected.")
            return

        commission = 1.0  # Fixed commission

        # Calculate fill cost
        fill_cost = 0
        if order_event.direction == 'BUY':
            fill_cost = order_event.quantity * current_price
        elif order_event.direction == 'SELL':
            # For sells, the cost is negative (cash comes in)
            fill_cost = - (order_event.quantity * current_price)

        fill = FillEvent(
            timestamp,
            symbol,
            order_event.quantity,
            order_event.direction,
            fill_cost=fill_cost,
            commission=commission
        )
        events_queue.put(fill)
        print(f"      BROKER: Order for {order_event.quantity} {symbol} filled at ${current_price:.2f}.")