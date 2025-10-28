"""Flagship cross-sectional momentum strategy."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from ..events import SignalEvent

TRADING_DAYS_MONTH = 21


@dataclass
class SleeveSelection:
    symbols: List[str]
    frame: pd.DataFrame


class FlagshipMomentumStrategy:
    """Cross-sectional momentum with sector normalisation and sleeve controls."""

    def __init__(
        self,
        symbols: Iterable[str],
        universe_path: str,
        lookback_months: int = 12,
        skip_months: int = 1,
        top_frac: float = 0.25,
        bottom_frac: float = 0.25,
        max_positions_per_sector: int = 8,
        min_adv: float = 5_000_000.0,
        min_price: float = 5.0,
        turnover_target_pct_adv: float = 0.1,
        rebalance_frequency: str = "M",
        warmup_history: Mapping[str, Sequence[float]] | None = None,
    ) -> None:
        if not universe_path:
            raise ValueError("FlagshipMomentumStrategy expects a universe_path.")

        self.symbols = [s.upper() for s in symbols]
        self.symbol_set = set(self.symbols)
        self.lookback_months = int(max(1, lookback_months))
        self.skip_months = int(max(0, skip_months))
        self.top_frac = float(max(0.0, min(1.0, top_frac)))
        self.bottom_frac = float(max(0.0, min(1.0, bottom_frac)))
        self.max_positions_per_sector = max(1, int(max_positions_per_sector))
        self.min_adv = float(min_adv)
        self.min_price = float(min_price)
        self.turnover_target_pct_adv = float(max(turnover_target_pct_adv, 0.0))
        self.rebalance_frequency = rebalance_frequency

        self.price_history: Dict[str, List[float]] = {
            sym: list(warmup_history.get(sym, [])) if warmup_history else []
            for sym in self.symbols
        }
        self.position_side: Dict[str, int] = {sym: 0 for sym in self.symbols}
        self.last_period: Optional[pd.Timestamp] = None
        self.sector_map: Dict[str, str] = {}

        self.universe = self._load_universe(universe_path)
        self.universe_dates = sorted(self.universe.keys())
        self.max_history = (
            (self.lookback_months + self.skip_months + 2) * TRADING_DAYS_MONTH
        )

    # ------------------------------------------------------------------
    def _load_universe(self, path: str) -> Dict[pd.Timestamp, pd.DataFrame]:
        df = pd.read_csv(path)
        if "symbol" not in df.columns or "date" not in df.columns:
            raise ValueError(
                "Universe file must contain at least 'symbol' and 'date' columns."
            )

        df["symbol"] = df["symbol"].astype(str).str.upper()
        df["date"] = pd.to_datetime(df["date"])
        df["rebalance"] = df["date"].dt.to_period("M").dt.to_timestamp("M")
        if "sector" not in df.columns:
            df["sector"] = "UNKNOWN"
        for column in ("adv_20", "adv_63", "adv_126", "market_cap_proxy"):
            if column not in df.columns:
                df[column] = np.nan
        df.set_index(["rebalance", "symbol"], inplace=True)

        universe: Dict[pd.Timestamp, pd.DataFrame] = {}
        for rebalance_date, group in df.groupby(level=0):
            rebalance_ts = pd.Timestamp(rebalance_date)
            snapshot = group.droplevel(0).copy()
            snapshot["sector"] = snapshot["sector"].fillna("UNKNOWN")
            snapshot["adv_20"] = snapshot["adv_20"].fillna(0.0)
            snapshot["close"] = snapshot.get("close", pd.Series(dtype=float)).fillna(
                0.0
            )
            universe[rebalance_ts] = snapshot
        latest_sector = (
            df.reset_index()
            .sort_values("rebalance")
            .drop_duplicates("symbol", keep="last")
            .set_index("symbol")
        )
        self.sector_map = {
            sym: str(row.get("sector", "UNKNOWN"))
            for sym, row in latest_sector.iterrows()
        }
        return universe

    # ------------------------------------------------------------------
    def on_market(self, event) -> List[SignalEvent]:
        if event.symbol not in self.symbol_set:
            return []

        history = self.price_history.setdefault(event.symbol, [])
        history.append(float(event.price))
        if len(history) > self.max_history:
            del history[:-self.max_history]

        timestamp = pd.to_datetime(event.timestamp)
        period_end = (
            timestamp.to_period(self.rebalance_frequency)
            .to_timestamp(how="end")
            .normalize()
        )

        if self.last_period is None:
            self.last_period = period_end
            return []
        if period_end <= self.last_period:
            return []

        signals = self._rebalance(period_end, event.timestamp)
        self.last_period = period_end
        return signals

    # ------------------------------------------------------------------
    def _rebalance(
        self, period_end: pd.Timestamp, event_timestamp: int
    ) -> List[SignalEvent]:
        universe = self._universe_snapshot(period_end)
        if universe is None or universe.empty:
            return []

        frame = self._build_score_frame(universe)
        if frame.empty:
            return []

        long_sel = self._select_sleeve(frame, sleeve="long")
        short_sel = self._select_sleeve(frame, sleeve="short")
        return self._build_signals(long_sel, short_sel, event_timestamp, period_end)

    # ------------------------------------------------------------------
    def _universe_snapshot(
        self, period_end: pd.Timestamp
    ) -> Optional[pd.DataFrame]:
        eligible = [date for date in self.universe_dates if date <= period_end]
        if not eligible:
            return None
        latest = max(eligible)
        return self.universe.get(latest)

    # ------------------------------------------------------------------
    def _required_bars(self) -> int:
        return (self.lookback_months + self.skip_months) * TRADING_DAYS_MONTH + 1

    # ------------------------------------------------------------------
    def _build_score_frame(self, universe: pd.DataFrame) -> pd.DataFrame:
        records: List[Dict[str, float | str]] = []
        required = self._required_bars()
        skip_days = self.skip_months * TRADING_DAYS_MONTH
        lookback_days = self.lookback_months * TRADING_DAYS_MONTH

        for symbol, row in universe.iterrows():
            symbol_str = str(symbol).upper()
            prices = self.price_history.get(symbol_str)
            if not prices or len(prices) < required:
                continue
            if prices[-1] < self.min_price:
                continue

            recent_idx = -skip_days - 1 if skip_days > 0 else -1
            if abs(recent_idx) > len(prices):
                continue
            past_idx = recent_idx - lookback_days
            if abs(past_idx) > len(prices):
                continue
            past_price = prices[past_idx]
            recent_price = prices[recent_idx]
            if past_price <= 0:
                continue
            momentum = (recent_price / past_price) - 1.0
            adv = float(row.get("adv_20", 0.0) or 0.0)
            if adv < self.min_adv:
                continue

            records.append(
                {
                    "symbol": symbol_str,
                    "sector": str(row.get("sector", self.sector_map.get(symbol_str, "UNKNOWN"))),
                    "momentum": float(momentum),
                    "adv": adv,
                    "close": float(row.get("close", prices[-1])),
                }
            )

        if not records:
            return pd.DataFrame()

        frame = pd.DataFrame.from_records(records)
        # Sector-normalised z-score
        frame["sector_mean"] = frame.groupby("sector")["momentum"].transform("mean")
        frame["sector_std"] = (
            frame.groupby("sector")["momentum"].transform("std").replace(0.0, np.nan)
        )
        frame["sector_z"] = (frame["momentum"] - frame["sector_mean"]) / frame[
            "sector_std"
        ]
        frame["sector_z"] = frame["sector_z"].fillna(
            frame["momentum"] - frame["sector_mean"]
        )
        single_name = frame.groupby("sector")["momentum"].transform("count") <= 1
        frame.loc[single_name, "sector_z"] = frame.loc[single_name, "momentum"]
        frame["sector_z"] = frame["sector_z"].fillna(0.0)
        frame.drop(columns=["sector_mean", "sector_std"], inplace=True)
        return frame

    # ------------------------------------------------------------------
    def _select_sleeve(self, frame: pd.DataFrame, sleeve: str) -> SleeveSelection:
        if frame.empty:
            return SleeveSelection([], frame.iloc[0:0])
        count = len(frame)
        if sleeve == "long":
            target_n = int(round(count * self.top_frac))
            ascending = False
        else:
            target_n = int(round(count * self.bottom_frac))
            ascending = True

        if target_n <= 0:
            return SleeveSelection([], frame.iloc[0:0])
        target_n = max(1, target_n)

        ordered = frame.sort_values("sector_z", ascending=ascending)
        selected_rows = []
        per_sector: Dict[str, int] = defaultdict(int)
        for _, row in ordered.iterrows():
            sector = str(row["sector"])
            if per_sector[sector] >= self.max_positions_per_sector:
                continue
            selected_rows.append(row)
            per_sector[sector] += 1
            if len(selected_rows) >= target_n:
                break

        if not selected_rows:
            return SleeveSelection([], frame.iloc[0:0])
        selected = pd.DataFrame(selected_rows)
        return SleeveSelection(selected["symbol"].tolist(), selected)

    # ------------------------------------------------------------------
    def _build_signals(
        self,
        longs: SleeveSelection,
        shorts: SleeveSelection,
        event_timestamp: int,
        period_end: pd.Timestamp,
    ) -> List[SignalEvent]:
        long_set = set(longs.symbols)
        short_set = set(shorts.symbols)
        conflicts = long_set & short_set
        for sym in conflicts:
            long_score = float(
                longs.frame.loc[longs.frame["symbol"] == sym, "sector_z"].iloc[0]
            )
            short_score = float(
                shorts.frame.loc[shorts.frame["symbol"] == sym, "sector_z"].iloc[0]
            )
            if abs(long_score) >= abs(short_score):
                short_set.remove(sym)
                shorts.frame = shorts.frame[shorts.frame["symbol"] != sym]
            else:
                long_set.remove(sym)
                longs.frame = longs.frame[longs.frame["symbol"] != sym]

        signals: List[SignalEvent] = []
        for symbol, side in list(self.position_side.items()):
            if side == 0:
                continue
            if (side > 0 and symbol not in long_set) or (
                side < 0 and symbol not in short_set
            ):
                signals.append(
                    SignalEvent(
                        event_timestamp,
                        symbol,
                        "EXIT",
                        meta={"reason": "rebalance", "period_end": str(period_end.date())},
                    )
                )
                self.position_side[symbol] = 0

        for _, row in longs.frame.iterrows():
            symbol = str(row["symbol"])
            meta = self._signal_meta(row, "long", period_end)
            if self.position_side.get(symbol, 0) < 0:
                signals.append(
                    SignalEvent(
                        event_timestamp,
                        symbol,
                        "EXIT",
                        meta={"reason": "flip_to_long", "period_end": str(period_end.date())},
                    )
                )
            if self.position_side.get(symbol, 0) <= 0:
                signals.append(SignalEvent(event_timestamp, symbol, "LONG", meta=meta))
            self.position_side[symbol] = 1

        for _, row in shorts.frame.iterrows():
            symbol = str(row["symbol"])
            meta = self._signal_meta(row, "short", period_end)
            if self.position_side.get(symbol, 0) > 0:
                signals.append(
                    SignalEvent(
                        event_timestamp,
                        symbol,
                        "EXIT",
                        meta={"reason": "flip_to_short", "period_end": str(period_end.date())},
                    )
                )
            if self.position_side.get(symbol, 0) >= 0:
                signals.append(SignalEvent(event_timestamp, symbol, "SHORT", meta=meta))
            self.position_side[symbol] = -1

        return signals

    # ------------------------------------------------------------------
    def _signal_meta(
        self, row: pd.Series, sleeve: str, period_end: pd.Timestamp
    ) -> Dict[str, float | str]:
        adv = float(row.get("adv", 0.0))
        heat = (
            self.turnover_target_pct_adv
            if adv <= 0
            else min(self.turnover_target_pct_adv, 1.0)
        )
        return {
            "sleeve": sleeve,
            "sector": str(row.get("sector", "UNKNOWN")),
            "momentum": float(row.get("momentum", 0.0)),
            "sector_z": float(row.get("sector_z", 0.0)),
            "adv_20": adv,
            "turnover_heat": heat,
            "period_end": str(period_end.date()),
            "lookback_months": float(self.lookback_months),
            "skip_months": float(self.skip_months),
        }
