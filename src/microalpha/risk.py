# microalpha/risk.py
from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
import pandas as pd

from .risk_stats import block_bootstrap, sharpe_stats


def create_sharpe_ratio(
    returns,
    periods: int = 252,
    *,
    rf: float = 0.0,
    ddof: int = 0,
    hac_lags: Optional[int] = None,
):
    """
    Calculates the annualized Sharpe ratio of a returns stream.
    `returns` is a pandas Series.
    `periods` is the number of periods per year (252 for daily).
    """
    stats = sharpe_stats(
        returns=pd.Series(returns),
        rf=rf,
        periods=periods,
        ddof=ddof,
        hac_lags=hac_lags,
    )
    return float(stats["sharpe"])


def create_drawdowns(equity_curve):
    """
    Calculates the maximum drawdown and the drawdown series.
    `equity_curve` is a pandas Series representing portfolio value over time.
    """
    # Calculate the running maximum
    high_water_mark = equity_curve.cummax()
    # Calculate the drawdown series
    drawdown = high_water_mark - equity_curve
    drawdown_percentage = drawdown / high_water_mark
    max_drawdown = drawdown_percentage.max()
    return drawdown_percentage, max_drawdown


def bootstrap_sharpe_ratio(
    returns,
    num_simulations: int = 5000,
    periods: int = 252,
    *,
    rf: float = 0.0,
    ddof: int = 0,
    hac_lags: Optional[int] = None,
    method: str = "stationary",
    block_len: Optional[int] = None,
    rng: Optional[np.random.Generator] = None,
):
    """
    Performs a bootstrap analysis on a returns stream to determine the
    statistical significance of its Sharpe ratio.
    """
    series = pd.Series(returns).dropna().astype(float)
    if series.std(ddof=ddof) == 0 or len(series) < 3:  # Not enough data
        return {"sharpe_dist": [0.0], "p_value": 1.0, "confidence_interval": (0.0, 0.0)}

    method_lower = method.lower()
    rng = rng or np.random.default_rng()
    if method_lower == "iid":
        warnings.warn(
            "IID bootstrap is deprecated. Use block_bootstrap with stationary "
            "or circular blocks for serial dependence.",
            DeprecationWarning,
            stacklevel=2,
        )
        samples = (
            rng.choice(series.to_numpy(), size=len(series), replace=True)
            for _ in range(num_simulations)
        )
    else:
        samples = block_bootstrap(
            series.to_numpy(),
            B=num_simulations,
            method=method_lower,  # type: ignore[arg-type]
            block_len=block_len,
            rng=rng,
        )

    sharpe_dist = []
    for sample in samples:
        stats = sharpe_stats(
            returns=pd.Series(sample),
            rf=rf,
            periods=periods,
            ddof=ddof,
            hac_lags=hac_lags,
        )
        sharpe_dist.append(float(stats["sharpe"]))
    if not sharpe_dist:
        return {"sharpe_dist": [0.0], "p_value": 1.0, "confidence_interval": (0.0, 0.0)}

    sharpe_arr = np.asarray(sharpe_dist, dtype=float)
    p_value = float(np.mean(sharpe_arr <= 0.0))
    confidence_interval = (
        float(np.percentile(sharpe_arr, 2.5)),
        float(np.percentile(sharpe_arr, 97.5)),
    )

    return {
        "sharpe_dist": sharpe_dist,
        "p_value": p_value,
        "confidence_interval": confidence_interval,
    }
