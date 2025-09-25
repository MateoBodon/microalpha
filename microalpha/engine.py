# microalpha/engine.py
import queue
from .events import MarketEvent, SignalEvent, OrderEvent, FillEvent

class Engine:
    def __init__(self, data_handler, strategy, portfolio, broker):
        self.data_handler = data_handler
        self.strategy = strategy
        self.portfolio = portfolio
        self.broker = broker
        self.events_queue = queue.Queue()
        self.running = True

    def run(self):
        """
        The main event loop, corrected to process events chronologically.
        """
        print("Starting backtest...")

        # The outer loop is now the "heartbeat" driven by market data.
        for market_event in self.data_handler.stream_events():
            # Put the new market data onto the queue
            self.events_queue.put(market_event)

            # Process all events that result from this market data
            # before moving to the next heartbeat.
            while not self.events_queue.empty():
                try:
                    event = self.events_queue.get(block=False)
                except queue.Empty:
                    break # No more events for this time tick

                if isinstance(event, MarketEvent):
                    self.portfolio.update_timeindex(event)
                    print(f"ENGINE: Processing MarketEvent at {event.timestamp}")
                    self.strategy.calculate_signals(event, self.events_queue)

                elif isinstance(event, SignalEvent):
                    self.portfolio.on_signal(event, self.events_queue)

                elif isinstance(event, OrderEvent):
                    self.broker.execute_order(event, self.events_queue)

                elif isinstance(event, FillEvent):
                    self.portfolio.on_fill(event)

        print("Backtest finished.")