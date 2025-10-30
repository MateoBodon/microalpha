"""Render separate equity and bootstrap plots for Microalpha runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DEFAULT_TITLE = "Microalpha Flagship Performance"
DEFAULT_EQUITY_NAME = "equity_curve.png"
DEFAULT_BOOTSTRAP_NAME = "bootstrap_hist.png"


def _ensure_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    candidate = Path(path)
    return candidate if candidate.exists() else None


def _load_metrics(path: Path | None) -> dict[str, float]:
    if path is None:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def _load_bootstrap(path: Path | None) -> list[float]:
    if path is None:
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    if isinstance(payload, dict):
        dist = payload.get("distribution") or []
        return [float(x) for x in dist]
    if isinstance(payload, list):
        if payload and isinstance(payload[0], (int, float)):
            return [float(x) for x in payload]
        samples: list[float] = []
        for entry in payload:
            dist = entry.get("distribution") if isinstance(entry, dict) else None
            if dist:
                samples.extend(float(x) for x in dist)
        return samples
    return []


def _compute_drawdown(equity: pd.Series) -> pd.Series:
    running_max = equity.cummax()
    dd = equity / running_max - 1.0
    return dd.fillna(0.0)


def render_tearsheet(
    equity_csv: str | Path,
    bootstrap_json: str | Path | None,
    output_path: str | Path,
    *,
    bootstrap_output: str | Path | None = None,
    metrics_path: str | Path | None = None,
    title: str | None = None,
) -> Mapping[str, Path]:
    """Render equity and bootstrap plots.

    Parameters
    ----------
    equity_csv
        Equity curve CSV containing "timestamp" and "equity" columns.
    bootstrap_json
        JSON file containing bootstrap samples (list of floats or legacy payload).
    output_path
        Either the target path for the equity plot or a directory in which the
        default filenames will be written.
    bootstrap_output
        Optional explicit path for the bootstrap histogram PNG. Defaults to
        ``<artifacts_dir>/bootstrap_hist.png``.
    metrics_path
        Optional metrics.json providing additional annotations.
    title
        Optional title for the plots.
    """
    equity_df = pd.read_csv(equity_csv)
    if "equity" not in equity_df.columns:
        raise ValueError("equity_curve.csv must include an 'equity' column.")

    ts = (
        pd.to_datetime(equity_df["timestamp"])
        if "timestamp" in equity_df.columns
        else pd.RangeIndex(len(equity_df))
    )
    equity = pd.Series(equity_df["equity"].to_numpy(dtype=float), index=ts)
    drawdown = _compute_drawdown(equity)

    metrics = _load_metrics(_ensure_path(metrics_path))
    bootstrap_samples = _load_bootstrap(_ensure_path(bootstrap_json))

    base_path = Path(output_path)
    if base_path.suffix.lower() == ".png":
        equity_path = base_path
        artifacts_dir = equity_path.parent
    else:
        artifacts_dir = base_path
        equity_path = artifacts_dir / DEFAULT_EQUITY_NAME

    bootstrap_path = (
        Path(bootstrap_output)
        if bootstrap_output is not None
        else artifacts_dir / DEFAULT_BOOTSTRAP_NAME
    )

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    equity_path.parent.mkdir(parents=True, exist_ok=True)
    bootstrap_path.parent.mkdir(parents=True, exist_ok=True)

    title = title or DEFAULT_TITLE

    fig_equity, axes = plt.subplots(
        2,
        1,
        figsize=(10, 6),
        sharex=True,
        gridspec_kw={"height_ratios": [1.2, 0.8], "hspace": 0.15},
    )
    axes[0].plot(equity.index, equity.values, color="tab:blue", linewidth=1.5)
    axes[0].set_title(title)
    axes[0].set_ylabel("Equity")
    axes[0].grid(True, alpha=0.2, linestyle=":")

    sharpe = metrics.get("sharpe_ratio")
    drawdown_pct = metrics.get("max_drawdown")
    ann_vol = metrics.get("ann_vol")
    hac_lags = metrics.get("sharpe_hac_lags")

    lines: list[str] = []
    if sharpe is not None:
        lines.append(f"Sharpe: {sharpe:.2f}")
    if drawdown_pct is not None:
        lines.append(f"Max DD: {drawdown_pct * 100:.1f}%")
    if ann_vol is not None:
        lines.append(f"Ann. Vol: {ann_vol * 100:.1f}%")
    if hac_lags and hac_lags > 0:
        lines.append(f"HAC Lags: {int(hac_lags)}")
    if lines:
        axes[0].text(
            0.02,
            0.98,
            "\n".join(lines),
            transform=axes[0].transAxes,
            va="top",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
        )

    axes[1].fill_between(
        drawdown.index,
        drawdown.values,
        0.0,
        color="tab:red",
        alpha=0.3,
    )
    axes[1].set_ylabel("Drawdown")
    axes[1].set_xlabel("Date")
    axes[1].grid(True, alpha=0.2, linestyle=":")

    fig_equity.tight_layout()
    fig_equity.savefig(equity_path, dpi=200)
    plt.close(fig_equity)

    fig_hist, ax_hist = plt.subplots(figsize=(10, 4))
    if bootstrap_samples:
        ax_hist.hist(
            bootstrap_samples,
            bins=min(50, max(10, len(bootstrap_samples) // 20)),
            color="tab:green",
            alpha=0.8,
        )
        ax_hist.set_xlabel("Bootstrapped Sharpe")
        ax_hist.set_ylabel("Frequency")
        p_value = metrics.get("reality_check_p_value") or metrics.get("bootstrap_p_value")
        mean = float(np.mean(bootstrap_samples))
        std = float(np.std(bootstrap_samples))
        textbox = [
            f"Samples: {len(bootstrap_samples)}",
            f"Mean Sharpe: {mean:.2f}",
            f"Std: {std:.2f}",
        ]
        if p_value is not None:
            textbox.append(f"p-value: {float(p_value):.3f}")
        ax_hist.text(
            0.98,
            0.95,
            "\n".join(textbox),
            transform=ax_hist.transAxes,
            va="top",
            ha="right",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.85),
        )
    else:
        ax_hist.set_axis_off()
        ax_hist.text(
            0.5,
            0.5,
            "Bootstrap distribution unavailable.",
            ha="center",
            va="center",
            fontsize=12,
        )

    fig_hist.tight_layout()
    fig_hist.savefig(bootstrap_path, dpi=200)
    plt.close(fig_hist)

    return {"equity_curve": equity_path.resolve(), "bootstrap_hist": bootstrap_path.resolve()}


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("equity_csv", help="Path to equity_curve.csv")
    parser.add_argument("--bootstrap", help="Path to bootstrap.json")
    parser.add_argument("--metrics", help="Path to metrics.json")
    parser.add_argument("--output", required=True, help="Output PNG file path")
    parser.add_argument(
        "--bootstrap-output",
        default=None,
        help="Optional override for bootstrap histogram PNG path",
    )
    parser.add_argument("--title", default=None, help="Optional custom title")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    outputs = render_tearsheet(
        equity_csv=args.equity_csv,
        bootstrap_json=args.bootstrap,
        output_path=args.output,
        bootstrap_output=args.bootstrap_output,
        metrics_path=args.metrics,
        title=args.title,
    )
    print(
        "\n".join(
            [
                f"Equity curve plot written to {outputs['equity_curve']}",
                f"Bootstrap histogram written to {outputs['bootstrap_hist']}",
            ]
        )
    )


__all__ = [
    "render_tearsheet",
    "main",
    "DEFAULT_EQUITY_NAME",
    "DEFAULT_BOOTSTRAP_NAME",
]
