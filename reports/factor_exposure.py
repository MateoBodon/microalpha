#!/usr/bin/env python3
"""Compute rolling factor exposures for a strategy equity curve.

Example
-------
    python reports/factor_exposure.py \
        --equity artifacts/run-123/equity_curve.csv \
        --factors data/factors/fama_french.csv \
        --window 63 \
        --output artifacts/run-123/factor_exposures.png

The factor CSV must contain a ``date`` column (daily timestamps) and one or
more factor return columns expressed in decimal form (e.g. 0.01 = 1%).  The
equity curve is converted to daily returns and aligned to the factor index
before running ordinary least squares in a rolling window.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _load_equity(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    if "timestamp" in df.columns:
        index = pd.to_datetime(df["timestamp"])
    elif "date" in df.columns:
        index = pd.to_datetime(df["date"])
    else:
        index = pd.RangeIndex(len(df))
    equity = pd.Series(df["equity"].astype(float).values, index=index).sort_index()
    returns = equity.pct_change().dropna()
    return returns


def _load_factors(path: Path) -> pd.DataFrame:
    factors = pd.read_csv(path)
    if "date" not in factors.columns:
        raise ValueError("Factor CSV must contain a 'date' column.")
    factors["date"] = pd.to_datetime(factors["date"])
    factors = factors.set_index("date").sort_index()
    return factors.astype(float)


def _rolling_ols(
    y: pd.Series, X: pd.DataFrame, window: int
) -> Tuple[pd.DataFrame, pd.Series]:
    aligned_y, aligned_X = y.align(X, join="inner")
    aligned_X = aligned_X.reindex(aligned_y.index).dropna()
    aligned_y = aligned_y.reindex(aligned_X.index).dropna()

    if len(aligned_y) < window:
        raise ValueError("Not enough overlapping observations for requested window.")

    exposures: Dict[str, list[float]] = {col: [] for col in aligned_X.columns}
    intercept: list[float] = []
    index: list[pd.Timestamp] = []

    matrix = aligned_X.to_numpy()
    target = aligned_y.to_numpy()
    factors = aligned_X.columns.tolist()

    for start in range(0, len(aligned_y) - window + 1):
        end = start + window
        X_win = matrix[start:end]
        y_win = target[start:end]
        X_design = np.column_stack([np.ones(window), X_win])
        beta, *_ = np.linalg.lstsq(X_design, y_win, rcond=None)
        intercept.append(float(beta[0]))
        for idx, factor in enumerate(factors, start=1):
            exposures[factor].append(float(beta[idx]))
        index.append(aligned_y.index[end - 1])

    exposures_df = pd.DataFrame(exposures, index=index)
    intercept_series = pd.Series(intercept, index=index, name="alpha")
    return exposures_df, intercept_series


def _plot_exposures(
    exposures: pd.DataFrame, alpha: pd.Series, output: Path, title: str
) -> None:
    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax = plt.subplots(figsize=(12, 6))
    for column in exposures.columns:
        ax.plot(exposures.index, exposures[column], label=column)
    ax.set_title(title)
    ax.set_ylabel("Exposure")
    ax.legend(loc="upper right")

    ax2 = ax.twinx()
    ax2.plot(alpha.index, alpha.values, color="black", linestyle="--", label="alpha")
    ax2.set_ylabel("Alpha")
    ax2.legend(loc="lower right")

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute rolling factor exposures for an equity curve."
    )
    parser.add_argument("--equity", required=True, help="Path to equity_curve.csv")
    parser.add_argument("--factors", required=True, help="CSV of factor returns")
    parser.add_argument(
        "--window", type=int, default=63, help="Rolling window length (default: 63)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output PNG (and exposures CSV alongside)",
    )
    parser.add_argument(
        "--label", default="Rolling Factor Exposures", help="Plot title label"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    equity_path = Path(args.equity)
    factors_path = Path(args.factors)
    output_path = Path(args.output)

    returns = _load_equity(equity_path)
    factors = _load_factors(factors_path)
    exposures_df, alpha_series = _rolling_ols(returns, factors, args.window)

    csv_path = output_path.with_suffix(".csv")
    exposures_df.assign(alpha=alpha_series).to_csv(csv_path, index_label="date")
    _plot_exposures(exposures_df, alpha_series, output_path, args.label)
    print(f"Wrote exposures to {csv_path}")
    print(f"Saved plot to {output_path}")


if __name__ == "__main__":
    main()
