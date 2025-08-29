# microalpha/engine.py
import queue
from .events import MarketEvent

class Engine:
    """
    The core event-driven engine.
    """
    def __init__(self, data_handler):
        self.data_handler = data_handler
        self.events_queue = queue.Queue()
        self.running = True

    def run(self):
        """
        The main event loop.
        It will continuously check the events queue and process events
        until the backtest is complete.
        """
        print("Starting backtest...")
        # Prime the queue with initial market data
        for event in self.data_handler.stream_events():
            self.events_queue.put(event)

        while self.running:
            try:
                event = self.events_queue.get(block=False)
            except queue.Empty:
                # If the queue is empty, the backtest is over
                self.running = False
                continue

            # For now, we just print the event to prove the loop works
            if isinstance(event, MarketEvent):
                print(f"Time: {event.timestamp}, Symbol: {event.symbol}, Price: {event.price}")

        print("Backtest finished.")