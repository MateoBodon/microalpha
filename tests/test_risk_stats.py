from __future__ import annotations

import numpy as np
import pandas as pd

from microalpha.risk import bootstrap_sharpe_ratio
from microalpha.risk_stats import block_bootstrap, sharpe_stats


def _ar1_series(n: int, phi: float, scale: float, seed: int) -> pd.Series:
    rng = np.random.default_rng(seed)
    shocks = rng.normal(scale=scale, size=n)
    series = np.zeros(n, dtype=float)
    for t in range(1, n):
        series[t] = phi * series[t - 1] + shocks[t]
    return pd.Series(series)


def test_hac_newey_west_widens_uncertainty_on_ar1() -> None:
    returns = _ar1_series(n=400, phi=0.6, scale=0.01, seed=2025)
    iid_stats = sharpe_stats(returns, hac_lags=None)
    hac_stats = sharpe_stats(returns, hac_lags=6)

    assert hac_stats["se"] > iid_stats["se"]
    assert abs(hac_stats["tstat"]) < abs(iid_stats["tstat"])


def test_block_bootstrap_confidence_interval_covers_zero_sharpe() -> None:
    rng = np.random.default_rng(77)
    base = rng.normal(loc=0.0, scale=0.01, size=360)
    returns = pd.Series(base - base.mean())

    result = bootstrap_sharpe_ratio(
        returns,
        num_simulations=400,
        periods=252,
        method="stationary",
        block_len=10,
        rng=np.random.default_rng(1234),
    )
    ci_low, ci_high = result["confidence_interval"]
    assert ci_low <= 0.0 <= ci_high


def test_block_bootstrap_generator_shapes() -> None:
    data = np.arange(12, dtype=float)
    rng = np.random.default_rng(11)
    samples = list(block_bootstrap(data, B=5, method="circular", block_len=4, rng=rng))
    assert len(samples) == 5
    for sample in samples:
        assert sample.shape == data.shape
