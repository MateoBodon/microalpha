"""Walk-forward validation orchestration."""

from __future__ import annotations

from dataclasses import asdict
from itertools import product
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import json
import math

import pandas as pd
import yaml

from .broker import SimulatedBroker
from .data import CsvDataHandler
from .engine import Engine
from .execution import Executor, KyleLambda, SquareRootImpact, TWAP
from .manifest import build as build_manifest, write as write_manifest
from .metrics import compute_metrics
from .portfolio import Portfolio
from .runner import persist_config, prepare_artifacts_dir, resolve_path
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


def run_walk_forward(config_path: str) -> Dict[str, Any]:
    cfg_path = Path(config_path).expanduser().resolve()
    with cfg_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    manifest = build_manifest(config.get("random_seed"), str(cfg_path))
    artifacts_dir = prepare_artifacts_dir(cfg_path, config)
    write_manifest(manifest, str(artifacts_dir))
    persist_config(cfg_path, artifacts_dir)

    data_cfg = config["data"]
    wf_cfg = config["walkforward"]
    strategy_cfg = config["strategy"]
    broker_cfg = config.get("broker_settings", {})
    portfolio_cfg = config.get("portfolio", {})

    data_dir = resolve_path(data_cfg["directory"], cfg_path)

    symbol = data_cfg["symbol"]
    initial_cash = portfolio_cfg.get("initial_cash", 100000.0)

    strategy_name = strategy_cfg["name"]
    strategy_class = STRATEGY_MAPPING.get(strategy_name)
    if strategy_class is None:
        raise ValueError(f"Unknown strategy '{strategy_name}'")

    param_grid = strategy_cfg.get("param_grid", {})
    if not param_grid:
        raise ValueError("Parameter grid is required for walk-forward validation")

    training_days = int(wf_cfg["training_days"])
    testing_days = int(wf_cfg["testing_days"])
    start_date = pd.Timestamp(wf_cfg["start"])
    end_date = pd.Timestamp(wf_cfg["end"])

    data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    if data_handler.data is None:
        raise FileNotFoundError(f"Unable to load data for symbol '{symbol}' from {data_dir}")

    equity_records: List[Dict[str, Any]] = []
    folds: List[Dict[str, Any]] = []
    total_turnover = 0.0

    current_date = start_date
    seed = config.get("random_seed", 42)

    while current_date + pd.Timedelta(days=training_days + testing_days) <= end_date:
        train_start = current_date
        train_end = train_start + pd.Timedelta(days=training_days)
        test_start = train_end + pd.Timedelta(days=1)
        test_end = test_start + pd.Timedelta(days=testing_days)

        best_params, best_sharpe = _optimise_parameters(
            data_handler,
            train_start,
            train_end,
            strategy_class,
            param_grid,
            symbol,
            initial_cash,
            broker_cfg,
            portfolio_cfg,
            seed,
        )

        if not best_params:
            folds.append(
                {
                    "train_start": str(train_start.date()),
                    "train_end": str(train_end.date()),
                    "test_start": str(test_start.date()),
                    "test_end": str(test_end.date()),
                    "best_params": None,
                    "best_sharpe": None,
                }
            )
            current_date += pd.Timedelta(days=testing_days)
            continue

        warmup_prices = _collect_warmup_prices(
            data_handler, train_end, best_params.get("lookback", 0)
        )

        data_handler.set_date_range(test_start, test_end)
        strategy = strategy_class(
            symbol=symbol, warmup_prices=warmup_prices, **best_params
        )
        portfolio = _build_portfolio(data_handler, initial_cash, portfolio_cfg)
        executor = _build_executor(data_handler, broker_cfg)
        broker = SimulatedBroker(executor)
        engine = Engine(data_handler, strategy, portfolio, broker, seed=seed)
        engine.run()

        if portfolio.equity_curve:
            equity_records.extend(portfolio.equity_curve)
        total_turnover += float(portfolio.total_turnover)

        folds.append(
            {
                "train_start": str(train_start.date()),
                "train_end": str(train_end.date()),
                "test_start": str(test_start.date()),
                "test_end": str(test_end.date()),
                "best_params": best_params,
                "best_sharpe": round(float(best_sharpe), 4)
                if best_sharpe is not None and math.isfinite(best_sharpe)
                else None,
            }
        )

        current_date += pd.Timedelta(days=testing_days)

    folds_path = artifacts_dir / "folds.json"
    with folds_path.open("w", encoding="utf-8") as handle:
        json.dump(folds, handle, indent=2)

    metrics = _summarise_walkforward(equity_records, artifacts_dir, total_turnover)

    result: Dict[str, Any] = asdict(manifest)
    result.update(
        {
            "artifacts_dir": str(artifacts_dir),
            "strategy": strategy_name,
            "folds_path": str(folds_path),
            "metrics": metrics,
        }
    )
    return result


def _optimise_parameters(
    data_handler: CsvDataHandler,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    strategy_class,
    param_grid: Dict[str, Iterable[Any]],
    symbol: str,
    initial_cash: float,
    broker_cfg: Dict[str, Any],
    portfolio_cfg: Dict[str, Any],
    seed: int,
) -> Tuple[Dict[str, Any], float]:
    best_params: Dict[str, Any] | None = None
    best_sharpe = float("-inf")

    keys = list(param_grid.keys())
    values = [param_grid[key] for key in keys]

    for combination in product(*values):
        params = dict(zip(keys, combination))

        data_handler.set_date_range(train_start, train_end)
        strategy = strategy_class(symbol=symbol, **params)
        portfolio = _build_portfolio(data_handler, initial_cash, portfolio_cfg)
        executor = _build_executor(data_handler, broker_cfg)
        broker = SimulatedBroker(executor)

        engine = Engine(data_handler, strategy, portfolio, broker, seed=seed)
        engine.run()

        if not portfolio.equity_curve:
            continue

        metrics = compute_metrics(portfolio.equity_curve, portfolio.total_turnover)
        sharpe = metrics.get("sharpe_ratio", float("-inf"))

        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = params

    if best_params is None:
        return {}, best_sharpe

    return best_params, best_sharpe


def _build_portfolio(data_handler, initial_cash: float, portfolio_cfg: Dict[str, Any]) -> Portfolio:
    return Portfolio(
        data_handler=data_handler,
        initial_cash=initial_cash,
        max_exposure=portfolio_cfg.get("max_exposure"),
        max_drawdown_stop=portfolio_cfg.get("max_drawdown_stop"),
        turnover_cap=portfolio_cfg.get("turnover_cap"),
        kelly_fraction=portfolio_cfg.get("kelly_fraction"),
    )


def _build_executor(data_handler, broker_cfg: Dict[str, Any]):
    exec_type = broker_cfg.get("mode", "twap").lower()
    executor_cls = EXECUTION_MAPPING.get(exec_type, Executor)
    kwargs = {
        "price_impact": broker_cfg.get("price_impact", 0.0),
        "commission": broker_cfg.get("commission", 0.0),
    }
    if executor_cls is KyleLambda:
        kwargs["lam"] = broker_cfg.get("lam", broker_cfg.get("price_impact", 0.0))
    if executor_cls is TWAP and broker_cfg.get("slices"):
        kwargs["slices"] = broker_cfg.get("slices")
    return executor_cls(data_handler=data_handler, **kwargs)


def _collect_warmup_prices(
    data_handler: CsvDataHandler, train_end: pd.Timestamp, lookback: int
) -> List[float]:
    if lookback <= 0:
        return []

    warmup_start = train_end - pd.Timedelta(days=lookback)
    data_handler.set_date_range(warmup_start, train_end)
    return [event.price for event in data_handler.stream()]


def _summarise_walkforward(
    equity_records: List[Dict[str, Any]],
    artifacts_dir: Path,
    total_turnover: float,
) -> Dict[str, Any]:
    metrics = compute_metrics(equity_records, total_turnover)
    df = metrics.pop("equity_df")

    if not df.empty:
        equity_path = artifacts_dir / "walk_forward_equity.csv"
        df.to_csv(equity_path)
        metrics["equity_curve_path"] = str(equity_path)
    else:
        metrics["equity_curve_path"] = None

    metrics_path = artifacts_dir / "metrics.json"
    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    metrics["metrics_path"] = str(metrics_path)
    return metrics
