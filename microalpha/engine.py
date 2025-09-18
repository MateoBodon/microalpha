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

        for market_event in self.data_handler.stream_events():
            self.events_queue.put(market_event)

            while not self.events_queue.empty():
                try:
                    event = self.events_queue.get(block=False)
                except queue.Empty:
                    break

                if isinstance(event, MarketEvent):
                    print(f"ENGINE: Processing MarketEvent at {event.timestamp}")
                    self.portfolio.update_timeindex(event)
                    self.strategy.calculate_signals(event, self.events_queue)
                    # Notify the broker of the market tick for TWAP execution
                    self.broker.on_market_tick(event, self.events_queue)

                elif isinstance(event, SignalEvent):
                    self.portfolio.on_signal(event, self.events_queue)

                elif isinstance(event, OrderEvent):
                    # The broker now receives orders via on_order
                    self.broker.on_order(event, self.events_queue) 

                elif isinstance(event, FillEvent):
                    self.portfolio.on_fill(event)

        print("Backtest finished.")