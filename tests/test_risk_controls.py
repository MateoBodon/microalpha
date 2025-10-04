from microalpha.events import MarketEvent, SignalEvent
from microalpha.portfolio import Portfolio


class StubDataHandler:
    def __init__(self, price=100.0):
        self.price = price

    def get_latest_price(self, symbol, timestamp):
        return self.price

    def get_future_timestamps(self, start_timestamp, n):
        return [start_timestamp + 1]


def initialise_portfolio(**kwargs):
    data = StubDataHandler()
    portfolio = Portfolio(data_handler=data, initial_cash=100000.0, **kwargs)
    market_event = MarketEvent(timestamp=1, symbol="SPY", price=100.0, volume=1.0)
    portfolio.on_market(market_event)
    return portfolio


def test_max_exposure_blocks_orders_exceeding_limit():
    portfolio = initialise_portfolio(max_exposure=0.5)
    signal = SignalEvent(timestamp=1, symbol="SPY", side="LONG", meta={"qty": 800})
    assert list(portfolio.on_signal(signal)) == []

    allowed_signal = SignalEvent(
        timestamp=1, symbol="SPY", side="LONG", meta={"qty": 400}
    )
    orders = list(portfolio.on_signal(allowed_signal))
    assert orders and orders[0].qty == 400


def test_drawdown_stop_halts_new_positions():
    portfolio = initialise_portfolio(max_drawdown_stop=0.2)
    portfolio.cash = 70000.0
    drawdown_event = MarketEvent(timestamp=2, symbol="SPY", price=100.0, volume=1.0)
    portfolio.on_market(drawdown_event)

    long_signal = SignalEvent(timestamp=2, symbol="SPY", side="LONG")
    assert list(portfolio.on_signal(long_signal)) == []


def test_turnover_cap_blocks_when_exceeded():
    portfolio = initialise_portfolio(turnover_cap=10000.0)
    portfolio.total_turnover = 9500.0
    signal = SignalEvent(timestamp=1, symbol="SPY", side="LONG", meta={"qty": 100})
    assert list(portfolio.on_signal(signal)) == []


def test_kelly_fraction_sizes_orders():
    portfolio = initialise_portfolio(kelly_fraction=0.1)
    signal = SignalEvent(timestamp=1, symbol="SPY", side="LONG")
    orders = list(portfolio.on_signal(signal))
    assert orders
    assert orders[0].qty == 100
