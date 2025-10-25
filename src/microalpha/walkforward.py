"""Walk-forward validation orchestration."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple, cast

import numpy as np
import pandas as pd
import yaml

from .broker import SimulatedBroker
from .config import BacktestCfg, ExecModelCfg
from .config_wfv import WFVCfg
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
from .runner import persist_config, prepare_artifacts_dir, resolve_path
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


def load_wfv_cfg(path: str) -> WFVCfg:
    """Load a walk-forward validation configuration."""

    import yaml

    from .config import BacktestCfg, ExecModelCfg, StrategyCfg

    with open(path, "r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    if not isinstance(raw, dict):
        raise ValueError("Walk-forward configuration must be a mapping.")

    if "template" in raw and "walkforward" in raw:
        return WFVCfg(**raw)

    if {"data", "strategy", "walkforward"}.issubset(raw):
        data_cfg = raw["data"]
        strategy_payload = dict(raw["strategy"])
        grid = raw.get("grid") or strategy_payload.pop("param_grid", {}) or {}

        exec_payload = dict(raw.get("broker_settings") or raw.get("exec") or {})
        if "mode" in exec_payload:
            exec_payload["type"] = exec_payload.pop("mode")
        if "commission" in exec_payload:
            exec_payload["aln"] = exec_payload.pop("commission")

        portfolio_cfg = raw.get("portfolio") or {}
        data_path = data_cfg.get("directory") or data_cfg.get("path")
        if data_path is None:
            raise ValueError("Legacy walk-forward config missing data.directory/path")
        symbol = data_cfg.get("symbol")
        if symbol is None:
            raise ValueError("Legacy walk-forward config missing data.symbol")

        cash_value = portfolio_cfg.get("initial_cash", raw.get("cash", 1_000_000))
        try:
            cash = float(cash_value) if cash_value is not None else 1_000_000.0
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid cash value in walk-forward config") from exc

        seed_value = raw.get("random_seed", raw.get("seed", 42))
        try:
            seed = int(seed_value) if seed_value is not None else 42
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid seed value in walk-forward config") from exc

        template = BacktestCfg(
            data_path=data_path,
            symbol=symbol,
            cash=cash,
            exec=ExecModelCfg(**exec_payload),
            strategy=StrategyCfg(**strategy_payload),
            seed=seed,
            max_exposure=portfolio_cfg.get("max_exposure"),
            max_drawdown_stop=portfolio_cfg.get("max_drawdown_stop"),
            turnover_cap=portfolio_cfg.get("turnover_cap"),
            kelly_fraction=portfolio_cfg.get("kelly_fraction"),
        )

        return WFVCfg(
            template=template,
            walkforward=raw["walkforward"],
            grid=grid,
            artifacts_dir=raw.get("artifacts_dir"),
        )

    raise ValueError("Invalid walk-forward configuration schema.")


def run_walk_forward(config_path: str) -> Dict[str, Any]:
    cfg_path = Path(config_path).expanduser().resolve()
    raw_config = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    cfg = load_wfv_cfg(str(cfg_path))
    config_hash = hashlib.sha256(yaml.safe_dump(raw_config).encode("utf-8")).hexdigest()

    full_sha, short_sha = resolve_git_sha()
    base_run_id = generate_run_id(short_sha)
    run_id, artifacts_dir = prepare_artifacts_dir(cfg_path, raw_config, base_run_id)
    manifest = build_manifest(
        cfg.template.seed,
        str(cfg_path),
        run_id,
        config_hash,
        git_sha=full_sha,
    )
    write_manifest(manifest, str(artifacts_dir))
    persist_config(cfg_path, artifacts_dir)

    trade_logger = JsonlWriter(str(artifacts_dir / "trades.jsonl"))

    data_dir = resolve_path(cfg.template.data_path, cfg_path)
    symbol = cfg.template.symbol
    base_params = _strategy_params(cfg.template.strategy)
    param_grid: Dict[str, Sequence[Any]] = {
        key: tuple(values) for key, values in cfg.grid.items()
    }
    if not param_grid:
        raise ValueError("Parameter grid is required for walk-forward validation")

    training_days = int(cfg.walkforward.training_days)
    testing_days = int(cfg.walkforward.testing_days)
    start_date = pd.Timestamp(cfg.walkforward.start)
    end_date = pd.Timestamp(cfg.walkforward.end)

    strategy_name = cfg.template.strategy.name
    if strategy_name == "CrossSectionalMomentum":
        symbols = list(cfg.template.strategy.params.get("symbols") or [])
        if not symbols:
            # fallback: allow symbol string list under template
            symbols = list(getattr(cfg.template, "symbols", []) or [])
        if not symbols:
            symbols = [symbol]
        data_handler = MultiCsvDataHandler(csv_dir=data_dir, symbols=symbols)
    else:
        data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    if data_handler.data is None:
        raise FileNotFoundError(
            f"Unable to load data for symbol '{symbol}' from {data_dir}"
        )

    equity_records: List[Dict[str, Any]] = []
    folds: List[Dict[str, Any]] = []
    total_turnover = 0.0

    current_date = start_date
    master_rng = np.random.default_rng(cfg.template.seed)
    strategy_class = STRATEGY_MAPPING.get(strategy_name)
    if strategy_class is None:
        raise ValueError(f"Unknown strategy '{strategy_name}'")

    try:
        while (
            current_date + pd.Timedelta(days=training_days + testing_days) <= end_date
        ):
            train_start = current_date
            train_end = train_start + pd.Timedelta(days=training_days)
            test_start = train_end + pd.Timedelta(days=1)
            test_end = test_start + pd.Timedelta(days=testing_days)

            fold_rng = _spawn_rng(master_rng)
            train_rng = _spawn_rng(fold_rng)

            best_params, train_metrics, spa_pvalue = _optimise_parameters(
                data_handler,
                train_start,
                train_end,
                strategy_class,
                param_grid,
                base_params,
                cfg.template,
                train_rng,
            )

            if not best_params or not train_metrics:
                folds.append(
                    {
                        "train_start": str(train_start.date()),
                        "train_end": str(train_end.date()),
                        "test_start": str(test_start.date()),
                        "test_end": str(test_end.date()),
                        "best_params": None,
                        "train_metrics": None,
                        "test_metrics": None,
                        "spa_pvalue": None,
                    }
                )
                current_date += pd.Timedelta(days=testing_days)
                continue

            warmup_prices = _collect_warmup_prices(
                data_handler, train_end, best_params.get("lookback", 0)
            )

            data_handler.set_date_range(test_start, test_end)
            if strategy_name == "CrossSectionalMomentum":
                kwargs = _strategy_kwargs(best_params, warmup_prices)
                kwargs.pop("warmup_prices", None)
                strategy = strategy_class(**kwargs)
            else:
                strategy = strategy_class(
                    symbol=symbol, **_strategy_kwargs(best_params, warmup_prices)
                )
            portfolio = _build_portfolio(
                data_handler, cfg.template, trade_logger=trade_logger
            )
            test_rng = _spawn_rng(fold_rng)
            exec_rng = _spawn_rng(test_rng)
            executor = _build_executor(data_handler, cfg.template.exec, exec_rng)
            broker = SimulatedBroker(executor)
            engine = Engine(
                data_handler,
                strategy,
                portfolio,
                broker,
                rng=_spawn_rng(test_rng),
            )
            engine.run()

            if portfolio.equity_curve:
                equity_records.extend(portfolio.equity_curve)
            total_turnover += float(portfolio.total_turnover)

            test_metrics = compute_metrics(
                portfolio.equity_curve, portfolio.total_turnover
            )

            fold_entry = {
                "train_start": str(train_start.date()),
                "train_end": str(train_end.date()),
                "test_start": str(test_start.date()),
                "test_end": str(test_end.date()),
                "best_params": best_params,
                "train_metrics": _metrics_summary(train_metrics),
                "test_metrics": _metrics_summary(test_metrics),
                "spa_pvalue": None if spa_pvalue is None else float(spa_pvalue),
            }

            folds.append(fold_entry)

            current_date += pd.Timedelta(days=testing_days)
    finally:
        trade_logger.close()

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
            "folds": folds,
            "trades_path": str(artifacts_dir / "trades.jsonl"),
        }
    )
    return result


def _optimise_parameters(
    data_handler: CsvDataHandler,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    strategy_class,
    param_grid: Mapping[str, Sequence[Any]],
    base_params: Dict[str, Any],
    cfg: BacktestCfg,
    rng: np.random.Generator,
) -> Tuple[Dict[str, Any], Dict[str, Any] | None, float | None]:
    best_entry: Dict[str, Any] | None = None
    results: List[Dict[str, Any]] = []

    keys = list(param_grid.keys())

    for combination in product(*(param_grid[key] for key in keys)):
        params = dict(zip(keys, combination))

        sim_rng = _spawn_rng(rng)

        data_handler.set_date_range(train_start, train_end)
        combined = dict(base_params)
        combined.update(params)
        if strategy_class is CrossSectionalMomentum:
            strategy = strategy_class(**_strategy_kwargs(combined))
        else:
            strategy = strategy_class(symbol=cfg.symbol, **_strategy_kwargs(combined))
        portfolio = _build_portfolio(data_handler, cfg)
        exec_rng = _spawn_rng(sim_rng)
        executor = _build_executor(data_handler, cfg.exec, exec_rng)
        broker = SimulatedBroker(executor)

        engine = Engine(
            data_handler,
            strategy,
            portfolio,
            broker,
            rng=_spawn_rng(sim_rng),
        )
        engine.run()

        if not portfolio.equity_curve:
            continue

        metrics = compute_metrics(portfolio.equity_curve, portfolio.total_turnover)
        results.append(
            {
                "params": dict(params),
                "metrics": metrics,
                "returns": metrics.get("equity_df", pd.DataFrame())[
                    "returns"
                ].to_numpy(),
            }
        )

    if not results:
        return {}, None, None

    best_entry = max(
        results, key=lambda item: item["metrics"].get("sharpe_ratio", float("-inf"))
    )
    spa_pvalue = bootstrap_reality_check(results, seed=cfg.seed)

    params = dict(base_params)
    params.update(best_entry["params"])
    return params, best_entry["metrics"], spa_pvalue


def _build_portfolio(
    data_handler, cfg: BacktestCfg, trade_logger: JsonlWriter | None = None
) -> Portfolio:
    return Portfolio(
        data_handler=data_handler,
        initial_cash=cfg.cash,
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


def _build_executor(data_handler, exec_cfg: ExecModelCfg, rng: np.random.Generator):
    exec_type = exec_cfg.type.lower() if exec_cfg.type else "twap"
    executor_cls = EXECUTION_MAPPING.get(exec_type, Executor)
    kwargs: Dict[str, Any] = {
        "price_impact": exec_cfg.price_impact,
        "commission": exec_cfg.commission,
    }
    if executor_cls is KyleLambda:
        kwargs["lam"] = (
            exec_cfg.lam if exec_cfg.lam is not None else exec_cfg.price_impact
        )
    if executor_cls is TWAP and exec_cfg.slices:
        kwargs["slices"] = exec_cfg.slices
    if executor_cls is LOBExecution:
        from .lob import LatencyModel, LimitOrderBook

        latency = LatencyModel(
            ack_fixed=exec_cfg.latency_ack or 0.001,
            ack_jitter=exec_cfg.latency_ack_jitter or 0.0005,
            fill_fixed=exec_cfg.latency_fill or 0.01,
            fill_jitter=exec_cfg.latency_fill_jitter or 0.002,
            rng=rng,
        )
        book = LimitOrderBook(latency_model=latency)
        levels = exec_cfg.book_levels or 3
        level_size = exec_cfg.level_size or 200
        tick = exec_cfg.tick_size or 0.1
        mid_price = exec_cfg.mid_price
        if mid_price is None:
            full_data = getattr(data_handler, "full_data", None)
            if isinstance(full_data, pd.DataFrame) and not full_data.empty:
                mid_price = float(full_data.iloc[0]["close"])
            else:
                mid_price = 100.0
        book.seed_book(mid_price=mid_price, tick=tick, levels=levels, size=level_size)
        kwargs["book"] = book
        if exec_cfg.lob_tplus1 is not None:
            kwargs["lob_tplus1"] = bool(exec_cfg.lob_tplus1)
    return executor_cls(data_handler=data_handler, **kwargs)


def _spawn_rng(parent: np.random.Generator) -> np.random.Generator:
    return np.random.default_rng(int(parent.integers(2**32)))


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
    metrics_copy = dict(metrics)
    df = cast(pd.DataFrame, metrics_copy.pop("equity_df"))

    equity_path: str | None = None
    if not df.empty:
        path = artifacts_dir / "equity_curve.csv"
        df.to_csv(path, index=False)
        equity_path = str(path)

    metrics_path = artifacts_dir / "metrics.json"
    stable_metrics = _stable_metrics(metrics_copy)
    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(stable_metrics, handle, indent=2)

    manifest_metrics = stable_metrics.copy()
    manifest_metrics["equity_curve_path"] = equity_path
    manifest_metrics["metrics_path"] = str(metrics_path)
    return manifest_metrics


def _stable_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    disallowed = {"run_id", "timestamp", "artifacts_dir", "config_path"}
    return {key: value for key, value in metrics.items() if key not in disallowed}


def _metrics_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    if not metrics:
        return {}

    summary: Dict[str, Any] = {}
    df = metrics.get("equity_df")
    for key, value in metrics.items():
        if key == "equity_df":
            continue
        if isinstance(value, (np.generic,)):
            value = float(value)
        summary[key] = value

    if df is not None and not df.empty:
        summary["observations"] = int(len(df))
        summary["period_start"] = _format_ts(df["timestamp"].iloc[0])
        summary["period_end"] = _format_ts(df["timestamp"].iloc[-1])
    else:
        summary["observations"] = 0

    return summary


def _format_ts(value: Any) -> str:
    try:
        ts = pd.to_datetime(value)
        return str(ts)
    except Exception:
        return str(value)


def _annualised_sharpe(returns: np.ndarray, periods: int = 252) -> float:
    if returns.size == 0:
        return 0.0
    mean = returns.mean()
    std = returns.std(ddof=0)
    if std == 0:
        return 0.0
    return float(np.sqrt(periods) * (mean / std))


def bootstrap_reality_check(
    results: List[Dict[str, Any]],
    seed: int,
    n_bootstrap: int = 200,
) -> float | None:
    valid = [res for res in results if res["returns"].size > 1]
    if len(valid) < 2:
        return None

    observed_sharpes = [res["metrics"].get("sharpe_ratio", 0.0) for res in valid]
    best_sharpe = max(observed_sharpes)
    if not np.isfinite(best_sharpe):
        return None

    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(n_bootstrap):
        max_sharpe = float("-inf")
        for entry in valid:
            returns = entry["returns"]
            sample = rng.choice(returns, size=returns.size, replace=True)
            sharpe = _annualised_sharpe(sample)
            max_sharpe = max(max_sharpe, sharpe)
        if max_sharpe >= best_sharpe:
            exceed += 1

    return (exceed + 1) / (n_bootstrap + 1)


def _strategy_params(strategy_cfg) -> Dict[str, Any]:
    params = dict(strategy_cfg.params)
    if getattr(strategy_cfg, "lookback", None) is not None:
        params.setdefault("lookback", strategy_cfg.lookback)
    if getattr(strategy_cfg, "z", None) is not None:
        params.setdefault("z_threshold", strategy_cfg.z)
    return params


def _strategy_kwargs(params: Dict[str, Any], warmup_prices=None) -> Dict[str, Any]:
    kwargs = dict(params)
    if "z" in kwargs and "z_threshold" not in kwargs:
        kwargs["z_threshold"] = kwargs.pop("z")
    if warmup_prices is not None:
        kwargs["warmup_prices"] = warmup_prices
    return kwargs
