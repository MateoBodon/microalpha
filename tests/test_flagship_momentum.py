from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Sequence

import numpy as np
import pandas as pd

from microalpha.events import MarketEvent
from microalpha.strategies.flagship_mom import FlagshipMomentumStrategy


def _write_universe(
    tmp_path: Path,
    symbols: Sequence[str],
    sectors: Dict[str, str],
    adv: float = 20_000_000.0,
) -> Path:
    rows = []
    for date in ("2020-01-31", "2020-02-29"):
        for sym in symbols:
            rows.append(
                {
                    "symbol": sym,
                    "date": date,
                    "sector": sectors[sym],
                    "adv_20": adv,
                    "adv_63": adv,
                    "adv_126": adv,
                    "market_cap_proxy": 1_000_000_000.0,
                    "close": 50.0,
                }
            )
    df = pd.DataFrame(rows)
    path = tmp_path / "universe.csv"
    df.to_csv(path, index=False)
    return path


def _make_history(length: int, start: float, trend: float) -> list[float]:
    idx = np.arange(length, dtype=float)
    series = start + trend * idx
    return series.tolist()


def test_flagship_sector_normalised_signals(tmp_path: Path) -> None:
    symbols = ["AAA", "AAB", "BBB", "BBC"]
    sectors = {"AAA": "TECH", "AAB": "TECH", "BBB": "HEALTH", "BBC": "HEALTH"}
    universe = _write_universe(tmp_path, symbols, sectors)

    history = {
        "AAA": _make_history(70, 60.0, 0.40),  # strong up
        "AAB": _make_history(70, 55.0, -0.05),  # weak/down
        "BBB": _make_history(70, 45.0, 0.18),  # up
        "BBC": _make_history(70, 50.0, -0.12),  # down but stays liquid
    }

    strategy = FlagshipMomentumStrategy(
        symbols=symbols,
        universe_path=str(universe),
        lookback_months=2,
        skip_months=1,
        top_frac=0.5,
        bottom_frac=0.5,
        max_positions_per_sector=1,
        turnover_target_pct_adv=0.08,
        warmup_history=history,
    )

    # First event sets initial period without rebalance
    ts_feb = pd.Timestamp("2020-02-28")
    for sym in symbols:
        value = history[sym][-1]
        event = MarketEvent(int(ts_feb.value), sym, value, 1_000_000.0)
        assert strategy.on_market(event) == []

    # March rebalance triggers signals using new prices consistent with trends
    ts_mar = pd.Timestamp("2020-03-31")
    signals = []
    for sym in symbols:
        price = history[sym][-1] + (0.3 if sym in {"AAA", "BBB"} else -0.3)
        signals.extend(strategy.on_market(MarketEvent(int(ts_mar.value), sym, price, 1_000_000.0)))

    assert {s.symbol for s in signals if s.side == "LONG"} == {"AAA", "BBB"}
    assert {s.symbol for s in signals if s.side == "SHORT"} == {"AAB", "BBC"}
    assert all(s.meta and "sector_z" in s.meta for s in signals if s.side != "EXIT")
    assert all(s.meta and s.meta.get("turnover_heat") == 0.08 for s in signals)
    assert all(s.meta and s.meta.get("sleeve") in {"long", "short"} for s in signals if s.side != "EXIT")
    assert all("weight" in (s.meta or {}) for s in signals if s.side in {"LONG", "SHORT"})
    long_budget = sum(s.meta["weight"] for s in signals if s.side == "LONG")
    short_budget = sum(abs(s.meta["weight"]) for s in signals if s.side == "SHORT")
    assert long_budget > 0
    assert short_budget > 0
    assert math.isclose(long_budget + short_budget, strategy.total_risk_budget, rel_tol=1e-6)


def test_flagship_requires_full_warmup_before_signalling(tmp_path: Path) -> None:
    symbols = ["AAA", "BBB"]
    sectors = {"AAA": "TECH", "BBB": "HEALTH"}
    universe = _write_universe(tmp_path, symbols, sectors, adv=6_000_000.0)

    warmup_history = {
        "AAA": _make_history(20, 40.0, 0.10),
        "BBB": _make_history(20, 35.0, -0.05),
    }

    lookback = 2
    skip = 1
    required = (lookback + skip) * 21 + 1

    strategy = FlagshipMomentumStrategy(
        symbols=symbols,
        universe_path=str(universe),
        lookback_months=lookback,
        skip_months=skip,
        top_frac=0.5,
        bottom_frac=0.5,
        warmup_history=warmup_history,
    )

    dates = pd.date_range("2020-02-01", periods=120, freq="D")
    first_signal_step: int | None = None
    captured: list = []

    for idx, date in enumerate(dates):
        for sym in symbols:
            base = warmup_history[sym][-1]
            drift = 0.20 if sym == "AAA" else -0.10
            price = base + drift * idx
            out = strategy.on_market(
                MarketEvent(int(date.value), sym, price, 500_000.0)
            )
            if out and first_signal_step is None:
                first_signal_step = idx + len(warmup_history[sym])
            if out and first_signal_step is not None:
                captured.extend(out)

    assert first_signal_step is not None, "strategy should eventually emit signals"
    assert first_signal_step >= required, "signals must wait for full momentum history"
    assert any(sig.side == "LONG" for sig in captured)
    assert any(sig.side == "SHORT" for sig in captured)
