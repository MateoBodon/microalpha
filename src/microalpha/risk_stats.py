"""Statistical helpers for risk analytics."""

from __future__ import annotations

from math import sqrt
from typing import Dict, Generator, Iterable, Literal, Optional

import numpy as np
import pandas as pd

__all__ = ["sharpe_stats", "block_bootstrap"]


def _as_series(returns: Iterable[float]) -> pd.Series:
    if isinstance(returns, pd.Series):
        series = returns
    else:
        series = pd.Series(returns)
    return series.dropna().astype(float)


def _newey_west_lrv(values: np.ndarray, max_lag: int) -> float:
    """Estimate the long-run variance using Newey-West weights."""
    n = values.shape[0]
    if n == 0:
        return 0.0
    mean = float(values.mean())
    demeaned = values - mean
    gamma0 = float(np.dot(demeaned, demeaned) / n)
    if max_lag <= 0:
        return gamma0
    max_lag = int(min(max_lag, n - 1))
    if max_lag <= 0:
        return gamma0
    lrv = gamma0
    for lag in range(1, max_lag + 1):
        weight = 1.0 - lag / (max_lag + 1.0)
        cov = float(np.dot(demeaned[lag:], demeaned[:-lag]) / n)
        lrv += 2.0 * weight * cov
    return lrv


def sharpe_stats(
    returns: pd.Series,
    rf: float = 0.0,
    periods: int = 252,
    ddof: int = 0,
    hac_lags: Optional[int] = None,
) -> Dict[str, float]:
    """Compute Sharpe ratio statistics with optional HAC standard errors."""
    series = _as_series(returns)
    n = len(series)
    if n == 0:
        return {"sharpe": 0.0, "se": 0.0, "tstat": 0.0, "ci_low": 0.0, "ci_high": 0.0}

    rf_per_period = rf / periods
    excess = series.astype(float) - rf_per_period
    n = len(excess)
    if n < 2:
        return {"sharpe": 0.0, "se": 0.0, "tstat": 0.0, "ci_low": 0.0, "ci_high": 0.0}

    mean = float(excess.mean())
    std = float(excess.std(ddof=ddof))
    if std == 0.0:
        return {"sharpe": 0.0, "se": 0.0, "tstat": 0.0, "ci_low": 0.0, "ci_high": 0.0}

    sharpe = sqrt(periods) * mean / std

    if hac_lags is None:
        var_mean = float(excess.var(ddof=ddof)) / n
    else:
        lrv = _newey_west_lrv(excess.to_numpy(), max_lag=int(hac_lags))
        var_mean = lrv / n

    se_mean = sqrt(var_mean) if var_mean > 0.0 else 0.0
    se_sharpe = sqrt(periods) * se_mean / std if se_mean > 0.0 else 0.0
    if se_sharpe > 0.0:
        tstat = sharpe / se_sharpe
        ci_low = sharpe - 1.96 * se_sharpe
        ci_high = sharpe + 1.96 * se_sharpe
    else:
        tstat = 0.0
        ci_low = sharpe
        ci_high = sharpe

    return {
        "sharpe": float(sharpe),
        "se": float(se_sharpe),
        "tstat": float(tstat),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
    }


def _default_block_len(n: int) -> int:
    return max(1, int(round(n ** (1.0 / 3.0))))


def block_bootstrap(
    returns: np.ndarray,
    B: int = 5000,
    method: Literal["stationary", "circular"] = "stationary",
    block_len: Optional[int] = None,
    rng: Optional[np.random.Generator] = None,
) -> Generator[np.ndarray, None, None]:
    """Yield bootstrap samples that preserve serial dependence via block resampling."""
    arr = np.asarray(returns, dtype=float)
    if arr.ndim != 1:
        raise ValueError("returns must be a one-dimensional array")
    n = arr.shape[0]
    if n == 0:
        raise ValueError("returns array cannot be empty")

    if rng is None:
        rng = np.random.default_rng()

    if block_len is None:
        block_len = _default_block_len(n)
    block_len = int(block_len)
    if block_len <= 0:
        raise ValueError("block_len must be positive")

    method = method.lower()
    if method not in {"stationary", "circular"}:
        raise ValueError("method must be 'stationary' or 'circular'")

    def stationary_bootstrap() -> Generator[np.ndarray, None, None]:
        p = 1.0 / block_len
        for _ in range(B):
            sample = np.empty(n, dtype=float)
            idx = rng.integers(0, n)
            for t in range(n):
                if t == 0 or rng.random() < p:
                    idx = rng.integers(0, n)
                else:
                    idx = (idx + 1) % n
                sample[t] = arr[idx]
            yield sample

    def circular_bootstrap() -> Generator[np.ndarray, None, None]:
        for _ in range(B):
            sample = np.empty(n, dtype=float)
            pos = 0
            while pos < n:
                start = rng.integers(0, n)
                block = min(block_len, n - pos)
                indices = (np.arange(start, start + block) % n).astype(int)
                sample[pos : pos + block] = arr[indices]
                pos += block
            yield sample

    if method == "stationary":
        yield from stationary_bootstrap()
    else:
        yield from circular_bootstrap()
