"""Baseline suite computation and reporting helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import yaml

from microalpha.risk_stats import sharpe_stats

BASELINE_COLUMNS = (
    "date",
    "flagship_net",
    "eqw_universe",
    "market_proxy",
    "mom_12_1",
    "cash_rf",
)

BASELINE_LABELS = {
    "flagship_net": "Flagship (net)",
    "eqw_universe": "Equal-weight universe",
    "market_proxy": "Market proxy",
    "mom_12_1": "Momentum 12-1",
    "cash_rf": "Cash / RF",
}

DEFAULT_LOOKBACK_MONTHS = 12
DEFAULT_SKIP_MONTHS = 1
DEFAULT_MOM_LONG_SHORT = False


def load_baseline_status(artifact_dir: Path) -> dict[str, Any] | None:
    status_path = Path(artifact_dir) / "baselines_status.json"
    if not status_path.exists():
        return None
    try:
        return json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_baselines(artifact_dir: Path) -> pd.DataFrame | None:
    baselines_path = Path(artifact_dir) / "baselines.csv"
    if not baselines_path.exists():
        return None
    df = pd.read_csv(baselines_path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def compute_baselines(
    artifact_dir: Path | str,
    *,
    force: bool = False,
) -> pd.DataFrame:
    artifact_dir = Path(artifact_dir).resolve()
    baselines_path = artifact_dir / "baselines.csv"
    status_path = artifact_dir / "baselines_status.json"

    if not force and baselines_path.exists() and status_path.exists():
        existing = load_baselines(artifact_dir)
        if existing is not None:
            return existing

    status: dict[str, Any] = {}
    for key in BASELINE_COLUMNS:
        if key != "date":
            status[key] = {"status": "missing", "reason": "not computed"}

    equity_path = artifact_dir / "equity_curve.csv"
    if not equity_path.exists():
        baseline_df = pd.DataFrame(columns=BASELINE_COLUMNS)
        _write_baselines(baseline_df, baselines_path, status, status_path)
        _write_missing_flagship_readme(artifact_dir, "equity_curve.csv not found")
        return baseline_df

    equity_df = pd.read_csv(equity_path)
    if "timestamp" not in equity_df.columns:
        baseline_df = pd.DataFrame(columns=BASELINE_COLUMNS)
        _write_baselines(baseline_df, baselines_path, status, status_path)
        _write_missing_flagship_readme(artifact_dir, "equity_curve.csv missing timestamp")
        return baseline_df

    equity_df["date"] = pd.to_datetime(equity_df["timestamp"], unit="ns", errors="coerce")
    equity_df["date"] = equity_df["date"].dt.normalize()
    equity_df = equity_df.dropna(subset=["date"]).drop_duplicates("date").sort_values("date")
    if equity_df.empty:
        baseline_df = pd.DataFrame(columns=BASELINE_COLUMNS)
        _write_baselines(baseline_df, baselines_path, status, status_path)
        _write_missing_flagship_readme(artifact_dir, "equity_curve.csv has no usable dates")
        return baseline_df

    if "returns" in equity_df.columns:
        flagship_returns = equity_df["returns"].astype(float)
    elif "equity" in equity_df.columns:
        flagship_returns = (
            equity_df["equity"].astype(float).pct_change(fill_method=None).fillna(0.0)
        )
    else:
        flagship_returns = pd.Series([np.nan] * len(equity_df), index=equity_df.index)

    calendar = pd.DatetimeIndex(equity_df["date"].tolist())
    baseline_df = pd.DataFrame(
        {
            "date": calendar,
            "flagship_net": flagship_returns.to_numpy(dtype=float, copy=False),
        }
    )

    if flagship_returns.notna().any():
        status["flagship_net"] = {"status": "ok", "reason": "equity_curve.csv returns"}
    else:
        status["flagship_net"] = {"status": "missing", "reason": "flagship returns unavailable"}
        _write_missing_flagship_readme(artifact_dir, "flagship returns unavailable in equity_curve.csv")

    config_path = _resolve_config_path(artifact_dir)
    config_payload = _load_config_payload(config_path)
    status["meta"] = {
        "config_path": str(config_path) if config_path else None,
        "config_source": "artifact" if config_path and config_path.exists() else "none",
    }
    data_path = _resolve_data_path(config_payload, config_path)
    universe_path = _resolve_universe_path(config_payload, config_path)
    status["meta"]["data_path"] = str(data_path) if data_path else None
    status["meta"]["universe_path"] = str(universe_path) if universe_path else None

    baseline_df = _attach_market_proxy(
        baseline_df,
        calendar=calendar,
        data_path=data_path,
        status=status,
    )
    baseline_df = _attach_cash_rf(
        baseline_df,
        calendar=calendar,
        data_path=data_path,
        status=status,
    )

    if data_path and universe_path and data_path.exists() and universe_path.exists():
        universe = _load_universe(universe_path)
        if universe:
            symbols = _collect_universe_symbols(universe)
            prices, missing_symbols = _load_price_panel(data_path, symbols, calendar)
            status["meta"]["missing_symbols"] = missing_symbols
            if not prices.empty:
                returns = prices.pct_change(fill_method=None)
                rebalance_dates = _month_end_dates(calendar)
                eqw_series, eqw_turnover = _compute_eqw_returns(
                    returns,
                    universe,
                    rebalance_dates,
                    calendar,
                )
                baseline_df["eqw_universe"] = eqw_series.reindex(calendar).to_numpy()
                status["eqw_universe"] = {
                    "status": "ok" if eqw_series.notna().any() else "missing",
                    "reason": "equal-weight rebalance",
                    "turnover": float(eqw_turnover),
                }

                mom_series, mom_turnover, mom_note = _compute_momentum_returns(
                    prices,
                    returns,
                    universe,
                    rebalance_dates,
                    calendar,
                    lookback_months=DEFAULT_LOOKBACK_MONTHS,
                    skip_months=DEFAULT_SKIP_MONTHS,
                    long_short=DEFAULT_MOM_LONG_SHORT,
                )
                baseline_df["mom_12_1"] = mom_series.reindex(calendar).to_numpy()
                status["mom_12_1"] = {
                    "status": "ok" if mom_series.notna().any() else "missing",
                    "reason": mom_note,
                    "turnover": float(mom_turnover),
                }
            else:
                status["eqw_universe"] = {
                    "status": "missing",
                    "reason": "no price data available",
                }
                status["mom_12_1"] = {
                    "status": "missing",
                    "reason": "no price data available",
                }
        else:
            status["eqw_universe"] = {"status": "missing", "reason": "universe empty"}
            status["mom_12_1"] = {"status": "missing", "reason": "universe empty"}
    else:
        if not universe_path or not universe_path.exists():
            status["eqw_universe"] = {
                "status": "missing",
                "reason": "universe_path not available",
            }
            status["mom_12_1"] = {
                "status": "missing",
                "reason": "universe_path not available",
            }
        elif not data_path or not data_path.exists():
            status["eqw_universe"] = {
                "status": "missing",
                "reason": "data_path not available",
            }
            status["mom_12_1"] = {
                "status": "missing",
                "reason": "data_path not available",
            }

    baseline_df = _enforce_columns(baseline_df)
    _write_baselines(baseline_df, baselines_path, status, status_path)
    return baseline_df


def compute_baseline_metrics(
    baselines: pd.DataFrame,
    *,
    flagship_metrics: Mapping[str, object] | None = None,
    hac_lags: int | None = None,
    periods_per_year: int = 252,
    status: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    status = status or {}

    def _turnover_for(label: str) -> float | None:
        entry = status.get(label) if isinstance(status, Mapping) else None
        if isinstance(entry, Mapping) and "turnover" in entry:
            try:
                return float(entry["turnover"])
            except (TypeError, ValueError):
                return None
        return None

    if flagship_metrics is not None:
        rows.append(
            {
                "Series": BASELINE_LABELS["flagship_net"],
                "Sharpe_HAC": _to_float(flagship_metrics.get("sharpe_ratio")),
                "MaxDD": _to_float(flagship_metrics.get("max_drawdown")),
                "CAGR": _to_float(flagship_metrics.get("cagr")),
                "Turnover": _to_float(flagship_metrics.get("total_turnover")),
            }
        )
    elif "flagship_net" in baselines:
        rows.append(
            {
                "Series": BASELINE_LABELS["flagship_net"],
                **_metrics_from_returns(
                    baselines["flagship_net"], periods_per_year=periods_per_year, hac_lags=hac_lags
                ),
                "Turnover": _turnover_for("flagship_net"),
            }
        )

    for key in ("eqw_universe", "market_proxy", "mom_12_1", "cash_rf"):
        if key not in baselines:
            continue
        metrics = _metrics_from_returns(
            baselines[key], periods_per_year=periods_per_year, hac_lags=hac_lags
        )
        metrics["Turnover"] = _turnover_for(key)
        rows.append(
            {
                "Series": BASELINE_LABELS.get(key, key),
                "Sharpe_HAC": metrics["Sharpe_HAC"],
                "MaxDD": metrics["MaxDD"],
                "CAGR": metrics["CAGR"],
                "Turnover": metrics["Turnover"],
            }
        )

    return pd.DataFrame(rows, columns=["Series", "Sharpe_HAC", "MaxDD", "CAGR", "Turnover"])


def render_baseline_table(metrics_df: pd.DataFrame) -> str:
    lines = ["| Series | Sharpe_HAC | MaxDD | CAGR | Turnover |", "| --- | ---:| ---:| ---:| ---:|"]
    for row in metrics_df.itertuples(index=False):
        lines.append(
            "| {series} | {sharpe} | {maxdd} | {cagr} | {turnover} |".format(
                series=row.Series,
                sharpe=_format_metric(row.Sharpe_HAC),
                maxdd=_format_pct(row.MaxDD),
                cagr=_format_pct(row.CAGR),
                turnover=_format_turnover(row.Turnover),
            )
        )
    return "\n".join(lines)


def plot_baseline_overlay(
    baselines: pd.DataFrame,
    output_path: Path,
    *,
    title: str = "Cumulative Returns: Flagship vs Baselines",
) -> Path | None:
    if baselines.empty:
        return None
    import matplotlib.pyplot as plt

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 5))
    plotted = 0
    for key in ("flagship_net", "eqw_universe", "market_proxy", "mom_12_1", "cash_rf"):
        if key not in baselines:
            continue
        series = pd.Series(baselines[key]).dropna()
        if series.empty:
            continue
        returns = baselines[key].fillna(0.0).astype(float)
        curve = (1.0 + returns).cumprod()
        plt.plot(baselines["date"], curve, label=BASELINE_LABELS.get(key, key))
        plotted += 1

    if plotted == 0:
        plt.close()
        return None

    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Cumulative return")
    plt.grid(True, linestyle=":", alpha=0.4)
    plt.legend(loc="best", fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    return output_path


def _metrics_from_returns(
    returns: pd.Series, *, periods_per_year: int, hac_lags: int | None
) -> dict[str, float | None]:
    series = pd.Series(returns).dropna()
    if series.empty:
        return {"Sharpe_HAC": None, "MaxDD": None, "CAGR": None}
    sharpe_summary = sharpe_stats(
        returns=series.astype(float),
        periods=periods_per_year,
        ddof=0,
        hac_lags=hac_lags,
    )
    sharpe = float(sharpe_summary["sharpe"])
    curve = (1.0 + series.astype(float)).cumprod()
    running_max = curve.cummax()
    drawdown = (running_max - curve) / running_max
    max_dd = float(drawdown.max() if not drawdown.empty else 0.0)
    years = max(len(series) / periods_per_year, 1e-9)
    ending_value = float(curve.iloc[-1]) if not curve.empty else 1.0
    cagr = float(ending_value ** (1.0 / years) - 1.0)
    return {"Sharpe_HAC": sharpe, "MaxDD": max_dd, "CAGR": cagr}


def _resolve_config_path(artifact_dir: Path) -> Path | None:
    manifest_path = artifact_dir / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            config_path = manifest.get("config_path")
            if config_path:
                candidate = Path(config_path)
                if candidate.exists():
                    return candidate
                artifact_candidate = artifact_dir / Path(config_path).name
                if artifact_candidate.exists():
                    return artifact_candidate
        except Exception:
            pass
    yaml_files = sorted(list(artifact_dir.glob("*.yaml")) + list(artifact_dir.glob("*.yml")))
    return yaml_files[0] if yaml_files else None


def _load_config_payload(config_path: Path | None) -> dict[str, Any]:
    if not config_path or not config_path.exists():
        return {}
    try:
        return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _resolve_data_path(config: Mapping[str, Any], config_path: Path | None) -> Path | None:
    base = config.get("template") if isinstance(config.get("template"), Mapping) else config
    if not isinstance(base, Mapping):
        return None
    data_path = base.get("data_path") or base.get("data_dir") or base.get("data")
    if not data_path:
        return None
    return _resolve_path(str(data_path), config_path)


def _resolve_universe_path(config: Mapping[str, Any], config_path: Path | None) -> Path | None:
    base = config.get("template") if isinstance(config.get("template"), Mapping) else config
    if not isinstance(base, Mapping):
        return None
    strategy = base.get("strategy")
    if not isinstance(strategy, Mapping):
        return None
    params = strategy.get("params")
    if not isinstance(params, Mapping):
        return None
    universe_path = params.get("universe_path")
    if not universe_path:
        return None
    return _resolve_path(str(universe_path), config_path)


def _resolve_path(value: str, config_path: Path | None) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(value))
    path = Path(expanded)
    if path.is_absolute():
        return path
    if config_path:
        candidate = (config_path.parent / path).resolve()
        if candidate.exists():
            return candidate
    return (Path.cwd() / path).resolve()


def _load_universe(path: Path) -> dict[pd.Timestamp, pd.DataFrame]:
    df = pd.read_csv(path)
    if "symbol" not in df.columns or "date" not in df.columns:
        return {}
    df["symbol"] = df["symbol"].astype(str).str.upper()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["rebalance"] = df["date"].dt.to_period("M").dt.to_timestamp("M")
    df.set_index(["rebalance", "symbol"], inplace=True)
    universe: dict[pd.Timestamp, pd.DataFrame] = {}
    for rebalance_date, group in df.groupby(level=0):
        snapshot = group.droplevel(0).copy()
        universe[pd.Timestamp(rebalance_date)] = snapshot
    return universe


def _collect_universe_symbols(universe: Mapping[pd.Timestamp, pd.DataFrame]) -> list[str]:
    symbols: set[str] = set()
    for snapshot in universe.values():
        symbols.update([str(sym).upper() for sym in snapshot.index])
    return sorted(symbols)


def _load_price_panel(
    data_path: Path, symbols: list[str], calendar: pd.DatetimeIndex
) -> tuple[pd.DataFrame, list[str]]:
    frames: list[pd.Series] = []
    missing: list[str] = []
    for sym in symbols:
        path = data_path / f"{sym}.csv"
        if not path.exists():
            missing.append(sym)
            continue
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        if df is None or df.empty or "close" not in df.columns:
            missing.append(sym)
            continue
        series = df["close"].astype(float)
        series = series.reindex(calendar, method="ffill")
        frames.append(series.rename(sym))
    if not frames:
        return pd.DataFrame(index=calendar), missing
    panel = pd.concat(frames, axis=1)
    panel = panel.loc[calendar]
    return panel, missing


def _month_end_dates(calendar: pd.DatetimeIndex) -> list[pd.Timestamp]:
    if calendar.empty:
        return []
    month_ends = (
        pd.Series(calendar)
        .groupby(calendar.to_period("M"))
        .max()
        .sort_values()
        .tolist()
    )
    return [pd.Timestamp(val) for val in month_ends]


def _snapshot_for(
    universe: Mapping[pd.Timestamp, pd.DataFrame], rebalance_date: pd.Timestamp
) -> pd.DataFrame | None:
    eligible = [date for date in universe.keys() if date <= rebalance_date]
    if not eligible:
        return None
    latest = max(eligible)
    return universe.get(latest)


def _compute_eqw_returns(
    returns: pd.DataFrame,
    universe: Mapping[pd.Timestamp, pd.DataFrame],
    rebalance_dates: list[pd.Timestamp],
    calendar: pd.DatetimeIndex,
) -> tuple[pd.Series, float]:
    series = pd.Series(index=calendar, dtype=float)
    turnover = 0.0
    prev_weights: pd.Series | None = None

    for idx, rebalance_date in enumerate(rebalance_dates):
        snapshot = _snapshot_for(universe, rebalance_date)
        if snapshot is None or snapshot.empty:
            continue
        symbols = [str(sym).upper() for sym in snapshot.index if sym in returns.columns]
        if not symbols:
            continue
        weights = pd.Series(1.0 / len(symbols), index=symbols)
        if prev_weights is not None:
            combined_index = prev_weights.index.union(weights.index)
            prev = prev_weights.reindex(combined_index, fill_value=0.0)
            current = weights.reindex(combined_index, fill_value=0.0)
            turnover += 0.5 * float((current - prev).abs().sum())
        prev_weights = weights

        end_date = rebalance_dates[idx + 1] if idx + 1 < len(rebalance_dates) else None
        if end_date is None:
            mask = calendar > rebalance_date
        else:
            mask = (calendar > rebalance_date) & (calendar <= end_date)
        window = calendar[mask]
        if window.empty:
            continue
        window_returns = returns.loc[window, symbols].fillna(0.0)
        series.loc[window] = window_returns.mul(weights, axis=1).sum(axis=1)

    return series, turnover


def _compute_momentum_returns(
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    universe: Mapping[pd.Timestamp, pd.DataFrame],
    rebalance_dates: list[pd.Timestamp],
    calendar: pd.DatetimeIndex,
    *,
    lookback_months: int,
    skip_months: int,
    long_short: bool,
) -> tuple[pd.Series, float, str]:
    series = pd.Series(index=calendar, dtype=float)
    turnover = 0.0
    prev_weights: pd.Series | None = None
    note = f"lookback={lookback_months}M skip={skip_months}M long_short={long_short}"

    for idx, rebalance_date in enumerate(rebalance_dates):
        formation_end = _shift_month_end(rebalance_date, -skip_months)
        formation_start = _shift_month_end(formation_end, -lookback_months)
        if formation_start is None or formation_end is None:
            continue
        formation_start = _calendar_on_or_before(calendar, formation_start)
        formation_end = _calendar_on_or_before(calendar, formation_end)
        if formation_start is None or formation_end is None:
            continue
        if formation_end >= rebalance_date:
            continue

        snapshot = _snapshot_for(universe, rebalance_date)
        if snapshot is None or snapshot.empty:
            continue
        symbols = [str(sym).upper() for sym in snapshot.index if sym in prices.columns]
        if not symbols:
            continue

        start_prices = prices.loc[formation_start, symbols]
        end_prices = prices.loc[formation_end, symbols]
        valid_mask = (start_prices > 0) & (end_prices > 0)
        scores = (end_prices[valid_mask] / start_prices[valid_mask] - 1.0).dropna()
        if scores.empty:
            continue

        scores = scores.sort_values(ascending=False)
        n = len(scores)
        decile = max(int(np.floor(n * 0.1)), 1)
        long_syms = list(scores.index[:decile])
        short_syms: list[str] = []
        if long_short and n >= 2:
            short_syms = list(scores.index[-decile:])
            short_syms = [sym for sym in short_syms if sym not in long_syms]

        weights: dict[str, float] = {}
        if long_syms:
            w = 1.0 / len(long_syms)
            for sym in long_syms:
                weights[sym] = w
        if short_syms:
            w = -1.0 / len(short_syms)
            for sym in short_syms:
                weights[sym] = w

        if not weights:
            continue
        weights_series = pd.Series(weights)
        if prev_weights is not None:
            combined_index = prev_weights.index.union(weights_series.index)
            prev = prev_weights.reindex(combined_index, fill_value=0.0)
            current = weights_series.reindex(combined_index, fill_value=0.0)
            turnover += 0.5 * float((current - prev).abs().sum())
        prev_weights = weights_series

        end_date = rebalance_dates[idx + 1] if idx + 1 < len(rebalance_dates) else None
        if end_date is None:
            mask = calendar > rebalance_date
        else:
            mask = (calendar > rebalance_date) & (calendar <= end_date)
        window = calendar[mask]
        if window.empty:
            continue
        window_returns = returns.loc[window, weights_series.index].fillna(0.0)
        series.loc[window] = window_returns.mul(weights_series, axis=1).sum(axis=1)

    return series, turnover, note


def _shift_month_end(date: pd.Timestamp, months: int) -> pd.Timestamp | None:
    if date is None:
        return None
    shifted = (date + pd.DateOffset(months=months)).to_period("M").to_timestamp("M")
    return pd.Timestamp(shifted)


def _calendar_on_or_before(
    calendar: pd.DatetimeIndex, date: pd.Timestamp
) -> pd.Timestamp | None:
    eligible = calendar[calendar <= date]
    if eligible.empty:
        return None
    return pd.Timestamp(eligible.max())


def _attach_market_proxy(
    baselines: pd.DataFrame,
    *,
    calendar: pd.DatetimeIndex,
    data_path: Path | None,
    status: dict[str, Any],
) -> pd.DataFrame:
    path, reason = _resolve_market_proxy_path(data_path)
    if path is None or not path.exists():
        status["market_proxy"] = {"status": "missing", "reason": reason or "market proxy not found"}
        baselines["market_proxy"] = np.nan
        return baselines

    returns = _load_proxy_returns(path, calendar)
    baselines["market_proxy"] = returns.to_numpy()
    status["market_proxy"] = {
        "status": "ok" if returns.notna().any() else "missing",
        "reason": reason or f"source={path}",
        "turnover": 0.0,
    }
    return baselines


def _resolve_market_proxy_path(data_path: Path | None) -> tuple[Path | None, str | None]:
    candidates: list[tuple[Path, str]] = []
    if data_path:
        candidates.extend(
            [
                (data_path / "crsp_vwretd.csv", "CRSP vwretd"),
                (data_path / "vwretd.csv", "CRSP vwretd"),
                (data_path / "market_proxy.csv", "market_proxy.csv"),
                (data_path / "SPY.csv", "SPY fallback"),
            ]
        )
        parent = data_path.parent
        candidates.extend(
            [
                (parent / "crsp_vwretd.csv", "CRSP vwretd"),
                (parent / "vwretd.csv", "CRSP vwretd"),
                (parent / "SPY.csv", "SPY fallback"),
            ]
        )
    repo_spy = Path("data/SPY.csv").resolve()
    candidates.append((repo_spy, "SPY fallback"))

    for path, label in candidates:
        if path.exists():
            return path, label
    return None, "missing market proxy"


def _load_proxy_returns(path: Path, calendar: pd.DatetimeIndex) -> pd.Series:
    df = pd.read_csv(path)
    if df.empty:
        return pd.Series(index=calendar, dtype=float)
    date_col = "date" if "date" in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df = df.set_index(date_col).sort_index()

    return_cols = [col for col in df.columns if col.lower() in {"vwretd", "return", "returns", "ret"}]
    if return_cols:
        series = df[return_cols[0]].astype(float)
        return series.reindex(calendar, fill_value=0.0)

    price_cols = [col for col in df.columns if col.lower() in {"close", "price", "adj_close"}]
    if price_cols:
        prices = df[price_cols[0]].astype(float)
        prices = prices.reindex(calendar, method="ffill")
        return prices.pct_change(fill_method=None).fillna(0.0)

    if len(df.columns) == 1:
        series = df.iloc[:, 0].astype(float)
        series = series.reindex(calendar, method="ffill")
        return series.pct_change().fillna(0.0)

    return pd.Series(index=calendar, dtype=float)


def _attach_cash_rf(
    baselines: pd.DataFrame,
    *,
    calendar: pd.DatetimeIndex,
    data_path: Path | None,
    status: dict[str, Any],
) -> pd.DataFrame:
    rf_series, source = _load_rf_series(calendar, data_path)
    baselines["cash_rf"] = rf_series.to_numpy()
    status["cash_rf"] = {
        "status": "ok" if rf_series.notna().any() else "missing",
        "reason": source,
        "turnover": 0.0,
    }
    return baselines


def _load_rf_series(
    calendar: pd.DatetimeIndex, data_path: Path | None
) -> tuple[pd.Series, str]:
    candidates: list[tuple[Path, str]] = []
    if data_path:
        candidates.extend(
            [
                (data_path / "rf.csv", "rf.csv"),
                (data_path / "factors.csv", "factors.csv"),
                (data_path / "ff5_mom_daily.csv", "ff5_mom_daily.csv"),
            ]
        )
        parent = data_path.parent
        candidates.extend(
            [
                (parent / "factors/ff5_mom_daily.csv", "factors/ff5_mom_daily.csv"),
                (parent / "factors/ff3_sample.csv", "factors/ff3_sample.csv"),
            ]
        )

    candidates.extend(
        [
            (Path("data/factors/ff5_mom_daily.csv"), "data/factors/ff5_mom_daily.csv"),
            (Path("data/factors/ff3_sample.csv"), "data/factors/ff3_sample.csv"),
        ]
    )

    for path, label in candidates:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if df.empty:
            continue
        date_col = "date" if "date" in df.columns else df.columns[0]
        if "RF" not in df.columns:
            continue
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])
        df = df.set_index(date_col).sort_index()
        series = df["RF"].astype(float)
        series = series.reindex(calendar, method="ffill").fillna(0.0)
        return series, f"RF from {label}"

    return pd.Series(0.0, index=calendar), "RF unavailable; using 0"


def _enforce_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in BASELINE_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    df = df[list(BASELINE_COLUMNS)]
    return df


def _write_baselines(
    df: pd.DataFrame,
    baselines_path: Path,
    status: Mapping[str, Any],
    status_path: Path,
) -> None:
    output = df.copy()
    if "date" in output.columns:
        output["date"] = pd.to_datetime(output["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    baselines_path.write_text(output.to_csv(index=False), encoding="utf-8")
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")


def _write_missing_flagship_readme(artifact_dir: Path, reason: str) -> None:
    readme_path = artifact_dir / "baselines_README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Baselines",
                "",
                "The flagship return series was not available when baselines were generated.",
                f"- Reason: {reason}",
                "",
                "Baselines were written with NaN placeholders; regenerate after fixing artifacts.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _format_metric(value: object) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "n/a"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "n/a"


def _format_pct(value: object) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "n/a"
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "n/a"


def _format_turnover(value: object) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "n/a"
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"


def _to_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
