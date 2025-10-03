#!/usr/bin/env python3
"""Visualise realized spread versus inventory for different execution modes."""

from __future__ import annotations

import copy
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import yaml

from microalpha.runner import run_from_config


config_path = Path("configs/mm.yaml").resolve()


def run_variant(cfg: dict, exec_type: str, workdir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    variant = copy.deepcopy(cfg)
    variant["exec"]["type"] = exec_type
    if exec_type != "lob":
        for key in ["book_levels", "level_size", "tick_size", "mid_price", "latency_ack", "latency_ack_jitter", "latency_fill", "latency_fill_jitter"]:
            variant["exec"].pop(key, None)
    data_path = Path(variant["data_path"])
    if not data_path.is_absolute():
        variant["data_path"] = str((config_path.parent / data_path).resolve())
    artifacts_dir = workdir / exec_type
    variant["artifacts_dir"] = str(artifacts_dir)
    cfg_path = workdir / f"mm_{exec_type}.yaml"
    cfg_path.write_text(yaml.safe_dump(variant, sort_keys=False))

    result = run_from_config(str(cfg_path))
    trades = pd.read_csv(result["trades_path"]) if result.get("trades_path") else pd.DataFrame()
    equity = pd.read_csv(result["metrics"]["equity_curve_path"]) if result.get("metrics") else pd.DataFrame()
    return trades, equity


def compute_realized_spread(trades: pd.DataFrame, mid_price: float = 100.0) -> pd.DataFrame:
    if trades.empty:
        return trades
    trades = trades.copy()
    trades["inventory"] = trades["qty"].cumsum()
    trades["realized_spread"] = trades["price"] - mid_price
    return trades


def main() -> None:
    base_cfg = yaml.safe_load(config_path.read_text())
    workdir = Path("artifacts/mm_demo")
    workdir.mkdir(parents=True, exist_ok=True)

    scenarios = {}
    for exec_type in ("lob", "twap"):
        trades, _ = run_variant(base_cfg, exec_type, workdir)
        scenarios[exec_type.upper()] = compute_realized_spread(trades, mid_price=base_cfg.get("exec", {}).get("mid_price", 100.0))

    fig, ax = plt.subplots(figsize=(8, 5))
    for label, df in scenarios.items():
        if df.empty:
            continue
        ax.plot(df["inventory"], df["realized_spread"], marker="o", label=label)

    ax.set_title("Realized Spread vs Inventory")
    ax.set_xlabel("Inventory (shares)")
    ax.set_ylabel("Realized Spread ($)")
    ax.legend()
    fig.tight_layout()
    output = workdir / "mm_spread.png"
    fig.savefig(output, dpi=200)
    print(f"Saved plot to {output}")


if __name__ == "__main__":
    main()
