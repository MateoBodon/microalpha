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

    # Figure with subplots: equity + rolling Sharpe + PnL hist (if available)
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=3, cols=1, shared_xaxes=False, specs=[[{"secondary_y": True}], [{}], [{}]],
                        row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.06)
    fig.add_trace(
        go.Scatter(x=eq_ts, y=eq["equity"], mode="lines", name="Equity", line=dict(color="#1f77b4")),
        row=1, col=1, secondary_y=False
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
                ), row=1, col=1, secondary_y=True
            )
            fig.add_trace(
                go.Scatter(
                    x=tts[sell_mask],
                    y=trades.loc[sell_mask, "price"],
                    mode="markers",
                    name="Sells",
                    marker=dict(symbol="triangle-down", color="#d62728"),
                ), row=1, col=1, secondary_y=True
            )

            # Rolling Sharpe on equity returns
            if len(eq) > 2:
                ret = pd.Series(eq["equity"]).pct_change().fillna(0.0)
                window = min(63, max(2, len(ret)//5))
                rolling_mean = ret.rolling(window).mean()
                rolling_std = ret.rolling(window).std(ddof=0)
                sharpe = (rolling_mean / (rolling_std.replace(0, pd.NA))).fillna(0.0) * (252 ** 0.5)
                fig.add_trace(go.Scatter(x=eq_ts, y=sharpe, mode="lines", name="Rolling Sharpe (63d)", line=dict(color="#9467bd")),
                              row=2, col=1)

            # Per-trade realized PnL histogram
            if "realized_pnl" in trades:
                fig.add_trace(go.Histogram(x=trades["realized_pnl"], name="Trade PnL", marker_color="#8c564b"),
                              row=3, col=1)

    fig.update_layout(title="Microalpha Report", legend=dict(orientation="h"), template="plotly_white")
    fig.update_yaxes(title_text="Equity", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Price", row=1, col=1, secondary_y=True)
    fig.update_xaxes(title_text="Time", row=1, col=1)
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_xaxes(title_text="Trade PnL", row=3, col=1)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out), include_plotlyjs="cdn")
    print(f"Saved report to {out}")


if __name__ == "__main__":
    main()
