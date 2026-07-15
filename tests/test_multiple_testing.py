import numpy as np
import pytest

from microalpha.multiple_testing import centered_max_statistic_test
from microalpha.walkforward import bootstrap_reality_check


def test_noise_family_is_not_promoted_after_max_statistic_correction():
    rng = np.random.default_rng(20260715)
    candidates = rng.normal(0.0, 0.01, size=(756, 128))
    result = centered_max_statistic_test(
        candidates,
        benchmark_returns=np.zeros(756),
        seed=91,
        num_bootstrap=999,
        block_length=8,
        candidate_names=[f"noise_{idx:03d}" for idx in range(128)],
    )

    assert result["null_centered"] is True
    assert result["synchronous_resampling"] is True
    assert float(result["p_value"]) >= 0.05


def test_planted_positive_control_survives_correction():
    rng = np.random.default_rng(7)
    candidates = rng.normal(0.0, 0.01, size=(756, 32))
    candidates[:, 0] += 0.002
    result = centered_max_statistic_test(
        candidates,
        benchmark_returns=np.zeros(756),
        seed=11,
        num_bootstrap=999,
        block_length=8,
        candidate_names=["planted_control", *[f"noise_{idx:02d}" for idx in range(31)]],
    )

    assert result["best_candidate"] == "planted_control"
    assert float(result["p_value"]) <= 0.01


def test_candidate_and_benchmark_must_align():
    with pytest.raises(ValueError, match="must align"):
        centered_max_statistic_test(
            np.zeros((10, 2)),
            benchmark_returns=np.zeros(9),
        )


def test_walkforward_reality_check_rejects_tail_alignment():
    results = [
        {
            "returns": np.zeros(10),
            "metrics": {"sharpe_ratio": 0.0},
            "params": {"model": "a"},
        },
        {
            "returns": np.zeros(9),
            "metrics": {"sharpe_ratio": 0.0},
            "params": {"model": "b"},
        },
    ]
    with pytest.raises(ValueError, match="aligned return calendar"):
        bootstrap_reality_check(results, seed=7)
