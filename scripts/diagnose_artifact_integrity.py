"""Diagnose equity/metrics integrity for a single artifact directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def _load_metrics(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _count_trades(path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    if path.suffix.lower() == ".jsonl":
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        return int(len(df))
    return 0


def _resolve_trades_path(artifact_dir: Path) -> Path | None:
    for candidate in ("trades.jsonl", "trades.csv"):
        path = artifact_dir / candidate
        if path.exists():
            return path
    return None


def _equity_stats(equity_df: pd.DataFrame) -> dict:
    if equity_df.empty or "equity" not in equity_df.columns:
        return {"count": 0}
    equity = pd.Series(equity_df["equity"], dtype=float)
    returns = (
        pd.Series(equity_df["returns"], dtype=float)
        if "returns" in equity_df.columns
        else equity.pct_change().fillna(0.0)
    )
    return {
        "count": int(len(equity)),
        "min": float(equity.min()),
        "max": float(equity.max()),
        "std": float(equity.std(ddof=0)),
        "returns_std": float(returns.std(ddof=0)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", required=True, type=Path)
    args = parser.parse_args()

    artifact_dir = args.artifact_dir.expanduser().resolve()
    if not artifact_dir.exists():
        raise SystemExit(f"Artifact directory not found: {artifact_dir}")

    equity_path = artifact_dir / "equity_curve.csv"
    metrics_path = artifact_dir / "metrics.json"
    trades_path = _resolve_trades_path(artifact_dir)

    metrics = _load_metrics(metrics_path)
    equity_df = pd.read_csv(equity_path) if equity_path.exists() else pd.DataFrame()
    stats = _equity_stats(equity_df)

    turnover = float(metrics.get("total_turnover", 0.0) or 0.0)
    num_trades_metric = int(metrics.get("num_trades", 0) or 0)
    trades_count = _count_trades(trades_path)

    commission = float(metrics.get("commission_total", 0.0) or 0.0)
    slippage = float(metrics.get("slippage_total", 0.0) or 0.0)
    borrow = float(metrics.get("borrow_cost_total", 0.0) or 0.0)
    total_costs = commission + slippage + borrow

    equity_constant = False
    if stats.get("count", 0) > 1:
        equity_constant = abs(stats["max"] - stats["min"]) <= 1e-8

    print("Artifact:", artifact_dir)
    print("Equity rows:", stats.get("count", 0))
    if stats.get("count", 0):
        print("Equity min/max/std:", stats["min"], stats["max"], stats["std"])
        print("Returns std:", stats["returns_std"])
    print("Trades (metrics/trades file):", num_trades_metric, "/", trades_count)
    print("Turnover:", turnover)
    print("Costs (commission/slippage/borrow/total):", commission, slippage, borrow, total_costs)

    checks = []
    if turnover > 0 and trades_count == 0:
        checks.append("turnover > 0 with zero trades in log")
    if (trades_count > 0 or total_costs > 0) and equity_constant:
        checks.append("equity curve constant despite trades/costs")

    if equity_df.empty is False:
        initial = float(equity_df["equity"].iloc[0])
        final = float(equity_df["equity"].iloc[-1])
        realized = float(metrics.get("total_realized_pnl", 0.0) or 0.0)
        implied_unrealized = final - initial - realized + commission + borrow
        print("Equity change:", final - initial)
        print("Realized PnL (metrics):", realized)
        print("Implied unrealized (net of commission+borrow):", implied_unrealized)

    if checks:
        print("Integrity checks FAILED:")
        for check in checks:
            print("-", check)
        return 2

    print("Integrity checks: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
