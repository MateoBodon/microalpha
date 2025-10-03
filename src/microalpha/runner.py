"""High-level execution helpers for single backtests."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import hashlib
import json
import shutil

import numpy as np
import yaml

import pandas as pd

from .broker import SimulatedBroker
from .config import parse_config
from .data import CsvDataHandler
from .engine import Engine
from .manifest import build as build_manifest, write as write_manifest
from .logging import JsonlWriter
from .metrics import compute_metrics
from .portfolio import Portfolio
from .execution import Executor, KyleLambda, SquareRootImpact, TWAP, LOBExecution
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
    "lob": LOBExecution,
}


def run_from_config(config_path: str) -> Dict[str, Any]:
    """Execute a backtest described by ``config_path``."""

    cfg_path = Path(config_path).expanduser().resolve()
    with cfg_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    cfg = parse_config(config)
    cfg_bytes = yaml.safe_dump(config).encode("utf-8")
    config_hash = hashlib.sha256(cfg_bytes).hexdigest()

    run_id, artifacts_dir = prepare_artifacts_dir(cfg_path, config)
    manifest = build_manifest(cfg.seed, str(cfg_path), run_id, config_hash)
    root_rng = np.random.default_rng(manifest.seed)
    write_manifest(manifest, str(artifacts_dir))
    persist_config(cfg_path, artifacts_dir)

    data_dir = resolve_path(cfg.data_path, cfg_path)

    symbol = cfg.symbol
    initial_cash = cfg.cash

    strategy_name = cfg.strategy.name
    strategy_class = STRATEGY_MAPPING.get(strategy_name)
    if strategy_class is None:
        raise ValueError(f"Unknown strategy '{strategy_name}'")

    strategy_params: Dict[str, Any] = dict(cfg.strategy.params)
    if cfg.strategy.lookback is not None:
        strategy_params.setdefault("lookback", cfg.strategy.lookback)
    if cfg.strategy.z is not None:
        strategy_params.setdefault("z_threshold", cfg.strategy.z)

    data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    if data_handler.data is None:
        raise FileNotFoundError(f"Unable to load data for symbol '{symbol}' from {data_dir}")

    trade_logger = JsonlWriter(str(artifacts_dir / "trades.jsonl"))

    portfolio = Portfolio(
        data_handler=data_handler,
        initial_cash=initial_cash,
        max_exposure=cfg.max_exposure,
        max_drawdown_stop=cfg.max_drawdown_stop,
        turnover_cap=cfg.turnover_cap,
        kelly_fraction=cfg.kelly_fraction,
        trade_logger=trade_logger,
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
    if executor_cls is LOBExecution:
        from .lob import LimitOrderBook, LatencyModel

        latency_rng = np.random.default_rng(root_rng.integers(2**32))
        latency = LatencyModel(
            ack_fixed=cfg.exec.latency_ack or 0.001,
            ack_jitter=cfg.exec.latency_ack_jitter or 0.0005,
            fill_fixed=cfg.exec.latency_fill or 0.01,
            fill_jitter=cfg.exec.latency_fill_jitter or 0.002,
            rng=latency_rng,
        )
        book = LimitOrderBook(latency_model=latency)
        levels = cfg.exec.book_levels or 3
        level_size = cfg.exec.level_size or 200
        tick = cfg.exec.tick_size or 0.1
        if cfg.exec.mid_price is not None:
            mid_price = cfg.exec.mid_price
        else:
            try:
                mid_price = float(data_handler.full_data.iloc[0]["close"])
            except Exception:
                mid_price = 100.0
        book.seed_book(mid_price=mid_price, tick=tick, levels=levels, size=level_size)
        exec_kwargs["book"] = book

    executor = executor_cls(data_handler=data_handler, **exec_kwargs)
    broker = SimulatedBroker(executor)

    strategy = strategy_class(symbol=symbol, **strategy_params)
    engine_rng = np.random.default_rng(root_rng.integers(2**32))
    engine = Engine(data_handler, strategy, portfolio, broker, rng=engine_rng)
    engine.run()

    trade_logger.close()

    metrics = compute_metrics(portfolio.equity_curve, portfolio.total_turnover)
    metrics_paths = _persist_metrics(metrics, artifacts_dir)
    trades_path = _persist_trades(portfolio, artifacts_dir)

    result: Dict[str, Any] = asdict(manifest)
    result.update(
        {
            "run_id": run_id,
            "artifacts_dir": str(artifacts_dir),
            "strategy": strategy_name,
            "seed": cfg.seed,
            "metrics": metrics_paths,
            "trades_path": trades_path,
        }
    )
    return result


def prepare_artifacts_dir(cfg_path: Path, config: Dict[str, Any]) -> tuple[str, Path]:
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
    return run_id, candidate


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


def _persist_trades(portfolio: Portfolio, artifacts_dir: Path) -> str | None:
    if getattr(portfolio, "trade_log_path", None):
        return str(portfolio.trade_log_path)

    if not getattr(portfolio, "trades", None):
        return None

    trades_df = pd.DataFrame(portfolio.trades)
    trades_path = artifacts_dir / "trades.csv"
    trades_df.to_csv(trades_path, index=False)
    return str(trades_path)


def resolve_path(value: str, cfg_path: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    candidate = (cfg_path.parent / path).resolve()
    if candidate.exists():
        return candidate

    return (Path.cwd() / path).resolve()
