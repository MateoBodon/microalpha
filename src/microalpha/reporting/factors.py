"""Factor regression utilities for Microalpha summaries."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

MODEL_FACTORS = {
    "ff3": ["Mkt_RF", "SMB", "HML"],
    "carhart": ["Mkt_RF", "SMB", "HML", "MOM"],
    "ff5_mom": ["Mkt_RF", "SMB", "HML", "RMW", "CMA", "MOM"],
}


@dataclass
class FactorResult:
    name: str
    beta: float
    t_stat: float


def _prepare_returns(equity_csv: Path) -> pd.Series:
    df = pd.read_csv(equity_csv)
    if "returns" not in df.columns:
        raise ValueError("equity_curve.csv must contain a 'returns' column")
    ts = pd.to_datetime(df["timestamp"]).dt.normalize()
    returns = pd.Series(df["returns"].astype(float).to_numpy(), index=ts)
    returns = returns.loc[~returns.index.duplicated(keep="last")]
    return returns


def _prepare_factors(factor_csv: Path, required: Sequence[str]) -> pd.DataFrame:
    factors = pd.read_csv(factor_csv, parse_dates=["date"])
    required_cols = set(required) | {"RF"}
    missing = required_cols.difference(factors.columns)
    if missing:
        raise ValueError(f"Factor CSV missing columns: {sorted(missing)}")
    frame = factors.set_index("date").sort_index()
    return frame


def _design_matrix(
    factors: pd.DataFrame, factor_names: Sequence[str], excess_returns: pd.Series
) -> tuple[np.ndarray, np.ndarray]:
    aligned = factors[list(factor_names)].join(excess_returns.rename("excess"), how="inner")
    aligned = aligned.dropna()
    if aligned.empty:
        raise ValueError("No overlapping dates between factors and returns")
    y = aligned["excess"].to_numpy(dtype=float)
    X = aligned[list(factor_names)].to_numpy(dtype=float)
    intercept = np.ones((X.shape[0], 1), dtype=float)
    X_design = np.hstack((intercept, X))
    return X_design, y


def _newey_west_se(X: np.ndarray, residuals: np.ndarray, lag: int) -> np.ndarray:
    T, k = X.shape
    lag = min(lag, T - 1) if T > 1 else 0
    XtX_inv = np.linalg.inv(X.T @ X)
    S = np.zeros((k, k), dtype=float)
    for t in range(T):
        xt = X[t : t + 1].T
        S += residuals[t] ** 2 * (xt @ xt.T)
    for ell in range(1, lag + 1):
        weight = 1.0 - ell / (lag + 1)
        Gamma = np.zeros((k, k), dtype=float)
        for t in range(ell, T):
            xt = X[t]
            xt_lag = X[t - ell]
            Gamma += residuals[t] * residuals[t - ell] * np.outer(xt, xt_lag)
        S += weight * (Gamma + Gamma.T)
    var = XtX_inv @ S @ XtX_inv
    return np.sqrt(np.diag(var))


def compute_factor_regression(
    equity_csv: Path,
    factor_csv: Path,
    model: str = "ff3",
    hac_lags: int = 5,
) -> list[FactorResult]:
    """Run Carhart/FF5(+MOM) regressions with Newey-West errors."""

    model_key = model.lower()
    if model_key not in MODEL_FACTORS:
        raise ValueError(f"Unknown factor model '{model}'. Valid options: {sorted(MODEL_FACTORS)}")

    factor_names = MODEL_FACTORS[model_key]
    returns = _prepare_returns(equity_csv)
    factors = _prepare_factors(factor_csv, factor_names)
    common = factors.index.intersection(returns.index)
    if common.empty:
        raise ValueError("No overlapping dates between factors and returns")
    returns_aligned = returns.loc[common]
    rf = factors.loc[common, "RF"].astype(float)
    excess = returns_aligned - rf
    X, y = _design_matrix(factors.loc[common], factor_names, excess)

    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residuals = y - X @ beta
    se = _newey_west_se(X, residuals, lag=hac_lags)
    with np.errstate(divide="ignore", invalid="ignore"):
        t_stats = np.where(se > 0, beta / se, np.nan)

    labels = ["Alpha", *factor_names]
    return [FactorResult(name=lab, beta=float(b), t_stat=float(t)) for lab, b, t in zip(labels, beta, t_stats)]


def _format_markdown_table(results: Iterable[FactorResult]) -> str:
    lines = ["| Factor | Beta | t-stat |", "| --- | ---:| ---:|"]
    for row in results:
        lines.append(f"| {row.name} | {row.beta:.4f} | {row.t_stat:.2f} |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run factor regressions on Microalpha artifacts")
    parser.add_argument("artifact_dir", type=Path, help="Artifact directory containing equity_curve.csv")
    parser.add_argument(
        "--factors",
        type=Path,
        default=Path("data/factors/ff3_sample.csv"),
        help="Path to factor CSV (default: data/factors/ff3_sample.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional markdown file to write the regression table to",
    )
    parser.add_argument("--hac-lags", type=int, default=5, help="Newey-West lag length (default: 5)")
    parser.add_argument(
        "--model",
        choices=sorted(MODEL_FACTORS.keys()),
        default="carhart",
        help="Factor model to run (default: carhart)",
    )
    args = parser.parse_args()

    equity_csv = args.artifact_dir / "equity_curve.csv"
    if not equity_csv.exists():
        raise SystemExit(f"Could not find equity_curve.csv under {args.artifact_dir}")
    if not args.factors.exists():
        raise SystemExit(f"Factor CSV not found: {args.factors}")

    results = compute_factor_regression(
        equity_csv,
        args.factors,
        model=args.model,
        hac_lags=args.hac_lags,
    )
    table = _format_markdown_table(results)
    print(table)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(table + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
