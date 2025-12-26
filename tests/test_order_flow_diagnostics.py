import pandas as pd

from microalpha.broker import SimulatedBroker
from microalpha.data import MultiCsvDataHandler
from microalpha.engine import Engine
from microalpha.events import SignalEvent
from microalpha.execution import Executor
from microalpha.order_flow import OrderFlowDiagnostics
from microalpha.portfolio import Portfolio
from microalpha.strategies.flagship_mom import (
    FlagshipMomentumStrategy,
    TRADING_DAYS_MONTH,
)


def _write_prices(tmp_path, symbol, dates, prices):
    frame = pd.DataFrame({"close": prices}, index=pd.to_datetime(dates))
    frame.to_csv(tmp_path / f"{symbol}.csv")


def test_order_flow_diagnostics_populated(tmp_path):
    _write_prices(tmp_path, "AAA", ["2020-01-31", "2020-02-03"], [50.0, 52.0])
    _write_prices(tmp_path, "BBB", ["2020-01-31", "2020-02-03"], [60.0, 61.0])

    universe_path = tmp_path / "universe.csv"
    pd.DataFrame(
        {
            "date": ["2020-02-14", "2020-02-14"],
            "symbol": ["AAA", "BBB"],
            "sector": ["A", "B"],
            "adv_20": [1_000_000.0, 1_000_000.0],
            "close": [50.0, 60.0],
        }
    ).to_csv(universe_path, index=False)

    required = (1 + 0) * TRADING_DAYS_MONTH + 1
    warmup_history = {
        "AAA": [10.0 + i * 0.1 for i in range(required)],
        "BBB": [20.0 + i * 0.1 for i in range(required)],
    }

    strategy = FlagshipMomentumStrategy(
        symbols=["AAA", "BBB"],
        universe_path=str(universe_path),
        lookback_months=1,
        skip_months=0,
        top_frac=1.0,
        bottom_frac=0.0,
        min_adv=0.0,
        min_price=1.0,
        cov_lookback_days=10,
        warmup_history=warmup_history,
    )

    data_handler = MultiCsvDataHandler(csv_dir=tmp_path, symbols=["AAA", "BBB"])
    order_flow = OrderFlowDiagnostics()
    portfolio = Portfolio(data_handler=data_handler, order_flow=order_flow)
    broker = SimulatedBroker(Executor(data_handler=data_handler))

    engine = Engine(data_handler, strategy, portfolio, broker)
    engine.run()

    order_flow.merge_filter_diagnostics(strategy.get_filter_diagnostics())
    payload = order_flow.payload()

    assert payload["entries"]
    entry = payload["entries"][0]
    assert entry["selected_long"] >= 1
    assert entry["target_weights_nonzero_count"] >= 1
    assert entry["orders_created_count"] >= 1
    assert entry["orders_accepted_count"] >= 1
    assert entry["fills_count"] >= 1
    assert entry["filled_notional"] > 0


def test_order_flow_drop_reason_bucket():
    class _StubData:
        def get_latest_price(self, symbol, timestamp):
            return 100.0

    order_flow = OrderFlowDiagnostics()
    portfolio = Portfolio(data_handler=_StubData(), order_flow=order_flow)
    signal = SignalEvent(timestamp=0, symbol="AAA", side="LONG", meta={"qty": 0})

    order_flow.begin_rebalance([signal], 0)
    orders = portfolio.on_signal(signal)
    assert orders == []

    payload = order_flow.payload()
    entry = payload["entries"][0]
    assert entry["orders_dropped_reason_counts"]["qty_rounded_to_zero"] == 1


def test_order_flow_missing_optional_fields_safe():
    order_flow = OrderFlowDiagnostics()
    order_flow.merge_filter_diagnostics({"summary": {}})
    payload = order_flow.payload()
    assert "errors" in payload
    assert "filter_diagnostics_missing_per_rebalance" in payload["errors"]
