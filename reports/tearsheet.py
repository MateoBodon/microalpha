#!/usr/bin/env python3
"""Minimal PNG tearsheet generator for a single run.

Reads an equity curve CSV and writes a simple 2-panel plot with equity and drawdown.

Usage:
    python reports/tearsheet.py artifacts/<run-id>/equity_curve.csv --output out.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _compute_drawdown(equity: pd.Series) -> pd.Series:
    running_max = equity.cummax()
    dd = (equity / running_max) - 1.0
    return dd.fillna(0.0)


def main() -> None:
    ap = argparse.ArgumentParser(description="Render a quick PNG tearsheet")
    ap.add_argument("equity_csv", help="Path to equity_curve.csv")
    ap.add_argument("--output", required=True, help="Output PNG file path")
    args = ap.parse_args()

    df = pd.read_csv(args.equity_csv)
    if "equity" not in df:
        raise SystemExit("equity_curve.csv missing 'equity' column")

    ts = pd.to_datetime(df["timestamp"]) if "timestamp" in df else pd.RangeIndex(len(df))
    equity = pd.Series(df["equity"].values, index=ts)
    dd = _compute_drawdown(equity)

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True, gridspec_kw={"hspace": 0.1})
    axes[0].plot(equity.index, equity.values, color="tab:blue")
    axes[0].set_ylabel("Equity")
    axes[0].grid(True, alpha=0.3, linestyle=":")

    axes[1].fill_between(dd.index, dd.values, 0.0, color="tab:red", alpha=0.3)
    axes[1].set_ylabel("Drawdown")
    axes[1].set_xlabel("Time")
    axes[1].grid(True, alpha=0.3, linestyle=":")

    fig.tight_layout()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    print(f"Saved tearsheet to {out}")


if __name__ == "__main__":
    main()

