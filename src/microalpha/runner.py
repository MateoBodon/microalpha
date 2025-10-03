"""High-level execution helpers for single backtests."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import json
import shutil

import yaml

from .broker import SimulatedBroker
from .config import parse_config
from .data import CsvDataHandler
from .engine import Engine
from .manifest import build as build_manifest, write as write_manifest
from .metrics import compute_metrics
from .portfolio import Portfolio
from .execution import Executor, KyleLambda, SquareRootImpact, TWAP
from .strategies.breakout import BreakoutStrategy
from .strategies.meanrev import MeanReversionStrategy
from .strategies.mm import NaiveMarketMakingStrategy


STRATEGY_MAPPING = {
    "MeanReversionStrategy": MeanReversionStrategy,
    "BreakoutStrategy": BreakoutStrategy,
    "NaiveMarketMakingStrategy": NaiveMarketMakingStrategy,
}

EXECUTION_MAPPING = {
    "instant": Executor,
    "linear": Executor,
    "twap": TWAP,
    "sqrt": SquareRootImpact,
    "squareroot": SquareRootImpact,
    "kyle": KyleLambda,
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

    portfolio = Portfolio(
        data_handler=data_handler,
        initial_cash=initial_cash,
        max_exposure=cfg.max_exposure,
        max_drawdown_stop=cfg.max_drawdown_stop,
        turnover_cap=cfg.turnover_cap,
        kelly_fraction=cfg.kelly_fraction,
    )
    exec_type = cfg.exec.type.lower() if cfg.exec.type else "instant"
    executor_cls = EXECUTION_MAPPING.get(exec_type, Executor)
    exec_kwargs: Dict[str, Any] = {
        "price_impact": cfg.exec.price_impact,
        "commission": cfg.exec.aln,
    }
    if executor_cls is KyleLambda:
        exec_kwargs["lam"] = cfg.exec.lam if cfg.exec.lam is not None else cfg.exec.price_impact
    if executor_cls is TWAP and cfg.exec.slices:
        exec_kwargs["slices"] = cfg.exec.slices
    executor = executor_cls(data_handler=data_handler, **exec_kwargs)
    broker = SimulatedBroker(executor)

    strategy = strategy_class(symbol=symbol, **strategy_params)
    engine = Engine(data_handler, strategy, portfolio, broker, seed=cfg.seed)
    engine.run()

    metrics = compute_metrics(portfolio.equity_curve, portfolio.total_turnover)
    metrics_paths = _persist_metrics(metrics, artifacts_dir)

    result: Dict[str, Any] = asdict(manifest)
    result.update(
        {
            "artifacts_dir": str(artifacts_dir),
            "strategy": strategy_name,
            "seed": cfg.seed,
            "metrics": metrics_paths,
        }
    )
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


def _persist_metrics(metrics: Dict[str, Any], artifacts_dir: Path) -> Dict[str, Any]:
    df = metrics.pop("equity_df")
    equity_path = artifacts_dir / "equity_curve.csv"
    df.to_csv(equity_path)

    metrics["equity_curve_path"] = str(equity_path)
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
