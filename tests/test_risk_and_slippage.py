import pandas as pd
import pytest

from microalpha import risk
from microalpha.slippage import VolumeSlippageModel


def test_create_sharpe_ratio_handles_zero_volatility():
    series = pd.Series([0.01, 0.01, 0.01])
    assert risk.create_sharpe_ratio(series) == 0.0


def test_create_drawdowns_returns_expected_shapes():
    equity = pd.Series([100, 110, 105, 120])
    drawdowns, max_drawdown = risk.create_drawdowns(equity)

    assert len(drawdowns) == len(equity)
    assert pytest.approx(max_drawdown, rel=1e-6) == (5 / 110)


def test_bootstrap_sharpe_ratio_returns_distribution():
    returns = pd.Series([0.01, -0.02, 0.015, 0.0, 0.03])
    result = risk.bootstrap_sharpe_ratio(returns, num_simulations=20, periods=252)

    assert len(result["sharpe_dist"]) == 20
    assert 0.0 <= result["p_value"] <= 1.0
    low, high = result["confidence_interval"]
    assert low <= high


def test_bootstrap_sharpe_ratio_handles_short_series():
    returns = pd.Series([0.0, 0.0])
    result = risk.bootstrap_sharpe_ratio(returns)

    assert result == {
        "sharpe_dist": [0.0],
        "p_value": 1.0,
        "confidence_interval": (0.0, 0.0),
    }


def test_volume_slippage_model_grows_quadratically():
    model = VolumeSlippageModel(price_impact=0.0001)
    assert model.calculate_slippage(0, 100.0) == 0.0
    assert model.calculate_slippage(10, 100.0) == pytest.approx(0.01)
    assert model.calculate_slippage(20, 100.0) == pytest.approx(0.04)
