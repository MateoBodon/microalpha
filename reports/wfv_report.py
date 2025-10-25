"""Render a fold-level WFV report (Sharpe per fold and parameter heat)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np


def _load_folds(path: Path) -> List[Dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_wfv_report(folds_path: str) -> plt.Figure:
    folds = _load_folds(Path(folds_path))
    if not folds:
        raise ValueError("No folds found")

    test_sharpes = [f.get("test_metrics", {}).get("sharpe_ratio", 0.0) for f in folds]
    train_sharpes = [f.get("train_metrics", {}).get("sharpe_ratio", 0.0) for f in folds]
    labels = [f"{i+1}" for i in range(len(folds))]

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=False)

    # Bar plot of Sharpe per fold (train vs test)
    x = np.arange(len(folds))
    width = 0.35
    axes[0].bar(x - width / 2, train_sharpes, width, label="Train", color="#1f77b4", alpha=0.7)
    axes[0].bar(x + width / 2, test_sharpes, width, label="Test", color="#d62728", alpha=0.7)
    axes[0].set_xticks(x, labels)
    axes[0].set_ylabel("Sharpe")
    axes[0].set_title("Per-Fold Sharpe (Train vs Test)")
    axes[0].legend()

    # Parameter scatter (top two params if present)
    params_list = [f.get("best_params", {}) or {} for f in folds]
    unique_keys = list({k for p in params_list for k in p.keys()})
    if len(unique_keys) >= 2:
        kx, ky = unique_keys[:2]
        xs = [p.get(kx) for p in params_list]
        ys = [p.get(ky) for p in params_list]
        c = test_sharpes
        sc = axes[1].scatter(xs, ys, c=c, cmap="viridis", s=60)
        axes[1].set_xlabel(kx)
        axes[1].set_ylabel(ky)
        axes[1].set_title("Best Params Colored by Test Sharpe")
        fig.colorbar(sc, ax=axes[1], label="Test Sharpe")
    else:
        axes[1].axis("off")
        axes[1].text(0.5, 0.5, "Params not available", ha="center", va="center")

    fig.tight_layout()
    return fig


def main() -> None:
    ap = argparse.ArgumentParser(description="Render a WFV fold report")
    ap.add_argument("folds_json", help="Path to folds.json")
    ap.add_argument("--output", help="Optional output file for saving the figure")
    args = ap.parse_args()

    fig = build_wfv_report(args.folds_json)
    if args.output:
        fig.savefig(args.output, dpi=200, bbox_inches="tight")
    else:
        plt.show()


if __name__ == "__main__":
    main()


