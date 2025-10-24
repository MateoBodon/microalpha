# tests/test_strategies.py
from microalpha.events import MarketEvent, SignalEvent
from microalpha.strategies.breakout import BreakoutStrategy
from microalpha.strategies.mom import CrossSectionalMomentum


def test_breakout_strategy_generates_long_signal():
    symbol = "TEST"
    strategy = BreakoutStrategy(symbol=symbol, lookback=5)

    prices = [100, 101, 102, 101, 100, 103]
    signals: list[SignalEvent] = []

    for ts, price in enumerate(prices):
        market_event = MarketEvent(timestamp=ts, symbol=symbol, price=price, volume=1.0)
        signals.extend(strategy.on_market(market_event))

    assert len(signals) == 1
    signal = signals[0]
    assert signal.side == "LONG"
    assert signal.symbol == symbol


def test_cross_sectional_momentum_batch_signals():
    symbols = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    strat = CrossSectionalMomentum(symbol_universe=symbols, lookback_months=1, skip_months=0, top_frac=0.4)

    # Build 30 days of prices with AAA/BBB trending up
    events = []
    for t in range(30):
        for s in symbols:
            base = 100.0
            drift = {"AAA": 0.02, "BBB": 0.015}.get(s, 0.0)
            price = base * (1 + drift) ** t
            events.append(MarketEvent(timestamp=t, symbol=s, price=price, volume=1.0))

    # Feed in batches per timestamp
    for i in range(0, len(events), len(symbols)):
        batch = events[i : i + len(symbols)]
        signals = strat.on_market_batch(batch)

    # After warmup, expect AAA/BBB to be held (LONG signals emitted)
    holds = strat.current_holds
    assert {"AAA", "BBB"}.issubset(holds)
