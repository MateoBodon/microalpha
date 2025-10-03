"""Generate simple equity, drawdown, and exposure plots."""

from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import pandas as pd


def build_tearsheet(equity_path: str) -> plt.Figure:
    df = pd.read_csv(equity_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

    equity = df.set_index("timestamp")["equity"]
    drawdown = equity / equity.cummax() - 1.0
    exposure = df.set_index("timestamp")["exposure"] if "exposure" in df else pd.Series(dtype=float)

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    axes[0].plot(equity.index, equity, label="Equity", color="#1f77b4")
    axes[0].set_ylabel("Equity")
    axes[0].legend(loc="upper left")

    axes[1].plot(drawdown.index, drawdown, color="#d62728")
    axes[1].fill_between(drawdown.index, drawdown, 0, color="#d62728", alpha=0.3)
    axes[1].set_ylabel("Drawdown")

    axes[2].plot(exposure.index, exposure, color="#9467bd")
    axes[2].set_ylabel("Exposure")
    axes[2].set_xlabel("Time")

    fig.tight_layout()
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a simple performance tearsheet")
    parser.add_argument("equity_csv", help="Path to equity_curve.csv")
    parser.add_argument("--output", help="Optional output path for saving the figure")
    args = parser.parse_args()

    fig = build_tearsheet(args.equity_csv)
    if args.output:
        fig.savefig(args.output, dpi=200, bbox_inches="tight")
    else:
        plt.show()


if __name__ == "__main__":
    main()
