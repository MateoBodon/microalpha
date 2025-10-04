"""Utility functions for computing portfolio performance metrics."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence

import numpy as np
import pandas as pd


def compute_metrics(
    equity_records: Sequence[Mapping[str, float | int]],
    turnover: float,
    periods: int = 252,
) -> Dict[str, Any]:
    if not equity_records:
        df = pd.DataFrame(columns=["timestamp", "equity", "exposure", "returns"])
        return {
            "equity_df": df,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "total_turnover": float(turnover),
            "traded_days": 0,
            "avg_exposure": 0.0,
            "final_equity": 0.0,
        }

    df = pd.DataFrame(equity_records).drop_duplicates("timestamp")
    df = df.sort_values("timestamp")
    df["returns"] = df["equity"].pct_change().fillna(0.0)

    returns = df["returns"]
    mean_return = returns.mean()
    std_return = returns.std(ddof=0)
    sharpe = 0.0
    if std_return > 0:
        sharpe = np.sqrt(periods) * (mean_return / std_return)

    downside = returns[returns < 0]
    downside_std = np.sqrt((downside**2).mean()) if not downside.empty else 0.0
    sortino = 0.0
    if downside_std > 0:
        sortino = (mean_return * periods) / (downside_std * np.sqrt(periods))

    equity_series = df["equity"]
    running_max = equity_series.cummax()
    drawdown = running_max - equity_series
    max_drawdown = ((drawdown / running_max).fillna(0.0)).max()

    traded_days = int(returns.ne(0).sum())
    avg_exposure = float(df["exposure"].mean()) if "exposure" in df else 0.0

    return {
        "equity_df": df,
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
        "max_drawdown": float(max_drawdown),
        "total_turnover": float(turnover),
        "traded_days": traded_days,
        "avg_exposure": avg_exposure,
        "final_equity": float(equity_series.iloc[-1]),
    }
