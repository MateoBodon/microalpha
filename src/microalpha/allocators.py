"""Portfolio allocators using covariance information."""

from __future__ import annotations

from typing import Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

__all__ = ["risk_parity", "lw_min_var", "budgeted_allocator"]


def risk_parity(
    cov: pd.DataFrame | np.ndarray,
    *,
    tol: float = 1e-8,
    max_iter: int = 10_000,
    ridge: float = 1e-8,
    initial: Sequence[float] | None = None,
) -> pd.Series:
    """Compute long-only risk parity weights for a covariance matrix."""

    cov_df = _as_dataframe(cov)
    n = cov_df.shape[0]
    if n == 0:
        return pd.Series(dtype=float)

    cov_mat = cov_df.to_numpy(copy=True).astype(float)
    if ridge > 0:
        cov_mat += np.eye(n) * ridge

    if initial is None:
        weights = np.full(n, 1.0 / n)
    else:
        weights = np.asarray(initial, dtype=float)
        if weights.shape[0] != n:
            raise ValueError("Initial weights length mismatch with covariance.")
        weights = np.clip(weights, 1e-12, None)
        weights /= weights.sum()

    for _ in range(max(1, max_iter)):
        marginal = cov_mat @ weights
        risk_contrib = weights * marginal
        avg = risk_contrib.mean()
        if np.max(np.abs(risk_contrib - avg)) < tol:
            break
        adjustment = avg / np.clip(risk_contrib, 1e-12, None)
        weights = np.clip(weights * adjustment, 1e-12, None)
        weights /= weights.sum()

    return pd.Series(weights, index=cov_df.index, name="weight")


def lw_min_var(
    returns: pd.DataFrame | np.ndarray,
    *,
    allow_short: bool = False,
    epsilon: float = 1e-6,
    return_cov: bool = False,
) -> pd.Series | Tuple[pd.Series, pd.DataFrame]:
    """Ledoit–Wolf shrinkage min-variance allocator."""

    returns_df = _as_dataframe(returns, columns_first=True)
    if returns_df.empty:
        weights = pd.Series(dtype=float)
        return (weights, returns_df) if return_cov else weights

    cov_shrink = _ledoit_wolf_cov(returns_df.to_numpy(dtype=float))
    cov_df = pd.DataFrame(cov_shrink, index=returns_df.columns, columns=returns_df.columns)
    weights = _min_var_weights(cov_df.to_numpy(), allow_short=allow_short, epsilon=epsilon)
    weights_series = pd.Series(weights, index=cov_df.index, name="weight")

    if return_cov:
        return weights_series, cov_df
    return weights_series


def budgeted_allocator(
    signals: Mapping[str, float] | pd.Series,
    cov: pd.DataFrame | np.ndarray,
    *,
    total_budget: float = 1.0,
    ridge: float = 1e-8,
    risk_model: str = "risk_parity",
    returns: pd.DataFrame | None = None,
    allow_short: bool = False,
) -> pd.Series:
    """Allocate capital across long/short sleeves using risk parity within each bucket."""

    signal_series = _as_series(signals)
    cov_df = _as_dataframe(cov)
    signal_series = signal_series.reindex(cov_df.index).fillna(0.0)

    long_signals = signal_series[signal_series > 0.0]
    short_signals = signal_series[signal_series < 0.0]
    total_signal = float(long_signals.sum() - short_signals.sum())
    if total_signal <= 0:
        total_signal = float(long_signals.abs().sum() + short_signals.abs().sum())
    total_signal = max(total_signal, 1e-12)

    long_budget = total_budget * float(long_signals.sum()) / total_signal if not long_signals.empty else 0.0
    short_budget = total_budget * float(short_signals.abs().sum()) / total_signal if not short_signals.empty else 0.0

    weights = pd.Series(0.0, index=cov_df.index, name="weight")

    if not long_signals.empty:
        cov_long = cov_df.loc[long_signals.index, long_signals.index]
        rp_long = _bucket_weights(
            cov_long,
            ridge=ridge,
            risk_model=risk_model,
            returns=None if returns is None else returns[long_signals.index],
            allow_short=allow_short,
        )
        weights.loc[rp_long.index] = rp_long * long_budget

    if not short_signals.empty:
        cov_short = cov_df.loc[short_signals.index, short_signals.index]
        rp_short = _bucket_weights(
            cov_short,
            ridge=ridge,
            risk_model=risk_model,
            returns=None if returns is None else returns[short_signals.index],
            allow_short=allow_short,
        )
        weights.loc[rp_short.index] = -rp_short * short_budget

    return weights


# ---------------------------------------------------------------------------
# Helpers

def _as_dataframe(
    data: pd.DataFrame | np.ndarray | Mapping[str, Mapping[str, float]],
    *,
    columns_first: bool = False,
) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data.astype(float)
    if isinstance(data, np.ndarray):
        arr = np.asarray(data, dtype=float)
        if arr.ndim != 2:
            raise ValueError("Covariance/returns array must be 2-dimensional.")
        index = pd.RangeIndex(arr.shape[0])
        if columns_first and arr.shape[0] < arr.shape[1]:
            arr = arr.T
            index = pd.RangeIndex(arr.shape[0])
        return pd.DataFrame(arr, index=index)
    # Mapping of mappings
    frame = pd.DataFrame(data).astype(float)
    return frame


def _as_series(data: Mapping[str, float] | pd.Series) -> pd.Series:
    if isinstance(data, pd.Series):
        return data.astype(float)
    return pd.Series(data, dtype=float)


def _ledoit_wolf_cov(returns: np.ndarray) -> np.ndarray:
    if returns.ndim != 2:
        raise ValueError("Returns array must be 2-dimensional.")
    t, n = returns.shape
    if t < 2:
        raise ValueError("At least two observations required for covariance.")

    X = returns - returns.mean(axis=0, keepdims=True)
    sample = (X.T @ X) / (t - 1)
    mu = np.trace(sample) / n
    prior = mu * np.eye(n)

    # Compute estimator components
    X2 = X**2
    phi_mat = (X2.T @ X2) / (t - 1) - sample**2
    phi = phi_mat.sum()
    gamma = np.linalg.norm(sample - prior, ord="fro") ** 2
    kappa = phi / gamma if gamma > 0 else 0.0
    shrinkage = max(0.0, min(1.0, kappa / t))

    cov = shrinkage * prior + (1.0 - shrinkage) * sample
    return cov


def _min_var_weights(
    cov: np.ndarray,
    *,
    allow_short: bool,
    epsilon: float,
) -> np.ndarray:
    n = cov.shape[0]
    cov_reg = cov + np.eye(n) * epsilon
    inv_cov = np.linalg.pinv(cov_reg)
    ones = np.ones(n)
    raw = inv_cov @ ones
    denom = float(ones @ raw)
    if abs(denom) < 1e-12:
        weights = np.full(n, 1.0 / n)
    else:
        weights = raw / denom

    if not allow_short:
        weights = np.clip(weights, 0.0, None)
        s = weights.sum()
        if s <= 0:
            weights = np.full(n, 1.0 / n)
        else:
            weights /= s
    return weights


def _bucket_weights(
    cov: pd.DataFrame,
    *,
    ridge: float,
    risk_model: str,
    returns: pd.DataFrame | None,
    allow_short: bool,
) -> pd.Series:
    method = risk_model.lower()
    if method in {"risk_parity", "rp", "budgeted_rp"}:
        return risk_parity(cov, ridge=ridge)
    if method in {"lw_min_var", "ledoit_wolf", "lw"}:
        if returns is None:
            raise ValueError("returns data required for Ledoit–Wolf allocation.")
        try:
            weights = lw_min_var(returns, allow_short=allow_short)
        except ValueError:
            n = cov.shape[0]
            return pd.Series(np.full(n, 1.0 / n), index=cov.index)
        return weights.reindex(cov.index).fillna(0.0)
    if method in {"equal", "ew"}:
        n = cov.shape[0]
        return pd.Series(np.full(n, 1.0 / n), index=cov.index)
    raise ValueError(f"Unsupported risk model '{risk_model}'")
