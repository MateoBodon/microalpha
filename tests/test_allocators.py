from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from microalpha.allocators import budgeted_allocator, lw_min_var, risk_parity


def test_risk_parity_equal_risk_contributions():
    cov = pd.DataFrame(
        [[0.04, 0.01, 0.0], [0.01, 0.05, 0.02], [0.0, 0.02, 0.09]],
        index=["A", "B", "C"],
        columns=["A", "B", "C"],
    )
    weights = risk_parity(cov)
    assert pytest.approx(float(weights.sum()), abs=1e-8) == 1.0
    assert (weights > 0).all()
    rc = weights.values * (cov.to_numpy() @ weights.values)
    assert np.max(rc) - np.min(rc) < 1e-6


def test_ledoit_wolf_min_var_weights_long_only():
    returns = pd.DataFrame(
        [
            [0.01, 0.015, -0.002],
            [-0.004, 0.003, 0.007],
            [0.006, -0.001, 0.004],
            [0.002, 0.008, -0.003],
            [0.007, 0.002, 0.001],
        ],
        columns=["A", "B", "C"],
    )
    weights, cov = lw_min_var(returns, return_cov=True)
    assert isinstance(cov, pd.DataFrame)
    assert pytest.approx(float(weights.sum()), abs=1e-8) == 1.0
    assert (weights >= 0).all()

    # Verify minimum variance normalisation
    ones = np.ones(len(weights))
    inv_cov = np.linalg.pinv(cov.to_numpy() + np.eye(len(weights)) * 1e-6)
    mv_weights = inv_cov @ ones
    mv_weights /= ones @ mv_weights
    assert np.linalg.norm(mv_weights - weights.values) < 1.0


def test_budgeted_allocator_long_short_split():
    signals = pd.Series({"A": 0.6, "B": 0.3, "C": -0.4})
    cov = pd.DataFrame(
        [[0.02, 0.01, 0.0], [0.01, 0.03, 0.015], [0.0, 0.015, 0.05]],
        index=["A", "B", "C"],
        columns=["A", "B", "C"],
    )
    weights = budgeted_allocator(signals, cov, total_budget=1.0)
    assert not weights.isna().any()
    assert (weights.loc[["A", "B"]] > 0).all()
    assert weights.loc["C"] < 0

    long_budget = weights[weights > 0].sum()
    short_budget = abs(weights[weights < 0].sum())
    total_signal = signals.clip(lower=0).sum() + signals.clip(upper=0).abs().sum()
    expected_long = signals.clip(lower=0).sum() / total_signal
    expected_short = signals.clip(upper=0).abs().sum() / total_signal
    assert math.isclose(long_budget, expected_long, rel_tol=1e-6)
    assert math.isclose(short_budget, expected_short, rel_tol=1e-6)

    # Within long bucket risk contributions should be close
    cov_long = cov.loc[["A", "B"], ["A", "B"]]
    long_weights = weights.loc[["A", "B"]] / long_budget
    rc_long = long_weights.values * (cov_long.to_numpy() @ long_weights.values)
    assert np.max(rc_long) - np.min(rc_long) < 1e-6


def test_budgeted_allocator_ledoit_wolf_option():
    signals = pd.Series({"A": 0.4, "B": 0.1, "C": -0.3, "D": -0.2})
    returns = pd.DataFrame(
        np.array(
            [
                [0.01, 0.015, -0.002, 0.004],
                [-0.005, 0.002, 0.006, -0.001],
                [0.007, -0.003, 0.005, 0.002],
                [0.003, 0.001, -0.004, 0.005],
                [0.006, 0.004, -0.001, 0.003],
            ]
        ),
        columns=["A", "B", "C", "D"],
    )
    cov = returns.cov()
    weights = budgeted_allocator(
        signals, cov, total_budget=1.0, risk_model="lw_min_var", returns=returns
    )
    assert not weights.isna().any()
    assert weights[["A", "B"]].sum() > 0
    assert weights[["C", "D"]].sum() < 0
