"""Utility functions for computing portfolio performance metrics."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from .risk_stats import sharpe_stats


def compute_metrics(
    equity_records: Sequence[Mapping[str, float | int]],
    turnover: float,
    periods: int = 252,
    trades: Optional[List[Mapping[str, Any]]] = None,
    benchmark_equity: Optional[Sequence[Mapping[str, float | int]]] = None,
    rf: float = 0.0,
    hac_lags: int | None = None,
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

    resolved_hac = hac_lags
    if resolved_hac is None:
        hac_env = os.getenv("METRICS_HAC_LAGS")
        if hac_env:
            try:
                candidate = int(hac_env)
            except ValueError:
                candidate = None
            else:
                if candidate < 0:
                    candidate = None
            resolved_hac = candidate

    sharpe_summary = sharpe_stats(
        returns=returns,
        rf=rf,
        periods=periods,
        ddof=0,
        hac_lags=resolved_hac,
    )
    sharpe = float(sharpe_summary["sharpe"])
    sharpe_se = float(sharpe_summary["se"])
    sharpe_tstat = float(sharpe_summary["tstat"])
    sharpe_ci_low = float(sharpe_summary["ci_low"])
    sharpe_ci_high = float(sharpe_summary["ci_high"])

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
    avg_gross_exposure = (
        float(df["gross_exposure"].mean()) if "gross_exposure" in df else None
    )
    max_gross_exposure = (
        float(df["gross_exposure"].max()) if "gross_exposure" in df else None
    )
    max_net_exposure = (
        float(df["exposure"].abs().max()) if "exposure" in df else None
    )

    # Annualized volatility and CAGR
    ann_vol = float(returns.std(ddof=0) * (periods**0.5)) if len(returns) > 1 else 0.0
    if len(equity_series) > 1:
        total_return = float(equity_series.iloc[-1] / equity_series.iloc[0] - 1.0)
        years = max(float(len(df)) / periods, 1e-9)
        base = 1.0 + total_return
        if base <= 0.0:
            cagr = -1.0
        else:
            cagr = float(base ** (1.0 / years) - 1.0)
    else:
        cagr = 0.0

    # Max drawdown duration in periods
    dd_boolean = (equity_series / running_max) < 1.0
    max_dd_duration = int(
        dd_boolean.astype(int)
        .groupby((dd_boolean != dd_boolean.shift()).cumsum())
        .transform("sum")
        .max()
        or 0
    )

    # Trade stats (if provided)
    num_trades = 0
    avg_trade_notional = 0.0
    win_rate = 0.0
    total_realized_pnl = 0.0
    if trades:
        import pandas as _pd

        tdf = _pd.DataFrame(trades)
        num_trades = int(len(tdf))
        if num_trades:
            avg_trade_notional = float((tdf["qty"].abs() * tdf["price"].abs()).mean())
        # Realized PnL attribution if present
        if "realized_pnl" in tdf:
            total_realized_pnl = float(tdf["realized_pnl"].sum())
            wins = (tdf["realized_pnl"] > 0).sum()
            losses = (tdf["realized_pnl"] < 0).sum()
            denom = max(wins + losses, 1)
            win_rate = float(wins / denom)

    # Benchmark-relative metrics if provided
    alpha = beta = information_ratio = 0.0
    if benchmark_equity:
        bdf = (
            pd.DataFrame(benchmark_equity)
            .drop_duplicates("timestamp")
            .sort_values("timestamp")
        )
        bdf["returns"] = bdf["equity"].pct_change().fillna(0.0)
        br = bdf["returns"].reindex(df.index, fill_value=0.0).astype(float)
        returns_np = returns.astype(float).to_numpy()
        br_np = br.astype(float).to_numpy()
        if br.std(ddof=0) > 0:
            cov = float(np.cov(returns_np, br_np, ddof=0)[0, 1])
            var_br = float(np.var(br_np, ddof=0))
            beta = cov / var_br if var_br != 0.0 else 0.0
            br_mean = float(np.mean(br_np))
            alpha = float(returns.mean() * periods - beta * br_mean * periods)
            diff = returns - br
            std_diff = float(diff.std(ddof=0))
            information_ratio = (
                float((diff.mean() * periods) / std_diff) if std_diff > 0 else 0.0
            )

    return {
        "equity_df": df,
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
        "max_drawdown": float(max_drawdown),
        "max_drawdown_duration": max_dd_duration,
        "cagr": cagr,
        "calmar_ratio": float(cagr / max_drawdown) if max_drawdown > 0 else 0.0,
        "alpha": float(alpha),
        "beta": float(beta),
        "information_ratio": float(information_ratio),
        "ann_vol": float(ann_vol),
        "avg_exposure": avg_exposure,
        "avg_gross_exposure": avg_gross_exposure,
        "max_gross_exposure": max_gross_exposure,
        "max_net_exposure": max_net_exposure,
        "exposure_std": float(df["exposure"].std(ddof=0)) if "exposure" in df else 0.0,
        "gross_exposure_std": (
            float(df["gross_exposure"].std(ddof=0))
            if "gross_exposure" in df
            else None
        ),
        "total_turnover": float(turnover),
        "turnover_per_day": float(turnover / max(len(df), 1)),
        "traded_days": traded_days,
        "num_trades": num_trades,
        "avg_trade_notional": float(avg_trade_notional),
        "win_rate": float(win_rate),
        "total_realized_pnl": float(total_realized_pnl),
        "final_equity": float(equity_series.iloc[-1]),
        "sharpe_ratio_se": sharpe_se,
        "sharpe_ratio_tstat": sharpe_tstat,
        "sharpe_ratio_ci_low": sharpe_ci_low,
        "sharpe_ratio_ci_high": sharpe_ci_high,
        "sharpe_hac_lags": float(resolved_hac or 0),
    }
