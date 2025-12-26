"""Flagship cross-sectional momentum strategy."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from ..allocators import budgeted_allocator
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
        cov_lookback_days: int = 63,
        allocator: str = "budgeted_rp",
        allocator_kwargs: Mapping[str, float] | None = None,
        total_risk_budget: float = 1.0,
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
        self.cov_lookback_days = int(max(10, cov_lookback_days))
        self.allocator_name = str(allocator).lower()
        self.allocator_kwargs = dict(allocator_kwargs or {})
        self.total_risk_budget = float(max(total_risk_budget, 0.0))

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
        self._filter_diagnostics: List[Dict[str, float | int | str]] = []

    # ------------------------------------------------------------------
    def get_filter_diagnostics(self) -> Dict[str, object]:
        entries = list(self._filter_diagnostics)
        summary: Dict[str, Dict[str, float | int]] = {}
        keys = [
            "universe_total",
            "with_history",
            "min_price_pass",
            "min_adv_pass",
            "frame_count",
            "long_target",
            "short_target",
            "long_selected",
            "short_selected",
            "long_sector_cap_rejections",
            "short_sector_cap_rejections",
        ]
        for key in keys:
            values = [int(entry.get(key, 0) or 0) for entry in entries]
            if values:
                summary[key] = {
                    "min": int(min(values)),
                    "max": int(max(values)),
                    "mean": float(np.mean(values)),
                }
            else:
                summary[key] = {"min": 0, "max": 0, "mean": 0.0}
        return {
            "rebalance_count": int(len(entries)),
            "summary": summary,
            "per_rebalance": entries,
        }

    # ------------------------------------------------------------------
    def _init_rebalance_diagnostics(
        self, period_end: pd.Timestamp, universe: Optional[pd.DataFrame]
    ) -> Dict[str, float | int | str]:
        return {
            "period_end": str(period_end.date()),
            "universe_total": int(len(universe)) if universe is not None else 0,
            "with_history": 0,
            "min_price_pass": 0,
            "min_adv_pass": 0,
            "frame_count": 0,
            "long_target": 0,
            "short_target": 0,
            "long_selected": 0,
            "short_selected": 0,
            "long_sector_cap_rejections": 0,
            "short_sector_cap_rejections": 0,
        }

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
        diagnostics = self._init_rebalance_diagnostics(period_end, universe)
        if universe is None or universe.empty:
            self._filter_diagnostics.append(diagnostics)
            return []

        frame = self._build_score_frame(universe, diagnostics)
        if frame.empty:
            self._filter_diagnostics.append(diagnostics)
            return []

        long_sel = self._select_sleeve(frame, sleeve="long", diagnostics=diagnostics)
        short_sel = self._select_sleeve(frame, sleeve="short", diagnostics=diagnostics)
        self._filter_diagnostics.append(diagnostics)
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
    def _build_score_frame(
        self,
        universe: pd.DataFrame,
        diagnostics: Optional[Dict[str, float | int | str]] = None,
    ) -> pd.DataFrame:
        records: List[Dict[str, float | str]] = []
        required = self._required_bars()
        skip_days = self.skip_months * TRADING_DAYS_MONTH
        lookback_days = self.lookback_months * TRADING_DAYS_MONTH

        for symbol, row in universe.iterrows():
            symbol_str = str(symbol).upper()
            prices = self.price_history.get(symbol_str)
            if not prices or len(prices) < required:
                continue
            if diagnostics is not None:
                diagnostics["with_history"] = int(diagnostics["with_history"]) + 1
            if prices[-1] < self.min_price:
                continue
            if diagnostics is not None:
                diagnostics["min_price_pass"] = int(diagnostics["min_price_pass"]) + 1

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
            if diagnostics is not None:
                diagnostics["min_adv_pass"] = int(diagnostics["min_adv_pass"]) + 1

            records.append(
                {
                    "symbol": symbol_str,
                    "sector": str(row.get("sector", self.sector_map.get(symbol_str, "UNKNOWN"))),
                    "momentum": float(momentum),
                    "adv": adv,
                    "close": float(row.get("close", prices[-1])),
                }
            )

        if diagnostics is not None:
            diagnostics["frame_count"] = len(records)
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
    def _select_sleeve(
        self,
        frame: pd.DataFrame,
        sleeve: str,
        diagnostics: Optional[Dict[str, float | int | str]] = None,
    ) -> SleeveSelection:
        if frame.empty:
            return SleeveSelection([], frame.iloc[0:0])
        count = len(frame)
        if sleeve == "long":
            target_n = int(round(count * self.top_frac))
            ascending = False
            target_key = "long_target"
            selected_key = "long_selected"
            rejected_key = "long_sector_cap_rejections"
        else:
            target_n = int(round(count * self.bottom_frac))
            ascending = True
            target_key = "short_target"
            selected_key = "short_selected"
            rejected_key = "short_sector_cap_rejections"

        if target_n <= 0:
            if diagnostics is not None:
                diagnostics[target_key] = 0
                diagnostics[selected_key] = 0
            return SleeveSelection([], frame.iloc[0:0])
        target_n = max(1, target_n)
        if diagnostics is not None:
            diagnostics[target_key] = int(target_n)

        ordered = frame.sort_values("sector_z", ascending=ascending)
        selected_rows = []
        per_sector: Dict[str, int] = defaultdict(int)
        for _, row in ordered.iterrows():
            sector = str(row["sector"])
            if per_sector[sector] >= self.max_positions_per_sector:
                if diagnostics is not None:
                    diagnostics[rejected_key] = int(diagnostics[rejected_key]) + 1
                continue
            selected_rows.append(row)
            per_sector[sector] += 1
            if len(selected_rows) >= target_n:
                break

        if not selected_rows:
            if diagnostics is not None:
                diagnostics[selected_key] = 0
            return SleeveSelection([], frame.iloc[0:0])
        selected = pd.DataFrame(selected_rows)
        if diagnostics is not None:
            diagnostics[selected_key] = int(len(selected_rows))
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
        weights = self._compute_weights(longs, shorts)

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
                        meta={
                            "reason": "rebalance",
                            "period_end": str(period_end.date()),
                            "weight": 0.0,
                        },
                    )
                )
                self.position_side[symbol] = 0

        for _, row in longs.frame.iterrows():
            symbol = str(row["symbol"])
            meta = self._signal_meta(row, "long", period_end)
            meta["weight"] = float(weights.get(symbol, 0.0))
            if self.position_side.get(symbol, 0) < 0:
                signals.append(
                    SignalEvent(
                        event_timestamp,
                        symbol,
                        "EXIT",
                        meta={
                            "reason": "flip_to_long",
                            "period_end": str(period_end.date()),
                            "weight": 0.0,
                        },
                    )
                )
            if self.position_side.get(symbol, 0) <= 0:
                signals.append(SignalEvent(event_timestamp, symbol, "LONG", meta=meta))
            self.position_side[symbol] = 1

        for _, row in shorts.frame.iterrows():
            symbol = str(row["symbol"])
            meta = self._signal_meta(row, "short", period_end)
            meta["weight"] = float(weights.get(symbol, 0.0))
            if self.position_side.get(symbol, 0) > 0:
                signals.append(
                    SignalEvent(
                        event_timestamp,
                        symbol,
                        "EXIT",
                        meta={
                            "reason": "flip_to_short",
                            "period_end": str(period_end.date()),
                            "weight": 0.0,
                        },
                    )
                )
            if self.position_side.get(symbol, 0) >= 0:
                signals.append(SignalEvent(event_timestamp, symbol, "SHORT", meta=meta))
            self.position_side[symbol] = -1

        return signals

    def _compute_weights(
        self, longs: SleeveSelection, shorts: SleeveSelection
    ) -> pd.Series:
        symbols_order = list(dict.fromkeys(longs.symbols + shorts.symbols))
        if not symbols_order or self.total_risk_budget <= 0.0:
            return pd.Series(dtype=float)

        returns_df, cov = self._covariance_inputs(symbols_order)
        if cov.empty:
            return self._fallback_weights(longs, shorts)

        signals = {}
        for _, row in longs.frame.iterrows():
            value = float(row.get("sector_z", row.get("momentum", 0.0)))
            signals[str(row["symbol"])] = max(value, 0.0) + 1e-9
        for _, row in shorts.frame.iterrows():
            value = float(row.get("sector_z", row.get("momentum", 0.0)))
            signals[str(row["symbol"])] = -abs(value) - 1e-9

        signal_series = pd.Series(signals)
        ridge = float(self.allocator_kwargs.get("ridge", 1e-8))
        risk_model = str(self.allocator_kwargs.get("risk_model", self.allocator_name))
        allow_short = bool(self.allocator_kwargs.get("allow_short", False))

        try:
            weights = budgeted_allocator(
                signal_series,
                cov,
                total_budget=self.total_risk_budget,
                ridge=ridge,
                risk_model=risk_model,
                returns=returns_df,
                allow_short=allow_short,
            )
        except ValueError:
            weights = self._fallback_weights(longs, shorts)

        return weights.reindex(symbols_order).fillna(0.0)

    def _covariance_inputs(
        self, symbols: Sequence[str]
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        returns: Dict[str, np.ndarray] = {}
        lookback = self.cov_lookback_days
        for sym in symbols:
            prices = self.price_history.get(sym, [])
            if prices is None or len(prices) < lookback + 1:
                continue
            tail = np.asarray(prices[-(lookback + 1) :], dtype=float)
            if np.any(tail <= 0):
                continue
            rets = np.diff(np.log(tail))
            if np.allclose(rets, 0):
                continue
            returns[sym] = rets

        if not returns:
            return pd.DataFrame(), pd.DataFrame()

        returns_df = pd.DataFrame(returns).dropna(axis=0, how="any")
        if returns_df.empty:
            return pd.DataFrame(), pd.DataFrame()
        cov = returns_df.cov()
        return returns_df, cov

    def _fallback_weights(
        self, longs: SleeveSelection, shorts: SleeveSelection
    ) -> pd.Series:
        weights: Dict[str, float] = {}
        total = len(longs.symbols) + len(shorts.symbols)
        if total == 0:
            return pd.Series(dtype=float)
        if longs.symbols:
            long_budget = self.total_risk_budget * (len(longs.symbols) / total)
            per_long = long_budget / max(len(longs.symbols), 1)
            for sym in longs.symbols:
                weights[sym] = per_long
        if shorts.symbols:
            short_budget = self.total_risk_budget * (len(shorts.symbols) / total)
            per_short = short_budget / max(len(shorts.symbols), 1)
            for sym in shorts.symbols:
                weights[sym] = -per_short
        return pd.Series(weights)

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
