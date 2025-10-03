# microalpha/broker.py
from .events import FillEvent, OrderEvent
from .slippage import VolumeSlippageModel


class SimulatedBroker:
    def __init__(
        self, data_handler, slippage_model=None, execution_style="INSTANT", num_ticks=4
    ):
        """
        The broker can now accept an execution style.
        - 'INSTANT': Fills the entire order at once (original behavior).
        - 'TWAP': Splits the order into `num_ticks` smaller child orders.
        """
        self.data_handler = data_handler
        self.slippage_model = (
            slippage_model if slippage_model else VolumeSlippageModel()
        )
        self.execution_style = execution_style
        self.num_ticks = num_ticks
        self._open_orders = []  # A list to hold orders being worked (for TWAP)

    def on_order(self, order_event, events_queue):
        """
        Receives a new meta-order from the portfolio.
        """
        if self.execution_style == "TWAP":
            # For TWAP, we break the order into child orders and store them.
            self._schedule_twap_orders(order_event)
        else:  # 'INSTANT'
            # For INSTANT, we execute the full order immediately.
            self._execute_trade(order_event, events_queue)

    def on_market_tick(self, market_event, events_queue):
        """
        Triggered on every new MarketEvent. Executes any scheduled child orders.
        """
        if not self._open_orders:
            return

        # Use a list comprehension to keep only the orders that are not yet filled
        remaining_orders = []
        for order in self._open_orders:
            if order.timestamp == market_event.timestamp:
                print(
                    f"      BROKER (TWAP): Executing child order for {order.quantity} {order.symbol}."
                )
                self._execute_trade(order, events_queue)
            elif order.timestamp > market_event.timestamp:
                remaining_orders.append(order)  # This order is for a future tick

        self._open_orders = remaining_orders

    def _schedule_twap_orders(self, order_event):
        """
        Splits a meta-order into smaller child orders for TWAP execution.
        This is now robust to running out of market data.
        """
        total_quantity = order_event.quantity

        # Get the next N timestamps from the data handler
        future_timestamps = self.data_handler.get_future_timestamps(
            start_timestamp=order_event.timestamp, n=self.num_ticks
        )

        if not future_timestamps:
            print(
                "      BROKER: No future ticks to execute TWAP. Executing instantly on next tick."
            )
            # We need at least one future timestamp to execute. If none, we can't do anything.
            # A more advanced implementation might place a limit order. For now, we drop it.
            return

        # Adjust the number of ticks to the actual number of available data points
        effective_num_ticks = len(future_timestamps)
        child_quantity = total_quantity // effective_num_ticks

        if child_quantity == 0:
            print(
                f"      BROKER: Order quantity ({total_quantity}) is too small to split over {effective_num_ticks} ticks. Executing in one chunk."
            )
            # Create a single child order for the full amount on the next tick
            single_child = OrderEvent(
                future_timestamps[0],
                order_event.symbol,
                total_quantity,
                order_event.direction,
            )
            self._open_orders.append(single_child)
            return

        print(
            f"      BROKER (TWAP): Scheduling {total_quantity} shares over {effective_num_ticks} ticks."
        )
        for i in range(effective_num_ticks):
            qty = child_quantity
            # Distribute the remainder across the first few orders
            if i < total_quantity % effective_num_ticks:
                qty += 1

            if qty > 0:
                child_order = OrderEvent(
                    timestamp=future_timestamps[i],
                    symbol=order_event.symbol,
                    quantity=qty,
                    direction=order_event.direction,
                )
                self._open_orders.append(child_order)

    def _execute_trade(self, order_event, events_queue):
        """
        Simulates filling a single trade, now with slippage applied.
        This is the final step for both INSTANT orders and TWAP child orders.
        """
        symbol = order_event.symbol
        timestamp = order_event.timestamp
        quantity = order_event.quantity
        direction = order_event.direction

        current_price = self.data_handler.get_latest_price(symbol, timestamp)

        if current_price is None:
            print(
                f"      BROKER: No price for {symbol} at {timestamp}. Order rejected."
            )
            return

        # --- SLIPPAGE CALCULATION ---
        slippage = self.slippage_model.calculate_slippage(quantity, current_price)

        if direction == "BUY":
            fill_price = current_price + slippage
            fill_cost = quantity * fill_price
        elif direction == "SELL":
            fill_price = current_price - slippage
            fill_cost = -(quantity * fill_price)
        # ----------------------------

        commission = 1.0

        fill = FillEvent(
            timestamp,
            symbol,
            quantity,
            direction,
            fill_cost=fill_cost,
            commission=commission,
        )
        events_queue.put(fill)
        print(
            f"      BROKER: Order for {quantity} {symbol} filled at ${fill_price:.2f} (slippage: ${slippage:.4f}/share)."
        )
