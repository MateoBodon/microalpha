"""Generate simple equity, drawdown, and exposure plots."""

from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import pandas as pd


def build_tearsheet(
    equity_path: str, benchmark_path: str | None = None, metrics_path: str | None = None
) -> plt.Figure:
    df = pd.read_csv(equity_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

    equity = df.set_index("timestamp")["equity"]
    drawdown = equity / equity.cummax() - 1.0
    exposure = df.set_index("timestamp")["exposure"] if "exposure" in df else pd.Series(dtype=float)

    bench = None
    if benchmark_path:
        try:
            bench = pd.read_csv(benchmark_path)
            if "timestamp" in bench.columns:
                bench["timestamp"] = pd.to_datetime(bench["timestamp"], errors="coerce")
                bench = bench.dropna(subset=["timestamp"]).sort_values("timestamp")
                bench = bench.set_index("timestamp").reindex(equity.index).ffill()
        except Exception:
            bench = None

    fig, axes = plt.subplots(4, 1, figsize=(11, 11), sharex=True)

    axes[0].plot(equity.index, equity, label="Equity", color="#1f77b4")
    if bench is not None:
        if "close" in bench.columns:
            axes[0].plot(bench.index, bench["close"] * (equity.iloc[0] / bench["close"].iloc[0]), label="Benchmark", color="#2ca02c", alpha=0.8)
    axes[0].set_ylabel("Equity")
    axes[0].legend(loc="upper left")

    axes[1].plot(drawdown.index, drawdown, color="#d62728")
    axes[1].fill_between(drawdown.index, drawdown, 0, color="#d62728", alpha=0.3)
    axes[1].set_ylabel("Drawdown")

    axes[2].plot(exposure.index, exposure, color="#9467bd", label="Net Exposure")
    if "gross_exposure" in df.columns:
        axes[2].plot(df.set_index("timestamp").index, df.set_index("timestamp")["gross_exposure"], color="#bcbd22", alpha=0.7, label="Gross Exposure")
    axes[2].set_ylabel("Exposure")
    if "num_positions" in df.columns:
        axes[2].twinx().plot(df.set_index("timestamp").index, df.set_index("timestamp")["num_positions"], color="#17becf", alpha=0.5, label="Num Positions")
    axes[2].legend(loc="upper left")

    # Rolling Sharpe (252-day window)
    returns = equity.pct_change().fillna(0.0)
    rolling_mean = returns.rolling(window=252, min_periods=30).mean()
    rolling_std = returns.rolling(window=252, min_periods=30).std(ddof=0)
    rolling_sharpe = (rolling_mean / rolling_std) * (252 ** 0.5)
    axes[3].plot(rolling_sharpe.index, rolling_sharpe, color="#8c564b")
    axes[3].set_ylabel("Rolling Sharpe (252d)")
    axes[3].set_xlabel("Time")

    # Optional top-line metrics as a title/footer
    if metrics_path:
        try:
            import json

            payload = json.loads(open(metrics_path, "r", encoding="utf-8").read())
            top = {
                "Sharpe": payload.get("sharpe_ratio"),
                "Sortino": payload.get("sortino_ratio"),
                "Calmar": payload.get("calmar_ratio"),
                "MaxDD": payload.get("max_drawdown"),
                "Alpha": payload.get("alpha"),
                "Beta": payload.get("beta"),
                "IR": payload.get("information_ratio"),
                "Turn/day": payload.get("turnover_per_day"),
            }
            subtitle = "  |  ".join(
                f"{k}: {v:.3f}" for k, v in top.items() if isinstance(v, (int, float))
            )
            fig.suptitle(subtitle, fontsize=10, y=0.98)
        except Exception:
            pass

    fig.tight_layout()
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a simple performance tearsheet")
    parser.add_argument("equity_csv", help="Path to equity_curve.csv")
    parser.add_argument("--benchmark", help="Optional benchmark CSV with timestamp,close")
    parser.add_argument("--metrics", help="Optional metrics.json for summary")
    parser.add_argument("--output", help="Optional output path for saving the figure")
    args = parser.parse_args()

    fig = build_tearsheet(args.equity_csv, args.benchmark, args.metrics)
    if args.output:
        fig.savefig(args.output, dpi=200, bbox_inches="tight")
    else:
        plt.show()


if __name__ == "__main__":
    main()
