# microalpha/broker.py
from .events import FillEvent

class SimulatedBroker:
    def __init__(self):
        # In a real system, this would connect to an exchange API
        pass

    def execute_order(self, order_event, events_queue):
        """
        Simulates filling an order.
        For simplicity, we assume the order is filled instantly at the
        last known market price. We also add a fixed commission.
        """
        # In a real backtester, you'd get the fill price from the DataHandler.
        # We will add this logic later. For now, it's a placeholder.
        # This is a source of lookahead bias we will fix!
        fill_price = 400.0 # Placeholder!
        commission = 1.0 # Fixed commission

        cost = 0
        if order_event.direction == 'BUY':
            cost = order_event.quantity * fill_price
        elif order_event.direction == 'SELL':
            cost = - (order_event.quantity * fill_price)

        fill = FillEvent(
            order_event.timestamp,
            order_event.symbol,
            order_event.quantity,
            order_event.direction,
            fill_cost=cost,
            commission=commission
        )
        events_queue.put(fill)
        print(f"      BROKER: Order executed and FillEvent created.")