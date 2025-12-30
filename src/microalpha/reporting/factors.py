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


@dataclass(frozen=True)
class FactorRegressionMeta:
    returns_freq: str
    factors_freq: str
    overlap_start: pd.Timestamp | None
    overlap_end: pd.Timestamp | None
    n_obs: int
    resampled: bool
    resample_rule: str | None
    returns_freq_inferred: str | None
    factors_freq_inferred: str | None


@dataclass(frozen=True)
class FactorRegressionOutput:
    results: list[FactorResult]
    meta: FactorRegressionMeta


def _validate_datetime_index(index: pd.DatetimeIndex, label: str) -> None:
    if not isinstance(index, pd.DatetimeIndex):
        raise TypeError(f"{label} index must be a DatetimeIndex")
    if index.has_duplicates:
        raise ValueError(f"{label} index contains duplicate timestamps")
    if not index.is_monotonic_increasing:
        raise ValueError(f"{label} index must be monotonic increasing")


def _normalize_freq_label(freq: str) -> str:
    upper = freq.upper()
    if upper.startswith(("D", "B", "CB")):
        return "daily"
    if upper.startswith("W"):
        return "weekly"
    if upper.startswith(("M", "BM", "MS", "BMS", "ME", "BME")):
        return "monthly"
    if upper.startswith(("Q", "BQ", "QS", "BQS")):
        return "quarterly"
    if upper.startswith(("A", "Y", "BA", "BY")):
        return "annual"
    return freq


def _label_from_timedelta(delta: pd.Timedelta) -> str:
    if pd.isna(delta):
        return "unknown"
    days = delta / pd.Timedelta(days=1)
    if abs(days - 1) <= 0.1:
        return "daily"
    if abs(days - 7) <= 0.6:
        return "weekly"
    if 27 <= days <= 31:
        return "monthly"
    if 89 <= days <= 92:
        return "quarterly"
    if 364 <= days <= 366:
        return "annual"
    return f"{days:.1f}d"


def _infer_index_frequency(index: pd.DatetimeIndex) -> tuple[str, str | None]:
    if index.size < 2:
        return "unknown", None
    inferred = None
    try:
        inferred = pd.infer_freq(index)
    except ValueError:
        inferred = None
    if inferred:
        return _normalize_freq_label(inferred), inferred
    deltas = index.to_series().diff().dropna()
    if deltas.empty:
        return "unknown", None
    return _label_from_timedelta(deltas.median()), None


def _compound_returns(returns: pd.Series) -> float:
    values = returns.to_numpy(dtype=float)
    return float(np.prod(1.0 + values) - 1.0)


def _resample_returns_to_factor_index(
    returns: pd.Series,
    factor_index: pd.DatetimeIndex,
    rule: str | None,
) -> pd.Series:
    if returns.empty:
        raise ValueError("Returns series is empty; cannot resample")
    overlap = factor_index[
        (factor_index >= returns.index.min()) & (factor_index <= returns.index.max())
    ]
    if overlap.empty:
        raise ValueError("No overlapping dates between factors and returns")
    if rule:
        resampled = returns.resample(rule).apply(_compound_returns)
        resampled = resampled.reindex(overlap)
        if resampled.isna().any():
            missing = resampled[resampled.isna()].index
            raise ValueError(
                f"Resample produced missing returns for {len(missing)} period(s); "
                "check resample_rule or input coverage"
            )
        return resampled
    values: list[float] = []
    prev: pd.Timestamp | None = None
    for date in overlap:
        if prev is None:
            mask = returns.index <= date
        else:
            mask = (returns.index > prev) & (returns.index <= date)
        window = returns.loc[mask]
        if window.empty:
            raise ValueError(
                f"No returns available to resample for factor date {date.date()}"
            )
        values.append(_compound_returns(window))
        prev = date
    return pd.Series(values, index=overlap, name=returns.name)


def align_factor_panel(
    returns: pd.Series,
    factors: pd.DataFrame,
    *,
    allow_resample: bool = False,
    resample_rule: str | None = None,
) -> tuple[pd.Series, pd.DataFrame, FactorRegressionMeta]:
    _validate_datetime_index(returns.index, "returns")
    _validate_datetime_index(factors.index, "factors")

    returns_freq, returns_freq_inferred = _infer_index_frequency(returns.index)
    factors_freq, factors_freq_inferred = _infer_index_frequency(factors.index)

    resampled = False
    resample_used = resample_rule
    aligned_returns = returns
    aligned_factors = factors

    if returns_freq != factors_freq:
        if not allow_resample:
            rule_hint = factors_freq_inferred or "M"
            raise ValueError(
                f"returns are {returns_freq}, factors are {factors_freq}; "
                f"set allow_resample=True with rule='{rule_hint}' (or use {returns_freq} factors)"
            )
        if resample_used is None:
            resample_used = factors_freq_inferred
        aligned_returns = _resample_returns_to_factor_index(
            returns, factors.index, resample_used
        )
        aligned_factors = factors.loc[aligned_returns.index]
        resampled = True

    returns_index = aligned_returns.index
    factors_index = aligned_factors.index
    overlap = returns_index.intersection(factors_index)
    if overlap.empty:
        raise ValueError("No overlapping dates between factors and returns")
    returns_subset = returns_index.isin(factors_index).all()
    factors_subset = factors_index.isin(returns_index).all()
    if not (returns_subset or factors_subset):
        raise ValueError(
            "returns and factors indexes are misaligned; "
            "refuse to align with partial overlap"
        )

    target_index = returns_index if returns_subset else factors_index
    aligned_returns = aligned_returns.loc[target_index]
    aligned_factors = aligned_factors.loc[target_index]

    meta = FactorRegressionMeta(
        returns_freq=returns_freq,
        factors_freq=factors_freq,
        overlap_start=target_index.min() if not target_index.empty else None,
        overlap_end=target_index.max() if not target_index.empty else None,
        n_obs=int(target_index.size),
        resampled=resampled,
        resample_rule=resample_used,
        returns_freq_inferred=returns_freq_inferred,
        factors_freq_inferred=factors_freq_inferred,
    )
    return aligned_returns, aligned_factors, meta


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
    *,
    allow_resample: bool = False,
    resample_rule: str | None = None,
) -> FactorRegressionOutput:
    """Run Carhart/FF5(+MOM) regressions with Newey-West errors."""

    model_key = model.lower()
    if model_key not in MODEL_FACTORS:
        raise ValueError(f"Unknown factor model '{model}'. Valid options: {sorted(MODEL_FACTORS)}")

    factor_names = MODEL_FACTORS[model_key]
    returns = _prepare_returns(equity_csv)
    factors = _prepare_factors(factor_csv, factor_names)
    aligned_returns, aligned_factors, meta = align_factor_panel(
        returns,
        factors,
        allow_resample=allow_resample,
        resample_rule=resample_rule,
    )
    rf = aligned_factors["RF"].astype(float)
    excess = aligned_returns - rf
    X, y = _design_matrix(aligned_factors, factor_names, excess)

    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residuals = y - X @ beta
    se = _newey_west_se(X, residuals, lag=hac_lags)
    with np.errstate(divide="ignore", invalid="ignore"):
        t_stats = np.where(se > 0, beta / se, np.nan)

    labels = ["Alpha", *factor_names]
    results = [
        FactorResult(name=lab, beta=float(b), t_stat=float(t))
        for lab, b, t in zip(labels, beta, t_stats)
    ]
    return FactorRegressionOutput(results=results, meta=meta)


def _format_markdown_table(results: Iterable[FactorResult]) -> str:
    lines = ["| Factor | Beta | t-stat |", "| --- | ---:| ---:|"]
    for row in results:
        lines.append(f"| {row.name} | {row.beta:.4f} | {row.t_stat:.2f} |")
    return "\n".join(lines)


def _format_meta_line(meta: FactorRegressionMeta) -> str:
    start = meta.overlap_start.date().isoformat() if meta.overlap_start else "n/a"
    end = meta.overlap_end.date().isoformat() if meta.overlap_end else "n/a"
    resample_note = ""
    if meta.resampled:
        rule = f", rule={meta.resample_rule}" if meta.resample_rule else ""
        resample_note = f" (resampled returns{rule})"
    return (
        "_Frequency: "
        f"returns {meta.returns_freq}, factors {meta.factors_freq}; "
        f"overlap {start} to {end}; n_obs={meta.n_obs}{resample_note}._"
    )


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
    parser.add_argument(
        "--allow-resample",
        action="store_true",
        help="Allow resampling returns to factor frequency (compounded).",
    )
    parser.add_argument(
        "--resample-rule",
        default=None,
        help="Optional pandas resample rule for returns (e.g., 'M', 'W-FRI').",
    )
    args = parser.parse_args()

    equity_csv = args.artifact_dir / "equity_curve.csv"
    if not equity_csv.exists():
        raise SystemExit(f"Could not find equity_curve.csv under {args.artifact_dir}")
    if not args.factors.exists():
        raise SystemExit(f"Factor CSV not found: {args.factors}")

    output = compute_factor_regression(
        equity_csv,
        args.factors,
        model=args.model,
        hac_lags=args.hac_lags,
        allow_resample=args.allow_resample,
        resample_rule=args.resample_rule,
    )
    table = _format_markdown_table(output.results)
    print(table)
    print(_format_meta_line(output.meta))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(table + "\n" + _format_meta_line(output.meta) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
