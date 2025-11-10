"""Analytics helpers for IC/IR curves, deciles, and rolling betas."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PLOTS_DIR = Path("artifacts/plots")
ANALYTICS_DIR = Path("artifacts/analytics")


@dataclass
class AnalyticsArtifacts:
    ic_series_path: Path
    deciles_path: Path
    betas_path: Path | None
    ic_plot: Path
    decile_plot: Path
    beta_plot: Path | None


def _resolve_plot_path(artifact_dir: Path, plots_dir: Path, stem: str) -> Path:
    run_label = artifact_dir.name or "analytics"
    return plots_dir / f"{run_label}_{stem}.png"


def _pearson(x: pd.Series, y: pd.Series) -> float:
    xv = x.to_numpy(dtype=float)
    yv = y.to_numpy(dtype=float)
    if xv.size < 2 or yv.size < 2:
        return float("nan")
    xv = xv - xv.mean()
    yv = yv - yv.mean()
    denom = float(np.sqrt((xv**2).sum()) * np.sqrt((yv**2).sum()))
    if denom == 0.0:
        return float("nan")
    return float(np.dot(xv, yv) / denom)


def load_signals(
    signals_path: Path,
    *,
    date_col: str = "as_of",
    score_col: str = "score",
    forward_col: str = "forward_return",
) -> pd.DataFrame:
    df = pd.read_csv(signals_path)
    required = {date_col, score_col, forward_col}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Signals file missing columns: {sorted(missing)}")
    df = df.rename(
        columns={
            date_col: "as_of",
            score_col: "score",
            forward_col: "forward_return",
        }
    )
    df["as_of"] = pd.to_datetime(df["as_of"])
    df = df.dropna(subset=["as_of", "score", "forward_return"])
    return df.sort_values("as_of")


def compute_ic_series(signals: pd.DataFrame, method: str = "spearman") -> pd.Series:
    ics: dict[pd.Timestamp, float] = {}
    for as_of, group in signals.groupby("as_of"):
        if len(group) < 3:
            continue
        scores = group["score"].astype(float)
        returns = group["forward_return"].astype(float)
        if scores.nunique() < 2 or returns.nunique() < 2:
            continue
        if method.lower() == "spearman":
            ranked_scores = scores.rank(method="average")
            ranked_returns = returns.rank(method="average")
            corr = _pearson(ranked_scores, ranked_returns)
        else:
            corr = _pearson(scores, returns)
        if np.isfinite(corr):
            ics[pd.Timestamp(as_of)] = float(corr)
    if not ics:
        return pd.Series(dtype=float, name="ic")
    series = pd.Series(ics).sort_index()
    series.name = "ic"
    return series


def compute_rolling_ir(ic_series: pd.Series, window: int = 63) -> pd.Series:
    if ic_series.empty:
        return pd.Series(dtype=float, name="rolling_ir")
    rolling_mean = ic_series.rolling(window).mean()
    rolling_std = ic_series.rolling(window).std(ddof=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        ir = np.where(rolling_std > 0, np.sqrt(window) * (rolling_mean / rolling_std), np.nan)
    result = pd.Series(ir, index=ic_series.index, name="rolling_ir")
    return result


def compute_decile_table(signals: pd.DataFrame, deciles: int = 10) -> pd.DataFrame:
    records: list[dict[str, float | str]] = []
    for as_of, group in signals.groupby("as_of"):
        if group["score"].nunique() < deciles or len(group) < deciles:
            continue
        try:
            buckets = pd.qcut(
                group["score"],
                deciles,
                labels=list(range(1, deciles + 1)),
            )
        except ValueError:
            continue
        frame = group.assign(decile=buckets.astype(int))
        stats = frame.groupby("decile")["forward_return"].mean()
        for decile, value in stats.items():
            records.append(
                {
                    "decile": int(decile),
                    "mean_return": float(value),
                }
            )
    if not records:
        return pd.DataFrame(columns=["decile", "mean_return"])
    summary = (
        pd.DataFrame(records)
        .groupby("decile")["mean_return"]
        .mean()
        .sort_index()
    )
    summary.index = [f"P{int(idx)}" for idx in summary.index]
    table = summary.to_frame().reset_index().rename(columns={"index": "decile"})
    tail_label = f"P{deciles}"
    head_label = "P1"
    if tail_label in summary.index and head_label in summary.index:
        long_short = summary.loc[tail_label] - summary.loc[head_label]
        table = pd.concat(
            [
                table,
                pd.DataFrame(
                    [
                        {
                            "decile": f"{tail_label}-{head_label}",
                            "mean_return": float(long_short),
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    return table


def load_equity_returns(equity_csv: Path) -> pd.Series:
    df = pd.read_csv(equity_csv)
    if "returns" not in df.columns:
        raise ValueError("equity_curve.csv must include a 'returns' column")
    timestamps = pd.to_datetime(df["timestamp"], errors="coerce")
    if timestamps.isna().all():
        timestamps = pd.to_datetime(df["timestamp"], unit="ns", errors="coerce")
    timestamps = timestamps.fillna(method="ffill")
    series = pd.Series(df["returns"].astype(float).to_numpy(), index=timestamps)
    series = series.loc[~series.index.duplicated(keep="last")]
    series.name = "returns"
    return series


def load_factor_frame(factor_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(factor_csv, parse_dates=["date"])
    if "RF" not in df.columns:
        raise ValueError("Factor CSV must contain an 'RF' column")
    return df.set_index("date").sort_index()


def compute_rolling_betas(
    returns: pd.Series,
    factors: pd.DataFrame,
    *,
    factor_cols: Sequence[str] | None = None,
    window: int = 63,
) -> pd.DataFrame:
    if factor_cols is None:
        factor_cols = [col for col in factors.columns if col != "RF"]
    aligned = factors.join(returns.rename("strategy"), how="inner")
    if aligned.empty:
        return pd.DataFrame(columns=["alpha", *factor_cols])
    rf = aligned.get("RF", 0.0)
    aligned["excess"] = aligned["strategy"] - rf
    records: list[dict[str, float | pd.Timestamp]] = []
    for idx in range(window - 1, len(aligned)):
        window_frame = aligned.iloc[idx - window + 1 : idx + 1]
        X = window_frame[list(factor_cols)].to_numpy(dtype=float)
        y = window_frame["excess"].to_numpy(dtype=float)
        if np.isnan(X).any() or np.isnan(y).any():
            continue
        X_design = np.column_stack([np.ones(len(X)), X])
        try:
            beta = np.linalg.lstsq(X_design, y, rcond=None)[0]
        except np.linalg.LinAlgError:
            continue
        record = {"date": window_frame.index[-1], "alpha": float(beta[0])}
        for name, value in zip(factor_cols, beta[1:]):
            record[name] = float(value)
        records.append(record)
    if not records:
        return pd.DataFrame(columns=["alpha", *factor_cols])
    frame = pd.DataFrame(records).set_index("date")
    return frame


def plot_ic_series(ic_series: pd.Series, ir_series: pd.Series, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    if ic_series.empty:
        axes[0].text(0.5, 0.5, "IC unavailable", ha="center", va="center", transform=axes[0].transAxes)
    else:
        axes[0].plot(ic_series.index, ic_series.values, label="IC", color="#1f77b4")
        axes[0].axhline(0.0, color="black", linewidth=0.8, linestyle=":")
        axes[0].set_ylabel("IC")
        axes[0].grid(True, linestyle=":", alpha=0.3)
    if ir_series.empty:
        axes[1].text(0.5, 0.5, "Rolling IR unavailable", ha="center", va="center", transform=axes[1].transAxes)
    else:
        axes[1].plot(ir_series.index, ir_series.values, label="Rolling IR", color="#d62728")
        axes[1].axhline(0.0, color="black", linewidth=0.8, linestyle=":")
        axes[1].set_ylabel("IR")
        axes[1].grid(True, linestyle=":", alpha=0.3)
    axes[1].set_xlabel("Date")
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def plot_deciles(table: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 4))
    if table.empty:
        ax.text(0.5, 0.5, "Deciles unavailable", ha="center", va="center", transform=ax.transAxes)
    else:
        labels = table["decile"].astype(str)
        mask = labels.str.match(r"^P\d+$")
        bars = table.loc[mask & (labels != "P10-P1"), ["decile", "mean_return"]]
        ax.bar(bars["decile"], bars["mean_return"], color="#6baed6")
        ls_row = table.loc[labels.str.endswith("-P1"), "mean_return"]
        if not ls_row.empty:
            ax.axhline(
                float(ls_row.iloc[0]),
                color="#d62728",
                linestyle="--",
                label=table.loc[labels.str.endswith("-P1"), "decile"].iloc[0],
            )
            ax.legend()
    ax.set_ylabel("Mean forward return")
    ax.set_xlabel("Decile")
    ax.grid(True, linestyle=":", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def plot_rolling_betas(betas: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    if betas.empty:
        ax.text(0.5, 0.5, "Rolling betas unavailable", ha="center", va="center", transform=ax.transAxes)
    else:
        for column in betas.columns:
            ax.plot(betas.index, betas[column], label=column)
        ax.legend(loc="upper right")
    ax.axhline(0.0, color="black", linewidth=0.8, linestyle=":")
    ax.set_ylabel("Beta")
    ax.set_xlabel("Date")
    ax.grid(True, linestyle=":", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def generate_analytics(
    artifact_dir: Path,
    *,
    signals_path: Path | None = None,
    equity_path: Path | None = None,
    factor_path: Path | None = None,
    plots_dir: Path = PLOTS_DIR,
    analytics_dir: Path = ANALYTICS_DIR,
    ic_method: str = "spearman",
    window: int = 63,
    deciles: int = 10,
) -> AnalyticsArtifacts:
    artifact_dir = artifact_dir.resolve()
    if not artifact_dir.exists():
        raise FileNotFoundError(f"Artifact directory not found: {artifact_dir}")

    default_signals = signals_path or (artifact_dir / "signals.csv")
    if not default_signals.exists():
        raise FileNotFoundError(
            "Signals CSV not found; provide --signals pointing to a file with as_of/score/forward_return columns."
        )
    signals = load_signals(default_signals)
    equity_csv = equity_path or (artifact_dir / "equity_curve.csv")
    returns = load_equity_returns(equity_csv)

    ic_series = compute_ic_series(signals, method=ic_method)
    ir_series = compute_rolling_ir(ic_series, window=window)
    decile_table = compute_decile_table(signals, deciles=deciles)

    factors_df: pd.DataFrame | None = None
    if factor_path:
        factor_csv = Path(factor_path)
        if factor_csv.exists():
            factors_df = load_factor_frame(factor_csv)
    elif Path("data/factors/ff5_sample.csv").exists():
        factors_df = load_factor_frame(Path("data/factors/ff5_sample.csv"))

    rolling_betas: pd.DataFrame | None = None
    if factors_df is not None:
        factor_cols = [col for col in factors_df.columns if col != "RF"]
        rolling_betas = compute_rolling_betas(returns, factors_df, factor_cols=factor_cols, window=window)

    analytics_dir.mkdir(parents=True, exist_ok=True)
    ic_path = analytics_dir / f"{artifact_dir.name}_ic_series.csv"
    ic_series.to_frame().to_csv(ic_path)
    decile_path = analytics_dir / f"{artifact_dir.name}_deciles.csv"
    decile_table.to_csv(decile_path, index=False)
    betas_path: Path | None = None
    if rolling_betas is not None:
        betas_path = analytics_dir / f"{artifact_dir.name}_rolling_betas.csv"
        rolling_betas.to_csv(betas_path)

    plots_dir.mkdir(parents=True, exist_ok=True)
    ic_plot = _resolve_plot_path(artifact_dir, plots_dir, "ic_ir")
    decile_plot = _resolve_plot_path(artifact_dir, plots_dir, "deciles")
    beta_plot: Path | None = None
    plot_ic_series(ic_series, ir_series, ic_plot)
    plot_deciles(decile_table, decile_plot)
    if rolling_betas is not None and not rolling_betas.empty:
        beta_plot = _resolve_plot_path(artifact_dir, plots_dir, "rolling_betas")
        plot_rolling_betas(rolling_betas, beta_plot)

    return AnalyticsArtifacts(
        ic_series_path=ic_path,
        deciles_path=decile_path,
        betas_path=betas_path,
        ic_plot=ic_plot,
        decile_plot=decile_plot,
        beta_plot=beta_plot,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir", type=Path, help="Artifact directory containing equity_curve.csv and signals.csv")
    parser.add_argument("--signals", type=Path, default=None, help="Override path to signals CSV")
    parser.add_argument("--factors", type=Path, default=None, help="Optional factor CSV (FF5+MOM compatible)")
    parser.add_argument("--plots-dir", type=Path, default=PLOTS_DIR, help="Directory for saving plots (default: artifacts/plots)")
    parser.add_argument("--analytics-dir", type=Path, default=ANALYTICS_DIR, help="Directory for saving CSV analytics (default: artifacts/analytics)")
    parser.add_argument("--window", type=int, default=63, help="Rolling window (trading days) for IR and betas")
    parser.add_argument("--deciles", type=int, default=10, help="Number of buckets for decile aggregation")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    generate_analytics(
        artifact_dir=args.artifact_dir,
        signals_path=args.signals,
        factor_path=args.factors,
        plots_dir=args.plots_dir,
        analytics_dir=args.analytics_dir,
        window=args.window,
        deciles=args.deciles,
    )


if __name__ == "__main__":
    main()
