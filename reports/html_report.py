#!/usr/bin/env python3
"""Minimal interactive HTML report for a run.

Displays an equity curve and optional trade markers using Plotly.

Usage:
    python reports/html_report.py artifacts/<run-id>/equity_curve.csv \
        --trades artifacts/<run-id>/trades.jsonl --output report.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def read_trades_jsonl(path: str | None) -> pd.DataFrame:
    if not path:
        return pd.DataFrame()
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            import json

            records.append(json.loads(line))
    return pd.DataFrame.from_records(records)


def main() -> None:
    ap = argparse.ArgumentParser(description="Render an interactive HTML report")
    ap.add_argument("equity_csv", help="Path to equity_curve.csv")
    ap.add_argument("--trades", default=None, help="Path to trades.jsonl (optional)")
    ap.add_argument("--output", required=True, help="Output HTML file path")
    args = ap.parse_args()

    eq = pd.read_csv(args.equity_csv)
    eq_ts = pd.to_datetime(eq["timestamp"]) if "timestamp" in eq else pd.RangeIndex(len(eq))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=eq_ts, y=eq["equity"], mode="lines", name="Equity", line=dict(color="#1f77b4"))
    )

    trades = read_trades_jsonl(args.trades)
    if not trades.empty:
        tts = pd.to_datetime(trades["timestamp"]) if "timestamp" in trades else None
        if tts is not None:
            buy_mask = trades["side"].eq("BUY")
            sell_mask = trades["side"].eq("SELL")
            fig.add_trace(
                go.Scatter(
                    x=tts[buy_mask],
                    y=trades.loc[buy_mask, "price"],
                    mode="markers",
                    name="Buys",
                    marker=dict(symbol="triangle-up", color="#2ca02c"),
                    yaxis="y2",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=tts[sell_mask],
                    y=trades.loc[sell_mask, "price"],
                    mode="markers",
                    name="Sells",
                    marker=dict(symbol="triangle-down", color="#d62728"),
                    yaxis="y2",
                )
            )

    fig.update_layout(
        title="Microalpha Report",
        xaxis=dict(title="Time"),
        yaxis=dict(title="Equity", side="left"),
        yaxis2=dict(title="Price", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h"),
        template="plotly_white",
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out), include_plotlyjs="cdn")
    print(f"Saved report to {out}")


if __name__ == "__main__":
    main()

