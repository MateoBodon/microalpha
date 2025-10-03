"""High-level execution helpers for single backtests."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import json
import shutil

import pandas as pd
import yaml

from .broker import SimulatedBroker
from .config import parse_config
from .data import CsvDataHandler
from .engine import Engine
from .manifest import build as build_manifest, write as write_manifest
from .portfolio import Portfolio
from .risk import create_drawdowns, create_sharpe_ratio
from .slippage import VolumeSlippageModel
from .strategies.breakout import BreakoutStrategy
from .strategies.meanrev import MeanReversionStrategy
from .strategies.mm import NaiveMarketMakingStrategy


STRATEGY_MAPPING = {
    "MeanReversionStrategy": MeanReversionStrategy,
    "BreakoutStrategy": BreakoutStrategy,
    "NaiveMarketMakingStrategy": NaiveMarketMakingStrategy,
}


def run_from_config(config_path: str) -> Dict[str, Any]:
    """Execute a backtest described by ``config_path``."""

    cfg_path = Path(config_path).expanduser().resolve()
    with cfg_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    cfg = parse_config(config)
    manifest = build_manifest(cfg.seed, str(cfg_path))

    artifacts_dir = prepare_artifacts_dir(cfg_path, config)
    write_manifest(manifest, str(artifacts_dir))
    persist_config(cfg_path, artifacts_dir)

    data_dir = resolve_path(cfg.data_path, cfg_path)

    symbol = cfg.symbol
    initial_cash = cfg.cash

    strategy_name = cfg.strategy.name
    strategy_class = STRATEGY_MAPPING.get(strategy_name)
    if strategy_class is None:
        raise ValueError(f"Unknown strategy '{strategy_name}'")

    strategy_params: Dict[str, Any] = {"lookback": cfg.strategy.lookback}
    if cfg.strategy.z is not None:
        strategy_params["z_threshold"] = cfg.strategy.z

    data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    if data_handler.data is None:
        raise FileNotFoundError(f"Unable to load data for symbol '{symbol}' from {data_dir}")

    portfolio = Portfolio(data_handler=data_handler, initial_cash=initial_cash)
    slippage_model = VolumeSlippageModel(price_impact=cfg.exec.price_impact)
    broker = SimulatedBroker(
        data_handler=data_handler,
        commission=cfg.exec.aln,
        slippage_model=slippage_model,
        mode=cfg.exec.type,
    )

    strategy = strategy_class(symbol=symbol, **strategy_params)
    engine = Engine(data_handler, strategy, portfolio, broker, seed=cfg.seed)
    engine.run()

    metrics = _collect_metrics(portfolio, artifacts_dir)

    result: Dict[str, Any] = asdict(manifest)
    result.update({
        "artifacts_dir": str(artifacts_dir),
        "strategy": strategy_name,
        "seed": cfg.seed,
        "metrics": metrics,
    })
    return result


def prepare_artifacts_dir(cfg_path: Path, config: Dict[str, Any]) -> Path:
    root = Path(config.get("artifacts_dir", "artifacts"))
    if not root.is_absolute():
        root = (Path.cwd() / root).resolve()

    root.mkdir(parents=True, exist_ok=True)

    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    candidate = root / run_id
    suffix = 1
    while candidate.exists():
        candidate = root / f"{run_id}-{suffix:02d}"
        suffix += 1

    candidate.mkdir()
    return candidate


def persist_config(cfg_path: Path, artifacts_dir: Path) -> None:
    destination = artifacts_dir / cfg_path.name
    shutil.copy2(cfg_path, destination)


def _collect_metrics(portfolio: Portfolio, artifacts_dir: Path) -> Dict[str, Any]:
    if not portfolio.equity_curve:
        return {
            "equity_curve_path": None,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "total_turnover": float(portfolio.total_turnover),
            "avg_exposure": 0.0,
        }

    equity_df = pd.DataFrame(portfolio.equity_curve).drop_duplicates("timestamp")
    equity_df = equity_df.set_index("timestamp").sort_index()

    equity_path = artifacts_dir / "equity_curve.csv"
    equity_df.to_csv(equity_path)

    equity_df["returns"] = equity_df["equity"].pct_change().fillna(0.0)
    sharpe = float(create_sharpe_ratio(equity_df["returns"]))
    _, max_dd = create_drawdowns(equity_df["equity"])

    metrics = {
        "equity_curve_path": str(equity_path),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": float(max_dd),
        "total_turnover": float(portfolio.total_turnover),
        "avg_exposure": float(equity_df["exposure"].mean()),
        "final_equity": float(equity_df["equity"].iloc[-1]),
    }

    metrics_path = artifacts_dir / "metrics.json"
    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

    metrics["metrics_path"] = str(metrics_path)
    return metrics


def resolve_path(value: str, cfg_path: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    candidate = (cfg_path.parent / path).resolve()
    if candidate.exists():
        return candidate

    return (Path.cwd() / path).resolve()
