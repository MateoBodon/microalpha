# microalpha/portfolio.py
from .events import LookaheadError, OrderEvent


class Portfolio:
    def __init__(self, data_handler, initial_cash=100000.0):
        self.data_handler = data_handler
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.holdings = {}
        self.equity_curve = []
        self.current_time = None
        self.total_turnover = 0.0

    def update_timeindex(self, event):
        """
        Updates the portfolio's state for a new timestamp.
        """
        self.current_time = event.timestamp

        market_value = 0.0
        for symbol, quantity in self.holdings.items():
            price = self.data_handler.get_latest_price(symbol, self.current_time)
            if price is not None:
                market_value += quantity * price

        total_equity = self.cash + market_value
        exposure = market_value / total_equity if total_equity != 0 else 0

        self.equity_curve.append(
            {
                "timestamp": self.current_time,
                "equity": total_equity,
                "exposure": exposure,  # Track exposure over time
            }
        )

    def on_fill(self, fill_event):
        """Updates holdings from a FillEvent and tracks turnover."""
        if self.current_time and fill_event.timestamp < self.current_time:
            raise LookaheadError("Fill event timestamp is in the past.")

        symbol = fill_event.symbol
        quantity = fill_event.quantity
        direction = fill_event.direction
        fill_cost = fill_event.fill_cost
        commission = fill_event.commission

        # --- UPDATE TURNOVER ---
        # fill_cost is negative for sells, so abs() gives the trade value
        self.total_turnover += abs(fill_cost)
        # -----------------------

        self.cash -= fill_cost + commission

        if direction == "BUY":
            self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        elif direction == "SELL":
            self.holdings[symbol] = self.holdings.get(symbol, 0) - quantity

        print(
            f"      BROKER->PORTFOLIO: Fill processed. Cash: {self.cash:.2f}, Holdings: {self.holdings}"
        )

    def on_signal(self, signal_event, events_queue):
        """
        Acts on a SignalEvent to generate an OrderEvent.
        """
        if self.current_time and signal_event.timestamp < self.current_time:
            raise LookaheadError("Signal event timestamp is in the past.")

        symbol = signal_event.symbol
        direction = signal_event.direction
        # INCREASED order size to make TWAP meaningful
        quantity = 400

        if direction == "LONG":
            order = OrderEvent(signal_event.timestamp, symbol, quantity, "BUY")
            events_queue.put(order)
            print(f"    PORTFOLIO: Creating BUY meta-order for {quantity} {symbol}.")
        elif direction == "EXIT":
            if symbol in self.holdings and self.holdings[symbol] > 0:
                # Ensure we don't sell more than we have
                sell_quantity = self.holdings[symbol]
                order = OrderEvent(
                    signal_event.timestamp, symbol, sell_quantity, "SELL"
                )
                events_queue.put(order)
                print(
                    f"    PORTFOLIO: Creating SELL meta-order for {sell_quantity} {symbol}."
                )
