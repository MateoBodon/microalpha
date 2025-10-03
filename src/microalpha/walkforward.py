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
from .manifest import build as build_manifest, write as write_manifest
from .portfolio import Portfolio
from .risk import create_drawdowns, create_sharpe_ratio
from .runner import persist_config, prepare_artifacts_dir, resolve_path
from .strategies.breakout import BreakoutStrategy
from .strategies.meanrev import MeanReversionStrategy
from .strategies.mm import NaiveMarketMakingStrategy


STRATEGY_MAPPING = {
    "MeanReversionStrategy": MeanReversionStrategy,
    "BreakoutStrategy": BreakoutStrategy,
    "NaiveMarketMakingStrategy": NaiveMarketMakingStrategy,
}


def run_walk_forward(config_path: str) -> Dict[str, Any]:
    """Execute walk-forward validation described by ``config_path``."""

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

    window = wf_cfg
    training_days = int(window["training_days"])
    testing_days = int(window["testing_days"])
    start_date = pd.Timestamp(window["start"])
    end_date = pd.Timestamp(window["end"])

    data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    if data_handler.data is None:
        raise FileNotFoundError(f"Unable to load data for symbol '{symbol}' from {data_dir}")

    equity_records: List[Dict[str, Any]] = []
    folds: List[Dict[str, Any]] = []
    total_turnover = 0.0

    current_date = start_date
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
        portfolio = Portfolio(data_handler=data_handler, initial_cash=initial_cash)
        broker = SimulatedBroker(
            data_handler=data_handler,
            execution_style=broker_cfg.get("execution_style", "INSTANT"),
            num_ticks=broker_cfg.get("num_ticks", 4),
        )
        engine = Engine(data_handler, strategy, portfolio, broker)
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
) -> Tuple[Dict[str, Any], float]:
    best_params: Dict[str, Any] | None = None
    best_sharpe = float("-inf")

    keys = list(param_grid.keys())
    values = [param_grid[key] for key in keys]

    for combination in product(*values):
        params = dict(zip(keys, combination))

        data_handler.set_date_range(train_start, train_end)
        strategy = strategy_class(symbol=symbol, **params)
        portfolio = Portfolio(data_handler=data_handler, initial_cash=initial_cash)
        broker = SimulatedBroker(
            data_handler=data_handler,
            execution_style=broker_cfg.get("execution_style", "INSTANT"),
            num_ticks=broker_cfg.get("num_ticks", 4),
        )

        engine = Engine(data_handler, strategy, portfolio, broker)
        engine.run()

        if not portfolio.equity_curve:
            continue

        equity_df = pd.DataFrame(portfolio.equity_curve).set_index("timestamp")
        equity_df["returns"] = equity_df["equity"].pct_change().fillna(0.0)
        sharpe = create_sharpe_ratio(equity_df["returns"])

        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = params

    if best_params is None:
        return {}, best_sharpe

    return best_params, best_sharpe


def _collect_warmup_prices(
    data_handler: CsvDataHandler, train_end: pd.Timestamp, lookback: int
) -> List[float]:
    if lookback <= 0:
        return []

    warmup_start = train_end - pd.Timedelta(days=lookback)
    data_handler.set_date_range(warmup_start, train_end)
    return [event.price for event in data_handler.stream_events()]


def _summarise_walkforward(
    equity_records: List[Dict[str, Any]],
    artifacts_dir: Path,
    total_turnover: float,
) -> Dict[str, Any]:
    if not equity_records:
        metrics = {
            "equity_curve_path": None,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "total_turnover": float(total_turnover),
            "avg_exposure": 0.0,
            "final_equity": 0.0,
        }
        metrics_path = artifacts_dir / "metrics.json"
        with metrics_path.open("w", encoding="utf-8") as handle:
            json.dump(metrics, handle, indent=2)
        metrics["metrics_path"] = str(metrics_path)
        return metrics

    equity_df = pd.DataFrame(equity_records).drop_duplicates("timestamp")
    equity_df = equity_df.set_index("timestamp").sort_index()

    equity_path = artifacts_dir / "walk_forward_equity.csv"
    equity_df.to_csv(equity_path)

    equity_df["returns"] = equity_df["equity"].pct_change().fillna(0.0)
    sharpe = float(create_sharpe_ratio(equity_df["returns"]))
    _, max_dd = create_drawdowns(equity_df["equity"])

    avg_exposure = float(equity_df["exposure"].mean())

    metrics = {
        "equity_curve_path": str(equity_path),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": float(max_dd),
        "total_turnover": float(total_turnover),
        "avg_exposure": avg_exposure,
        "final_equity": float(equity_df["equity"].iloc[-1]),
    }

    metrics_path = artifacts_dir / "metrics.json"
    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

    metrics["metrics_path"] = str(metrics_path)
    return metrics
