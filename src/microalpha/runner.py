"""High-level execution helpers for single backtests."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import yaml

from .broker import SimulatedBroker
from .config import parse_config
from .data import CsvDataHandler, MultiCsvDataHandler
from .engine import Engine
from .execution import TWAP, Executor, KyleLambda, LOBExecution, SquareRootImpact
from .logging import JsonlWriter
from .manifest import (
    build as build_manifest,
)
from .manifest import (
    generate_run_id,
    resolve_git_sha,
)
from .manifest import (
    write as write_manifest,
)
from .metrics import compute_metrics
from .portfolio import Portfolio
from .strategies.breakout import BreakoutStrategy
from .strategies.meanrev import MeanReversionStrategy
from .strategies.mm import NaiveMarketMakingStrategy
from .strategies.cs_momentum import CrossSectionalMomentum

STRATEGY_MAPPING = {
    "MeanReversionStrategy": MeanReversionStrategy,
    "BreakoutStrategy": BreakoutStrategy,
    "NaiveMarketMakingStrategy": NaiveMarketMakingStrategy,
    "CrossSectionalMomentum": CrossSectionalMomentum,
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


def run_from_config(config_path: str, override_artifacts_dir: str | None = None) -> Dict[str, Any]:
    """Execute a backtest described by ``config_path``."""

    cfg_path = Path(config_path).expanduser().resolve()
    with cfg_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    cfg = parse_config(config)
    cfg_bytes = yaml.safe_dump(config).encode("utf-8")
    config_hash = hashlib.sha256(cfg_bytes).hexdigest()

    full_sha, short_sha = resolve_git_sha()
    base_run_id = generate_run_id(short_sha)
    # Allow CLI override of artifacts root directory without mutating on-disk config
    if override_artifacts_dir is not None:
        config = dict(config)
        config["artifacts_dir"] = override_artifacts_dir

    run_id, artifacts_dir = prepare_artifacts_dir(cfg_path, config, base_run_id)
    manifest = build_manifest(
        cfg.seed,
        str(cfg_path),
        run_id,
        config_hash,
        git_sha=full_sha,
    )
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

    # Multi-asset support (if config strategy expects symbols list)
    if strategy_name == "CrossSectionalMomentum":
        symbols = strategy_params.get("symbols") or config.get("symbols") or [symbol]
        strategy_params["symbols"] = symbols
        data_handler = MultiCsvDataHandler(csv_dir=data_dir, symbols=symbols)
    else:
        data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    if data_handler.data is None:
        raise FileNotFoundError(
            f"Unable to load data for symbol '{symbol}' from {data_dir}"
        )

    trade_logger = JsonlWriter(str(artifacts_dir / "trades.jsonl"))

    portfolio = Portfolio(
        data_handler=data_handler,
        initial_cash=initial_cash,
        max_exposure=cfg.max_exposure,
        max_drawdown_stop=cfg.max_drawdown_stop,
        turnover_cap=cfg.turnover_cap,
        kelly_fraction=cfg.kelly_fraction,
        trade_logger=trade_logger,
        vol_target_annualized=cfg.vol_target_annualized,
        vol_lookback=cfg.vol_lookback,
        max_portfolio_heat=cfg.max_portfolio_heat,
        sectors=getattr(cfg, "sectors", None),
        max_positions_per_sector=cfg.max_positions_per_sector,
    )
    exec_type = cfg.exec.type.lower() if cfg.exec.type else "instant"
    executor_cls = EXECUTION_MAPPING.get(exec_type, Executor)
    exec_kwargs: Dict[str, Any] = {
        "price_impact": cfg.exec.price_impact,
        "commission": cfg.exec.commission,
    }
    if executor_cls is KyleLambda:
        exec_kwargs["lam"] = (
            cfg.exec.lam if cfg.exec.lam is not None else cfg.exec.price_impact
        )
    if executor_cls is TWAP and cfg.exec.slices:
        exec_kwargs["slices"] = cfg.exec.slices
    if executor_cls is LOBExecution:
        from .lob import LatencyModel, LimitOrderBook

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
        mid_price = cfg.exec.mid_price
        if mid_price is None:
            full_data = getattr(data_handler, "full_data", None)
            if isinstance(full_data, pd.DataFrame) and not full_data.empty:
                mid_price = float(full_data.iloc[0]["close"])
            else:
                mid_price = 100.0
        book.seed_book(mid_price=mid_price, tick=tick, levels=levels, size=level_size)
        exec_kwargs["book"] = book
        if cfg.exec.lob_tplus1 is not None:
            exec_kwargs["lob_tplus1"] = bool(cfg.exec.lob_tplus1)

    executor = executor_cls(data_handler=data_handler, **exec_kwargs)
    broker = SimulatedBroker(executor)

    if strategy_name == "CrossSectionalMomentum":
        strategy = strategy_class(**strategy_params)
    else:
        strategy = strategy_class(symbol=symbol, **strategy_params)
    engine_rng = np.random.default_rng(root_rng.integers(2**32))
    # Hint engine where to place profiling outputs for this run
    import os as _os
    _os.environ["MICROALPHA_ARTIFACTS_DIR"] = str(artifacts_dir)

    engine = Engine(data_handler, strategy, portfolio, broker, rng=engine_rng)
    engine.run()

    trade_logger.close()

    metrics = compute_metrics(
        portfolio.equity_curve,
        portfolio.total_turnover,
        trades=getattr(portfolio, "trades", None),
    )
    metrics_paths = _persist_metrics(metrics, artifacts_dir)
    trades_path = _persist_trades(portfolio, artifacts_dir)

    result: Dict[str, Any] = asdict(manifest)
    result.update(
        {
            "artifacts_dir": str(artifacts_dir),
            "strategy": strategy_name,
            "seed": cfg.seed,
            "metrics": metrics_paths,
            "trades_path": trades_path,
        }
    )
    return result


def prepare_artifacts_dir(
    cfg_path: Path, config: Dict[str, Any], base_run_id: str
) -> tuple[str, Path]:
    root = Path(config.get("artifacts_dir", "artifacts"))
    if not root.is_absolute():
        root = (Path.cwd() / root).resolve()

    root.mkdir(parents=True, exist_ok=True)

    candidate_run_id = base_run_id
    candidate = root / candidate_run_id
    suffix = 1
    while candidate.exists():
        candidate_run_id = f"{base_run_id}-{suffix:02d}"
        candidate = root / candidate_run_id
        suffix += 1

    candidate.mkdir()
    return candidate_run_id, candidate


def persist_config(cfg_path: Path, artifacts_dir: Path) -> None:
    destination = artifacts_dir / cfg_path.name
    shutil.copy2(cfg_path, destination)


def _persist_metrics(metrics: Dict[str, Any], artifacts_dir: Path) -> Dict[str, Any]:
    metrics_copy = dict(metrics)
    df = metrics_copy.pop("equity_df")
    equity_path = artifacts_dir / "equity_curve.csv"
    df.to_csv(equity_path, index=False)

    metrics_path = artifacts_dir / "metrics.json"
    stable_metrics = _stable_metrics(metrics_copy)
    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(stable_metrics, handle, indent=2)

    manifest_metrics = stable_metrics.copy()
    manifest_metrics["equity_curve_path"] = str(equity_path)
    manifest_metrics["metrics_path"] = str(metrics_path)
    return manifest_metrics


def _stable_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    disallowed = {"run_id", "timestamp", "artifacts_dir", "config_path"}
    return {key: value for key, value in metrics.items() if key not in disallowed}


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
