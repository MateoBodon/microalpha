"""Order flow diagnostics for post-signal execution tracing."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

import pandas as pd

from .events import FillEvent, OrderEvent, SignalEvent


def _timestamp_to_date(ts: int | None) -> str:
    if ts is None:
        return "unknown"
    try:
        return str(pd.Timestamp(ts).date())
    except Exception:
        return "unknown"


def _signal_rebalance_key(signal: SignalEvent | None, timestamp: int | None) -> str:
    if signal is not None and signal.meta:
        period_end = signal.meta.get("period_end")
        if period_end:
            return str(period_end)
    return _timestamp_to_date(timestamp if timestamp is not None else None)


def _new_entry(key: str) -> Dict[str, Any]:
    return {
        "rebalance_date": key,
        "selected_long": 0,
        "selected_short": 0,
        "target_weights_nonzero_count": 0,
        "sum_abs_weights": 0.0,
        "min_weight": None,
        "max_weight": None,
        "count_clipped_by_caps": 0,
        "orders_created_count": 0,
        "orders_nonzero_qty_count": 0,
        "orders_dropped_reason_counts": {},
        "orders_clipped_reason_counts": {},
        "orders_accepted_count": 0,
        "orders_rejected_count": 0,
        "orders_rejected_reason_counts": {},
        "fills_count": 0,
        "filled_notional": 0.0,
    }


@dataclass
class OrderFlowDiagnostics:
    """Collect per-rebalance order flow diagnostics without affecting execution."""

    _entries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _active_key: str | None = None
    _errors: List[str] = field(default_factory=list)

    def _entry_for_key(self, key: str) -> Dict[str, Any]:
        entry = self._entries.get(key)
        if entry is None:
            entry = _new_entry(key)
            self._entries[key] = entry
        return entry

    def _resolve_key(
        self,
        *,
        signal: SignalEvent | None = None,
        order: OrderEvent | None = None,
        timestamp: int | None = None,
    ) -> str:
        if self._active_key is not None:
            return self._active_key
        if signal is not None:
            return _signal_rebalance_key(signal, signal.timestamp)
        if order is not None:
            return _timestamp_to_date(order.timestamp)
        return _timestamp_to_date(timestamp)

    def record_error(self, message: str) -> None:
        self._errors.append(str(message))

    def begin_rebalance(
        self, signals: Iterable[SignalEvent], timestamp: int | None = None
    ) -> str:
        try:
            signals_list = list(signals)
        except Exception as exc:  # pragma: no cover - defensive
            self.record_error(f"begin_rebalance signals error: {type(exc).__name__}: {exc}")
            key = _timestamp_to_date(timestamp)
            self._active_key = key
            self._entry_for_key(key)
            return key

        key = (
            _signal_rebalance_key(signals_list[0], timestamp)
            if signals_list
            else _timestamp_to_date(timestamp)
        )
        entry = self._entry_for_key(key)
        self._active_key = key

        try:
            selected_long = sum(1 for s in signals_list if s.side == "LONG")
            selected_short = sum(1 for s in signals_list if s.side == "SHORT")
            entry["selected_long"] = int(selected_long)
            entry["selected_short"] = int(selected_short)

            weights: List[float] = []
            for sig in signals_list:
                if sig.side == "EXIT":
                    continue
                if not sig.meta:
                    continue
                weight = sig.meta.get("weight")
                if weight is None:
                    continue
                try:
                    weight_val = float(weight)
                except (TypeError, ValueError):
                    continue
                if math.isfinite(weight_val):
                    weights.append(weight_val)

            nonzero_weights = [w for w in weights if abs(w) > 0]
            entry["target_weights_nonzero_count"] = int(len(nonzero_weights))
            entry["sum_abs_weights"] = float(sum(abs(w) for w in weights)) if weights else 0.0
            entry["min_weight"] = float(min(weights)) if weights else None
            entry["max_weight"] = float(max(weights)) if weights else None
        except Exception as exc:  # pragma: no cover - diagnostics should not fail run
            self.record_error(
                f"begin_rebalance stats error: {type(exc).__name__}: {exc}"
            )
        return key

    def end_rebalance(self) -> None:
        self._active_key = None

    def record_order_created(self, order: OrderEvent, signal: SignalEvent | None = None) -> None:
        key = self._resolve_key(signal=signal, order=order)
        entry = self._entry_for_key(key)
        entry["orders_created_count"] = int(entry["orders_created_count"]) + 1
        if abs(int(getattr(order, "qty", 0) or 0)) > 0:
            entry["orders_nonzero_qty_count"] = int(entry["orders_nonzero_qty_count"]) + 1

    def record_order_drop(
        self,
        reason: str,
        *,
        signal: SignalEvent | None = None,
        order: OrderEvent | None = None,
        clipped_by_caps: bool = False,
    ) -> None:
        key = self._resolve_key(signal=signal, order=order)
        entry = self._entry_for_key(key)
        counts = entry["orders_dropped_reason_counts"]
        counts[reason] = int(counts.get(reason, 0)) + 1
        if clipped_by_caps:
            entry["count_clipped_by_caps"] = int(entry["count_clipped_by_caps"]) + 1

    def record_order_clip(
        self,
        reason: str,
        *,
        signal: SignalEvent | None = None,
        order: OrderEvent | None = None,
    ) -> None:
        key = self._resolve_key(signal=signal, order=order)
        entry = self._entry_for_key(key)
        entry["count_clipped_by_caps"] = int(entry["count_clipped_by_caps"]) + 1
        buckets = entry["orders_clipped_reason_counts"]
        buckets[reason] = int(buckets.get(reason, 0)) + 1

    def record_broker_accept(self, order: OrderEvent) -> None:
        key = self._resolve_key(order=order)
        entry = self._entry_for_key(key)
        entry["orders_accepted_count"] = int(entry["orders_accepted_count"]) + 1

    def record_broker_reject(self, order: OrderEvent, reason: str | None) -> None:
        key = self._resolve_key(order=order)
        entry = self._entry_for_key(key)
        entry["orders_rejected_count"] = int(entry["orders_rejected_count"]) + 1
        reason_key = reason or "unknown"
        buckets = entry["orders_rejected_reason_counts"]
        buckets[reason_key] = int(buckets.get(reason_key, 0)) + 1

    def record_fill(self, fill: FillEvent) -> None:
        key = self._resolve_key(timestamp=fill.timestamp)
        entry = self._entry_for_key(key)
        entry["fills_count"] = int(entry["fills_count"]) + 1
        try:
            entry["filled_notional"] = float(entry["filled_notional"]) + abs(
                float(fill.qty) * float(fill.price)
            )
        except (TypeError, ValueError):
            self.record_error("fill_notional_cast_error")

    def merge_filter_diagnostics(self, filter_diagnostics: Mapping[str, Any] | None) -> None:
        if filter_diagnostics is None:
            return
        if not isinstance(filter_diagnostics, Mapping):
            self.record_error("filter_diagnostics_not_mapping")
            return
        per_rebalance = filter_diagnostics.get("per_rebalance")
        if not isinstance(per_rebalance, list):
            self.record_error("filter_diagnostics_missing_per_rebalance")
            return
        for entry in per_rebalance:
            if not isinstance(entry, Mapping):
                continue
            key = str(entry.get("period_end", "unknown"))
            diag_entry = self._entry_for_key(key)
            if "long_selected" in entry:
                try:
                    diag_entry["selected_long"] = int(entry.get("long_selected") or 0)
                except (TypeError, ValueError):
                    self.record_error("filter_diagnostics_long_selected_cast")
            if "short_selected" in entry:
                try:
                    diag_entry["selected_short"] = int(entry.get("short_selected") or 0)
                except (TypeError, ValueError):
                    self.record_error("filter_diagnostics_short_selected_cast")

    def _aggregate_reason_counts(self, key: str) -> Dict[str, int]:
        totals: Counter[str] = Counter()
        for entry in self._entries.values():
            bucket = entry.get(key)
            if isinstance(bucket, Mapping):
                for reason, count in bucket.items():
                    try:
                        totals[str(reason)] += int(count)
                    except (TypeError, ValueError):
                        continue
        return dict(totals)

    def summary(self) -> Dict[str, Any]:
        entries = list(self._entries.values())
        summary = {
            "rebalance_count": int(len(entries)),
            "orders_created": int(
                sum(int(e.get("orders_created_count", 0) or 0) for e in entries)
            ),
            "orders_accepted": int(
                sum(int(e.get("orders_accepted_count", 0) or 0) for e in entries)
            ),
            "orders_rejected": int(
                sum(int(e.get("orders_rejected_count", 0) or 0) for e in entries)
            ),
            "fills": int(sum(int(e.get("fills_count", 0) or 0) for e in entries)),
            "filled_notional": float(
                sum(float(e.get("filled_notional", 0.0) or 0.0) for e in entries)
            ),
            "clipped_by_caps": int(
                sum(int(e.get("count_clipped_by_caps", 0) or 0) for e in entries)
            ),
            "targets_nonzero": int(
                sum(int(e.get("target_weights_nonzero_count", 0) or 0) for e in entries)
            ),
            "sum_abs_weights": float(
                sum(float(e.get("sum_abs_weights", 0.0) or 0.0) for e in entries)
            ),
            "orders_dropped_reason_counts": self._aggregate_reason_counts(
                "orders_dropped_reason_counts"
            ),
            "orders_clipped_reason_counts": self._aggregate_reason_counts(
                "orders_clipped_reason_counts"
            ),
            "orders_rejected_reason_counts": self._aggregate_reason_counts(
                "orders_rejected_reason_counts"
            ),
        }
        if self._errors:
            summary["errors"] = list(self._errors)
        return summary

    def payload(self) -> Dict[str, Any]:
        entries = sorted(self._entries.values(), key=lambda e: str(e.get("rebalance_date")))
        payload: Dict[str, Any] = {"entries": entries, "summary": self.summary()}
        if self._errors:
            payload["errors"] = list(self._errors)
        return payload


def infer_non_degenerate_reason(payload: Mapping[str, Any] | None) -> str | None:
    if not payload or not isinstance(payload, Mapping):
        return None
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        return "no_targets"

    totals = {
        "targets_nonzero": 0,
        "orders_created": 0,
        "orders_nonzero_qty": 0,
        "orders_accepted": 0,
        "orders_rejected": 0,
        "fills": 0,
        "qty_zero_drops": 0,
    }
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        totals["targets_nonzero"] += int(entry.get("target_weights_nonzero_count", 0) or 0)
        totals["orders_created"] += int(entry.get("orders_created_count", 0) or 0)
        totals["orders_nonzero_qty"] += int(entry.get("orders_nonzero_qty_count", 0) or 0)
        totals["orders_accepted"] += int(entry.get("orders_accepted_count", 0) or 0)
        totals["orders_rejected"] += int(entry.get("orders_rejected_count", 0) or 0)
        totals["fills"] += int(entry.get("fills_count", 0) or 0)
        drops = entry.get("orders_dropped_reason_counts")
        if isinstance(drops, Mapping):
            totals["qty_zero_drops"] += int(drops.get("qty_rounded_to_zero", 0) or 0)

    if totals["targets_nonzero"] <= 0:
        return "no_targets"
    if totals["orders_created"] <= 0:
        return "no_orders"
    if totals["orders_nonzero_qty"] <= 0 and totals["qty_zero_drops"] > 0:
        return "qty_rounded_to_zero"
    if totals["orders_created"] > 0 and totals["orders_accepted"] <= 0:
        return "broker_rejected_all"
    if totals["fills"] <= 0:
        return "no_fills"
    return None
