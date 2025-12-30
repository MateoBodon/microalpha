from __future__ import annotations

import pandas as pd
import pytest

from microalpha.reporting.factors import align_factor_panel


def _make_factors(index: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Mkt_RF": 0.01,
            "SMB": 0.0,
            "HML": 0.0,
            "RF": 0.0001,
        },
        index=index,
    )


def test_align_factor_panel_rejects_shifted_dates() -> None:
    returns = pd.Series(
        0.01,
        index=pd.date_range("2024-01-01", periods=5, freq="D"),
        name="returns",
    )
    factors = _make_factors(pd.date_range("2024-01-02", periods=5, freq="D"))
    with pytest.raises(ValueError, match="misaligned|overlap|aligned"):
        align_factor_panel(returns, factors)


def test_align_factor_panel_requires_explicit_resample() -> None:
    returns = pd.Series(
        0.01,
        index=pd.date_range("2024-01-01", periods=91, freq="D"),
        name="returns",
    )
    factors = _make_factors(pd.date_range("2024-01-31", periods=3, freq="ME"))
    with pytest.raises(ValueError, match="returns are daily, factors are monthly"):
        align_factor_panel(returns, factors)

    aligned_returns, aligned_factors, meta = align_factor_panel(
        returns,
        factors,
        allow_resample=True,
        resample_rule="ME",
    )
    assert meta.n_obs == len(factors)
    assert meta.returns_freq == "daily"
    assert meta.factors_freq == "monthly"
    assert aligned_returns.index.equals(factors.index)
    assert aligned_factors.index.equals(factors.index)


def test_align_factor_panel_never_forward_fills_factors() -> None:
    returns = pd.Series(
        0.01,
        index=pd.date_range("2024-01-01", periods=40, freq="D"),
        name="returns",
    )
    factors = _make_factors(pd.date_range("2024-01-05", periods=6, freq="W-FRI"))
    aligned_returns, aligned_factors, meta = align_factor_panel(
        returns,
        factors,
        allow_resample=True,
        resample_rule="W-FRI",
    )
    assert meta.resampled is True
    assert aligned_returns.index.equals(factors.index)
    assert aligned_factors.index.equals(factors.index)
    assert len(aligned_returns) == len(factors)
    assert len(aligned_returns) < len(returns)
