"""Benchmark-differential multiple-testing controls.

The public entry point implements a null-centered, synchronous max-statistic
bootstrap. Candidate returns are always evaluated as differentials to an
explicit benchmark. A single resampled time index is shared across candidates
on every draw, preserving their cross-sectional dependence.
"""

from __future__ import annotations

from typing import Literal, Sequence

import numpy as np


def _bootstrap_indices(
    n: int,
    *,
    method: Literal["stationary", "circular", "iid"],
    block_length: int,
    rng: np.random.Generator,
) -> np.ndarray:
    if method == "iid":
        return rng.integers(0, n, size=n)
    if method == "circular":
        indices: np.ndarray = np.empty(n, dtype=int)
        position = 0
        while position < n:
            start = int(rng.integers(0, n))
            width = min(block_length, n - position)
            indices[position : position + width] = np.arange(start, start + width) % n
            position += width
        return indices

    probability = 1.0 / block_length
    indices = np.empty(n, dtype=int)
    current = int(rng.integers(0, n))
    for position in range(n):
        indices[position] = current
        if rng.random() < probability:
            current = int(rng.integers(0, n))
        else:
            current = (current + 1) % n
    return indices


def _studentized_means(matrix: np.ndarray) -> np.ndarray:
    n = matrix.shape[0]
    means = matrix.mean(axis=0)
    std = matrix.std(axis=0, ddof=1)
    return np.divide(
        np.sqrt(n) * means,
        std,
        out=np.zeros_like(means, dtype=float),
        where=std > 0.0,
    )


def centered_max_statistic_test(
    candidate_returns: np.ndarray,
    *,
    benchmark_returns: np.ndarray,
    candidate_names: Sequence[str] | None = None,
    seed: int = 0,
    num_bootstrap: int = 2000,
    method: Literal["stationary", "circular", "iid"] = "stationary",
    block_length: int | None = None,
) -> dict[str, object]:
    """Test whether the best candidate beats a benchmark after selection.

    The null is that no candidate has positive expected differential return.
    Candidate differentials are recentered before resampling, and every
    candidate uses the same resampled timestamps on a given draw.
    """

    candidates = np.asarray(candidate_returns, dtype=float)
    benchmark = np.asarray(benchmark_returns, dtype=float)
    if candidates.ndim == 1:
        candidates = candidates[:, None]
    if candidates.ndim != 2:
        raise ValueError("candidate_returns must be a 1D or 2D array")
    if benchmark.ndim != 1:
        raise ValueError("benchmark_returns must be one-dimensional")
    if candidates.shape[0] != benchmark.shape[0]:
        raise ValueError("candidate and benchmark observations must align")
    if candidates.shape[0] < 5:
        raise ValueError("at least five aligned observations are required")
    if candidates.shape[1] < 1:
        raise ValueError("at least one candidate is required")
    if not np.isfinite(candidates).all() or not np.isfinite(benchmark).all():
        raise ValueError("returns must be finite")
    if num_bootstrap < 1:
        raise ValueError("num_bootstrap must be positive")
    if method not in {"stationary", "circular", "iid"}:
        raise ValueError("unsupported bootstrap method")

    n_observations, n_candidates = candidates.shape
    names = list(candidate_names or [f"candidate_{idx}" for idx in range(n_candidates)])
    if len(names) != n_candidates or len(set(names)) != len(names):
        raise ValueError("candidate_names must be unique and match candidate columns")

    if block_length is None:
        block_length = max(1, int(round(1.1447 * n_observations ** (1.0 / 3.0))))
    block_length = int(block_length)
    if block_length < 1:
        raise ValueError("block_length must be positive")

    differentials = candidates - benchmark[:, None]
    observed_components = _studentized_means(differentials)
    observed_statistic = float(max(0.0, float(np.max(observed_components))))
    centered = differentials - differentials.mean(axis=0, keepdims=True)

    rng = np.random.default_rng(seed)
    distribution: np.ndarray = np.empty(num_bootstrap, dtype=float)
    for draw in range(num_bootstrap):
        indices = _bootstrap_indices(
            n_observations,
            method=method,
            block_length=block_length,
            rng=rng,
        )
        components = _studentized_means(centered[indices, :])
        distribution[draw] = max(0.0, float(np.max(components)))

    exceedances = int(np.count_nonzero(distribution >= observed_statistic))
    p_value = float((exceedances + 1) / (num_bootstrap + 1))
    best_index = int(np.argmax(observed_components))

    return {
        "test": "centered_synchronous_max_statistic",
        "null": "no_candidate_outperforms_benchmark",
        "benchmark": "explicit_return_series",
        "p_value": p_value,
        "observed_statistic": observed_statistic,
        "best_candidate": names[best_index],
        "candidate_statistics": {
            name: float(value) for name, value in zip(names, observed_components)
        },
        "distribution": [float(value) for value in distribution],
        "method": method,
        "block_length": block_length,
        "num_bootstrap": num_bootstrap,
        "num_observations": n_observations,
        "num_candidates": n_candidates,
        "null_centered": True,
        "synchronous_resampling": True,
    }
