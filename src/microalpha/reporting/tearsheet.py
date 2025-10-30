"""Render an equity + bootstrap tearsheet for Microalpha runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DEFAULT_TITLE = "Microalpha Flagship Performance"


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
    metrics_path: str | Path | None = None,
    title: str | None = None,
) -> Path:
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

    title = title or DEFAULT_TITLE
    fig, axes = plt.subplots(
        3,
        1,
        figsize=(10, 8),
        sharex=False,
        gridspec_kw={"height_ratios": [1.4, 0.8, 1.0], "hspace": 0.35},
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

    axes[1].fill_between(drawdown.index, drawdown.values, 0.0, color="tab:red", alpha=0.3)
    axes[1].set_ylabel("Drawdown")
    axes[1].grid(True, alpha=0.2, linestyle=":")

    ax_hist = axes[2]
    if bootstrap_samples:
        ax_hist.hist(
            bootstrap_samples,
            bins=min(50, max(10, len(bootstrap_samples) // 20)),
            color="tab:green",
            alpha=0.8,
        )
        ax_hist.set_xlabel("Bootstrapped Sharpe")
        ax_hist.set_ylabel("Frequency")
        p_value = metrics.get("p_value")
        if p_value is None and isinstance(bootstrap_json, (str, Path)):
            payload = json.loads(Path(bootstrap_json).read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                p_value = payload.get("p_value")
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

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("equity_csv", help="Path to equity_curve.csv")
    parser.add_argument("--bootstrap", help="Path to bootstrap.json")
    parser.add_argument("--metrics", help="Path to metrics.json")
    parser.add_argument("--output", required=True, help="Output PNG file path")
    parser.add_argument("--title", default=None, help="Optional custom title")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    render_tearsheet(
        equity_csv=args.equity_csv,
        bootstrap_json=args.bootstrap,
        output_path=args.output,
        metrics_path=args.metrics,
        title=args.title,
    )
    print(f"Tearsheet written to {Path(args.output).resolve()}")


__all__ = ["render_tearsheet", "main"]
