# microalpha/portfolio.py
from .events import OrderEvent

class Portfolio:
    def __init__(self, initial_cash=100000.0):
        self.cash = initial_cash
        self.holdings = {} # { 'SYMBOL': quantity }

    def on_signal(self, signal_event, events_queue):
        """
        Acts on a SignalEvent to generate an OrderEvent.
        Simple implementation: fixed quantity of 100 shares.
        """
        symbol = signal_event.symbol
        direction = signal_event.direction
        quantity = 100 # Fixed size for simplicity

        if direction == 'LONG':
            order = OrderEvent(signal_event.timestamp, symbol, quantity, 'BUY')
            events_queue.put(order)
            print(f"    PORTFOLIO: Creating BUY order for {quantity} {symbol}.")
        elif direction == 'EXIT':
            if symbol in self.holdings and self.holdings[symbol] > 0:
                order = OrderEvent(signal_event.timestamp, symbol, self.holdings[symbol], 'SELL')
                events_queue.put(order)
                print(f"    PORTFOLIO: Creating SELL order for {self.holdings[symbol]} {symbol}.")

    def on_fill(self, fill_event):
        """
        Updates holdings from a FillEvent.
        """
        symbol = fill_event.symbol
        quantity = fill_event.quantity
        direction = fill_event.direction
        fill_cost = fill_event.fill_cost
        commission = fill_event.commission

        # Update cash
        self.cash -= (fill_cost + commission)

        # Update holdings
        if direction == 'BUY':
            self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        elif direction == 'SELL':
            self.holdings[symbol] = self.holdings.get(symbol, 0) - quantity

        print(f"      BROKER->PORTFOLIO: Fill processed. Cash: {self.cash:.2f}, Holdings: {self.holdings}")