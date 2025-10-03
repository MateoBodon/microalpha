# tests/test_no_lookahead.py
import pytest

from microalpha.events import LookaheadError, SignalEvent
from microalpha.portfolio import Portfolio


def test_portfolio_raises_lookahead_error_on_stale_signal():
    """
    Tests that the portfolio raises an error if it receives a SignalEvent
    with a timestamp that is earlier than its current known time.
    """

    # 1. Arrange
    # A mock data handler is needed for the Portfolio's constructor
    class MockDataHandler:
        def get_latest_price(self, symbol, timestamp):
            return 100.0

    portfolio = Portfolio(data_handler=MockDataHandler(), initial_cash=100000.0)

    # Set the portfolio's "current time" to a specific point
    portfolio.current_time = 2

    # Create a signal event with a timestamp from the PAST
    stale_signal = SignalEvent(timestamp=1, symbol="SPY", side="LONG")

    # 2. Act & 3. Assert
    # We expect a LookaheadError to be raised when processing the stale event.
    # pytest.raises acts as a context manager to catch the expected error.
    with pytest.raises(LookaheadError):
        list(portfolio.on_signal(stale_signal))
