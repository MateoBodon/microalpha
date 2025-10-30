"""Walk-forward validation orchestration."""

from __future__ import annotations

import hashlib
import json
import warnings
from dataclasses import asdict
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple, cast

import numpy as np
import pandas as pd
import yaml

from .broker import SimulatedBroker
from .config import BacktestCfg, ExecModelCfg
from .config_wfv import RealityCheckCfg, WFVCfg
from .data import CsvDataHandler, DataHandler, MultiCsvDataHandler
from .engine import Engine
from .execution import (
    TWAP,
    VWAP,
    Executor,
    ImplementationShortfall,
    KyleLambda,
    LOBExecution,
    SquareRootImpact,
)
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
from .market_metadata import load_symbol_meta
from .runner import (
    persist_config,
    prepare_artifacts_dir,
    resolve_capital_policy,
    persist_exposures,
    resolve_path,
    resolve_slippage_model,
)
from .strategies.breakout import BreakoutStrategy
from .strategies.cs_momentum import CrossSectionalMomentum
from .strategies.flagship_mom import FlagshipMomentumStrategy
from .strategies.meanrev import MeanReversionStrategy
from .strategies.mm import NaiveMarketMakingStrategy
from .risk_stats import block_bootstrap

STRATEGY_MAPPING = {
    "MeanReversionStrategy": MeanReversionStrategy,
    "BreakoutStrategy": BreakoutStrategy,
    "NaiveMarketMakingStrategy": NaiveMarketMakingStrategy,
    "CrossSectionalMomentum": CrossSectionalMomentum,
    "FlagshipMomentumStrategy": FlagshipMomentumStrategy,
}

EXECUTION_MAPPING = {
    "instant": Executor,
    "linear": Executor,
    "twap": TWAP,
    "vwap": VWAP,
    "is": ImplementationShortfall,
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

        reality_payload = raw.get("reality_check") or {}
        return WFVCfg(
            template=template,
            walkforward=raw["walkforward"],
            grid=grid,
            artifacts_dir=raw.get("artifacts_dir"),
            reality_check=reality_payload,
        )

    raise ValueError("Invalid walk-forward configuration schema.")


def run_walk_forward(
    config_path: str,
    override_artifacts_dir: str | None = None,
    reality_check_method: str | None = None,
    reality_check_block_len: int | None = None,
) -> Dict[str, Any]:
    cfg_path = Path(config_path).expanduser().resolve()
    raw_config = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    cfg = load_wfv_cfg(str(cfg_path))
    if reality_check_method or reality_check_block_len is not None:
        rc_update: Dict[str, Any] = {}
        if reality_check_method:
            rc_update["method"] = reality_check_method.lower()
        if reality_check_block_len is not None:
            rc_update["block_length"] = reality_check_block_len
        if rc_update:
            rc_cfg = cfg.reality_check.model_copy(update=rc_update)
            cfg = cfg.model_copy(update={"reality_check": rc_cfg})
    config_hash = hashlib.sha256(yaml.safe_dump(raw_config).encode("utf-8")).hexdigest()

    full_sha, short_sha = resolve_git_sha()
    base_run_id = generate_run_id(short_sha)
    # Allow CLI override of artifacts root directory without mutating on-disk config
    effective_cfg = dict(raw_config)
    if override_artifacts_dir is not None:
        effective_cfg["artifacts_dir"] = override_artifacts_dir

    run_id, artifacts_dir = prepare_artifacts_dir(cfg_path, effective_cfg, base_run_id)
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
    data_handler: DataHandler
    cs_symbols: List[str] = []
    if strategy_name in {"CrossSectionalMomentum", "FlagshipMomentumStrategy"}:
        if strategy_name == "CrossSectionalMomentum":
            raw_symbols = list(cfg.template.strategy.params.get("symbols") or [])
            if not raw_symbols:
                raw_symbols = list(getattr(cfg.template, "symbols", []) or [])
            if not raw_symbols:
                raw_symbols = [symbol]
            cs_symbols = [str(sym).upper() for sym in raw_symbols]
            base_params.setdefault("symbols", cs_symbols)
        else:
            universe_path = base_params.get("universe_path") or cfg.template.strategy.params.get(
                "universe_path"
            )
            if universe_path is None:
                raise ValueError(
                    "FlagshipMomentumStrategy requires 'universe_path' defined in template params"
                )
            u_path = resolve_path(str(universe_path), cfg_path)
            if not u_path.exists():
                raise FileNotFoundError(f"Flagship universe file not found: {u_path}")
            base_params["universe_path"] = str(u_path)
            universe_df = pd.read_csv(u_path)
            if "symbol" not in universe_df.columns:
                raise ValueError("Flagship universe file must contain 'symbol' column")
            cs_symbols = sorted(universe_df["symbol"].astype(str).str.upper().unique())
            base_params["symbols"] = cs_symbols
        data_handler = MultiCsvDataHandler(csv_dir=data_dir, symbols=cs_symbols)
    else:
        data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    if data_handler.data is None:
        raise FileNotFoundError(
            f"Unable to load data for symbol '{symbol}' from {data_dir}"
        )

    symbol_meta: Dict[str, Any] = {}
    if getattr(cfg.template, "meta_path", None):
        meta_resolved = resolve_path(cfg.template.meta_path, cfg_path)
        symbol_meta = load_symbol_meta(meta_resolved)

    equity_records: List[Dict[str, Any]] = []
    folds: List[Dict[str, Any]] = []
    bootstrap_records: List[Dict[str, Any]] = []
    fold_exposure_paths: List[str] = []
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

            best_params, train_metrics, rc_result = _optimise_parameters(
                data_handler,
                train_start,
                train_end,
                strategy_class,
                param_grid,
                base_params,
                cfg.template,
                train_rng,
                cfg.reality_check,
                symbol_meta=symbol_meta,
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
                        "reality_check_pvalue": None,
                        "reality_check": None,
                        "spa_pvalue": None,
                    }
                )
                current_date += pd.Timedelta(days=testing_days)
                continue

            warmup_prices: List[float] | None = None
            warmup_history: Dict[str, List[float]] | None = None
            if strategy_name in {"CrossSectionalMomentum", "FlagshipMomentumStrategy"}:
                assert isinstance(data_handler, MultiCsvDataHandler)
                warmup_history = _collect_cs_warmup_history(
                    data_handler,
                    train_start,
                    train_end,
                    cs_symbols,
                )
            else:
                assert isinstance(data_handler, CsvDataHandler)
                warmup_prices = _collect_warmup_prices(
                    data_handler, train_end, best_params.get("lookback", 0)
                )

            data_handler.set_date_range(test_start, test_end)
            if strategy_name in {"CrossSectionalMomentum", "FlagshipMomentumStrategy"}:
                assert isinstance(data_handler, MultiCsvDataHandler)
                kwargs = _strategy_kwargs(best_params)
                kwargs.pop("warmup_prices", None)
                if warmup_history:
                    kwargs["warmup_history"] = warmup_history
                strategy = strategy_class(**kwargs)
            else:
                strategy = strategy_class(
                    symbol=symbol, **_strategy_kwargs(best_params, warmup_prices)
                )
            portfolio = _build_portfolio(
                data_handler,
                cfg.template,
                trade_logger=trade_logger,
                symbol_meta=symbol_meta,
            )
            if hasattr(strategy, "sector_map") and strategy.sector_map:
                portfolio.sector_of.update(strategy.sector_map)
            test_rng = _spawn_rng(fold_rng)
            exec_rng = _spawn_rng(test_rng)
            executor = _build_executor(
                data_handler,
                cfg.template.exec,
                exec_rng,
                symbol_meta=symbol_meta,
            )
            broker = SimulatedBroker(executor)
            # Hint engine where to place profiling outputs for this run
            import os as _os

            _os.environ["MICROALPHA_ARTIFACTS_DIR"] = str(artifacts_dir)

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

            fold_index = len(folds)
            exposure_path = persist_exposures(
                portfolio,
                artifacts_dir,
                filename=f"exposures_fold_{fold_index}.csv",
            )
            if exposure_path:
                fold_exposure_paths.append(exposure_path)

            test_metrics = compute_metrics(
                portfolio.equity_curve,
                portfolio.total_turnover,
                hac_lags=cfg.template.metrics_hac_lags,
            )

            rc_summary: Dict[str, Any] | None = None
            rc_pvalue = None
            if rc_result:
                rc_pvalue = rc_result.get("p_value")
                best_sharpe_val = rc_result.get("best_sharpe")
                if best_sharpe_val is not None and np.isfinite(best_sharpe_val):
                    best_sharpe_val = float(best_sharpe_val)
                else:
                    best_sharpe_val = None
                rc_summary = {
                    "p_value": float(rc_pvalue) if rc_pvalue is not None else None,
                    "best_sharpe": best_sharpe_val,
                    "method": rc_result.get("method"),
                    "block_length": rc_result.get("block_length"),
                    "num_bootstrap": rc_result.get("num_bootstrap"),
                }
                distribution = rc_result.get("distribution", [])
                bootstrap_records.append(
                    {
                        "fold": len(folds),
                        "train_start": str(train_start.date()),
                        "train_end": str(train_end.date()),
                        "test_start": str(test_start.date()),
                        "test_end": str(test_end.date()),
                        "p_value": float(rc_pvalue) if rc_pvalue is not None else None,
                        "best_sharpe": best_sharpe_val,
                        "distribution": [float(x) for x in distribution],
                        "method": rc_result.get("method"),
                        "block_length": rc_result.get("block_length"),
                        "num_bootstrap": rc_result.get("num_bootstrap"),
                    }
                )

            fold_entry = {
                "train_start": str(train_start.date()),
                "train_end": str(train_end.date()),
                "test_start": str(test_start.date()),
                "test_end": str(test_end.date()),
                "best_params": best_params,
                "train_metrics": _metrics_summary(train_metrics),
                "test_metrics": _metrics_summary(test_metrics),
                "reality_check_pvalue": (
                    None if rc_pvalue is None else float(rc_pvalue)
                ),
                "reality_check": rc_summary,
                "exposures_path": exposure_path,
                "spa_pvalue": None,
            }

            folds.append(fold_entry)

            current_date += pd.Timedelta(days=testing_days)
    finally:
        trade_logger.close()

    exposures_path: str | None = None
    if fold_exposure_paths:
        final_path = artifacts_dir / "exposures.csv"
        last_df = pd.read_csv(fold_exposure_paths[-1])
        last_df.to_csv(final_path, index=False)
        exposures_path = str(final_path)

    folds_path = artifacts_dir / "folds.json"
    with folds_path.open("w", encoding="utf-8") as handle:
        json.dump(folds, handle, indent=2)

    bootstrap_path = artifacts_dir / "bootstrap.json"
    with bootstrap_path.open("w", encoding="utf-8") as handle:
        json.dump(bootstrap_records, handle, indent=2)

    metrics = _summarise_walkforward(
        equity_records,
        artifacts_dir,
        total_turnover,
        hac_lags=cfg.template.metrics_hac_lags,
    )

    result: Dict[str, Any] = asdict(manifest)
    result.update(
        {
            "artifacts_dir": str(artifacts_dir),
            "strategy": strategy_name,
            "folds_path": str(folds_path),
            "bootstrap_path": str(bootstrap_path),
            "exposures_path": exposures_path,
            "metrics": metrics,
            "folds": folds,
            "trades_path": str(artifacts_dir / "trades.jsonl"),
        }
    )
    return result


def _optimise_parameters(
    data_handler: DataHandler,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    strategy_class,
    param_grid: Mapping[str, Sequence[Any]],
    base_params: Dict[str, Any],
    cfg: BacktestCfg,
    rng: np.random.Generator,
    reality_cfg: RealityCheckCfg,
    symbol_meta: Mapping[str, Any] | None = None,
) -> Tuple[Dict[str, Any], Dict[str, Any] | None, Dict[str, Any] | None]:
    best_entry: Dict[str, Any] | None = None
    results: List[Dict[str, Any]] = []

    keys = list(param_grid.keys())

    for combination in product(*(param_grid[key] for key in keys)):
        params = dict(zip(keys, combination))

        sim_rng = _spawn_rng(rng)

        data_handler.set_date_range(train_start, train_end)
        combined = dict(base_params)
        combined.update(params)
        if strategy_class in (CrossSectionalMomentum, FlagshipMomentumStrategy):
            strategy = strategy_class(**_strategy_kwargs(combined))
        else:
            strategy = strategy_class(symbol=cfg.symbol, **_strategy_kwargs(combined))
        portfolio = _build_portfolio(
            data_handler,
            cfg,
            symbol_meta=symbol_meta,
        )
        if hasattr(strategy, "sector_map") and strategy.sector_map:
            portfolio.sector_of.update(strategy.sector_map)
        exec_rng = _spawn_rng(sim_rng)
        executor = _build_executor(
            data_handler,
            cfg.exec,
            exec_rng,
            symbol_meta=symbol_meta,
        )
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

        metrics = compute_metrics(
            portfolio.equity_curve,
            portfolio.total_turnover,
            hac_lags=cfg.metrics_hac_lags,
        )
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
    rc_method = reality_cfg.method.lower()
    rc_block_len = reality_cfg.block_length
    rc_samples = int(reality_cfg.samples)
    reality_result = bootstrap_reality_check(
        results,
        seed=cfg.seed,
        n_bootstrap=rc_samples,
        method=rc_method,
        block_len=rc_block_len,
    )

    params = dict(base_params)
    params.update(best_entry["params"])
    return params, best_entry["metrics"], reality_result


def _build_portfolio(
    data_handler,
    cfg: BacktestCfg,
    trade_logger: JsonlWriter | None = None,
    symbol_meta: Mapping[str, Any] | None = None,
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
        capital_policy=resolve_capital_policy(cfg.capital_policy),
        symbol_meta=symbol_meta,
    )


def _build_executor(
    data_handler,
    exec_cfg: ExecModelCfg,
    rng: np.random.Generator,
    symbol_meta: Mapping[str, Any] | None = None,
):
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
    if executor_cls in (TWAP, VWAP, ImplementationShortfall) and exec_cfg.slices:
        kwargs["slices"] = exec_cfg.slices
    if executor_cls is ImplementationShortfall and exec_cfg.urgency is not None:
        kwargs["urgency"] = exec_cfg.urgency
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
    slippage_model = resolve_slippage_model(exec_cfg.slippage, symbol_meta)
    if slippage_model is not None:
        kwargs["slippage_model"] = slippage_model
    if symbol_meta:
        kwargs.setdefault("symbol_meta", symbol_meta)
    if exec_cfg.limit_mode and exec_cfg.limit_mode.lower() != "market":
        kwargs["limit_mode"] = exec_cfg.limit_mode.upper()
    if exec_cfg.queue_coefficient is not None:
        kwargs["queue_coefficient"] = float(exec_cfg.queue_coefficient)
    if exec_cfg.queue_passive_multiplier is not None:
        kwargs["queue_passive_multiplier"] = float(
            exec_cfg.queue_passive_multiplier
        )
    if exec_cfg.queue_seed is not None:
        kwargs["queue_seed"] = int(exec_cfg.queue_seed)
    if exec_cfg.queue_randomize is not None:
        kwargs["queue_randomize"] = bool(exec_cfg.queue_randomize)
    if exec_cfg.volatility_lookback is not None:
        kwargs["volatility_lookback"] = int(exec_cfg.volatility_lookback)
    if exec_cfg.min_fill_qty is not None:
        kwargs["min_fill_qty"] = int(exec_cfg.min_fill_qty)

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


def _collect_cs_warmup_history(
    data_handler: MultiCsvDataHandler,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    symbols: Sequence[str],
) -> Dict[str, List[float]]:
    data_handler.set_date_range(train_start, train_end)
    history: Dict[str, List[float]] = {sym: [] for sym in symbols}
    for event in data_handler.stream():
        history.setdefault(event.symbol, []).append(event.price)
    return history


def _summarise_walkforward(
    equity_records: List[Dict[str, Any]],
    artifacts_dir: Path,
    total_turnover: float,
    hac_lags: int | None = None,
) -> Dict[str, Any]:
    metrics = compute_metrics(
        equity_records,
        total_turnover,
        hac_lags=hac_lags,
    )
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
    method: str = "stationary",
    block_len: int | None = None,
) -> Dict[str, Any] | None:
    valid = [res for res in results if res["returns"].size > 1]
    if len(valid) < 2:
        return None

    observed_sharpes = [res["metrics"].get("sharpe_ratio", 0.0) for res in valid]
    best_sharpe = max(observed_sharpes)
    if not np.isfinite(best_sharpe):
        return None

    rng = np.random.default_rng(seed)
    method_lower = method.lower()
    use_iid = method_lower == "iid"
    if use_iid:
        warnings.warn(
            "IID resampling for walk-forward reality check is deprecated; "
            "prefer stationary or circular block bootstrap.",
            DeprecationWarning,
            stacklevel=2,
        )

    exceed = 0
    distribution: List[float] = []
    for _ in range(max(1, n_bootstrap)):
        max_sharpe = float("-inf")
        for entry in valid:
            returns = entry["returns"]
            if use_iid:
                sample = rng.choice(returns, size=returns.size, replace=True)
            else:
                sample = next(
                    block_bootstrap(
                        returns,
                        B=1,
                        method=method_lower,  # type: ignore[arg-type]
                        block_len=block_len,
                        rng=rng,
                    )
                )
            sharpe = _annualised_sharpe(sample)
            max_sharpe = max(max_sharpe, sharpe)
        distribution.append(float(max_sharpe))
        if max_sharpe >= best_sharpe:
            exceed += 1

    p_value = (exceed + 1) / (len(distribution) + 1)
    return {
        "p_value": float(p_value),
        "distribution": distribution,
        "best_sharpe": float(best_sharpe),
        "method": method_lower,
        "block_length": block_len,
        "num_models": len(valid),
        "num_bootstrap": len(distribution),
    }


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
