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
        print("Starting backtest...")
        for event in self.data_handler.stream_events():
            self.events_queue.put(event)

        while self.running:
            try:
                event = self.events_queue.get(block=False)
            except queue.Empty:
                self.running = False
                continue

            if isinstance(event, MarketEvent):
                print(f"ENGINE: Processing MarketEvent at {event.timestamp}")
                self.strategy.calculate_signals(event, self.events_queue)

            elif isinstance(event, SignalEvent):
                self.portfolio.on_signal(event, self.events_queue)

            elif isinstance(event, OrderEvent):
                self.broker.execute_order(event, self.events_queue)

            elif isinstance(event, FillEvent):
                self.portfolio.on_fill(event)

        print("Backtest finished.")