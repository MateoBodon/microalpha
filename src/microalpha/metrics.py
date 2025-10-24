"""Utility functions for computing portfolio performance metrics."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence, Iterable, Optional

import numpy as np
import pandas as pd


def compute_metrics(
    equity_records: Sequence[Mapping[str, float | int]],
    turnover: float,
    periods: int = 252,
    *,
    benchmark: Optional[Iterable[float]] = None,
    trades: Optional[Sequence[Mapping[str, Any]]] = None,
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
    dd_ratio = (drawdown / running_max).fillna(0.0)
    max_drawdown = dd_ratio.max()

    # Longest drawdown duration (consecutive observations under previous high)
    in_dd = dd_ratio > 0
    # Compute max run length of True
    max_drawdown_duration = 0
    current = 0
    for flag in in_dd.to_numpy():
        if flag:
            current += 1
            if current > max_drawdown_duration:
                max_drawdown_duration = current
        else:
            current = 0

    # CAGR and Calmar ratio
    cagr = 0.0
    if len(equity_series) > 1 and equity_series.iloc[0] > 0:
        total_return = float(equity_series.iloc[-1] / equity_series.iloc[0])
        years = len(equity_series) / periods
        if years > 0:
            cagr = float(total_return ** (1.0 / years) - 1.0)
    calmar = float(cagr / max_drawdown) if max_drawdown > 0 else 0.0

    traded_days = int(returns.ne(0).sum())
    avg_exposure = float(df["exposure"].mean()) if "exposure" in df else 0.0
    exposure_std = (
        float(df["exposure"].std(ddof=0)) if "exposure" in df else 0.0
    )

    # Rolling benchmark alignment (optional)
    alpha = 0.0
    beta = 0.0
    info_ratio = 0.0
    if benchmark is not None:
        bench = pd.Series(list(benchmark))
        if len(bench) == len(df):
            bench_returns = bench.pct_change().fillna(0.0)
            br = bench_returns.to_numpy()
            rr = returns.to_numpy()
            var_b = float(np.var(br))
            if var_b > 0.0:
                cov_rb = float(np.cov(rr, br, ddof=0)[0, 1])
                beta = cov_rb / var_b
                # Annualised alpha (mean excess over beta * benchmark)
                alpha = float((rr.mean() - beta * br.mean()) * periods)
            # Information ratio
            diff = rr - br
            diff_std = float(np.std(diff, ddof=0))
            if diff_std > 0:
                info_ratio = float(np.sqrt(periods) * (diff.mean() / diff_std))

    # Distributional stats on returns
    skewness = float(returns.skew()) if len(returns) > 0 else 0.0
    kurtosis = float(returns.kurt()) if len(returns) > 0 else 0.0
    win_rate = float((returns > 0).mean()) if len(returns) > 0 else 0.0

    # Turnover per day
    obs = int(len(df)) if len(df) else 1
    turnover_per_day = float(turnover) / float(obs)

    # Trade statistics (optional)
    num_trades = 0
    avg_trade_notional = 0.0
    if trades:
        notionals = []
        for t in trades:
            try:
                notionals.append(abs(float(t.get("qty", 0.0)) * float(t.get("price", 0.0))))
            except Exception:
                continue
        num_trades = len(notionals)
        if notionals:
            avg_trade_notional = float(np.mean(notionals))

    return {
        "equity_df": df,
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
        "max_drawdown": float(max_drawdown),
        "max_drawdown_duration": int(max_drawdown_duration),
        "cagr": float(cagr),
        "calmar_ratio": float(calmar),
        "alpha": float(alpha),
        "beta": float(beta),
        "information_ratio": float(info_ratio),
        "skewness": float(skewness),
        "kurtosis": float(kurtosis),
        "win_rate": float(win_rate),
        "turnover_per_day": float(turnover_per_day),
        "avg_exposure": avg_exposure,
        "exposure_std": exposure_std,
        "total_turnover": float(turnover),
        "traded_days": traded_days,
        "num_trades": int(num_trades),
        "avg_trade_notional": float(avg_trade_notional),
        "final_equity": float(equity_series.iloc[-1]),
    }
