"""Frozen six-candidate selection runner for the CRSP-v2 flagship protocol."""

from __future__ import annotations

import csv
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from zipfile import ZipFile

import numpy as np
import pandas as pd

from microalpha.risk_stats import sharpe_stats

from .crsp_v2 import (
    CRSPV2Error,
    apply_constrained_trade_capacity,
    apply_trade_capacity,
    audit_source_protocol,
    estimate_rebalance_cost,
    industry_neutral_weights,
    load_protocol,
    protocol_sha256,
    sha256_file,
)

HAC_LAGS_MONTHLY = 3
SIGNAL_DEFINITIONS = {
    "mom_12_2": (
        "formation lags 1..11; equivalently realization-relative months t-12..t-2"
    ),
    "mom_6_2": (
        "formation lags 1..5; equivalently realization-relative months t-6..t-2"
    ),
    "blend_12_2_6_2": "equal arithmetic blend of the two frozen lagged signals",
    "residual_mom_12_2": (
        "sum of stock return minus contemporaneous FF12-industry median return "
        "over formation lags 1..11"
    ),
    "residual_mom_6_2": (
        "sum of stock return minus contemporaneous FF12-industry median return "
        "over formation lags 1..5"
    ),
    "residual_mom_12_2_minus_reversal_1_1": (
        "residual_mom_12_2 minus the formation-month stock return minus "
        "contemporaneous FF12-industry median return"
    ),
    "low_volatility_126d": (
        "negative point-in-time trailing 126-session daily-return volatility; "
        "low-volatility securities rank above high-volatility securities"
    ),
    "short_term_reversal_1_1": (
        "negative formation-month stock return minus contemporaneous FF12-industry "
        "median return, observed at month-end for next-month execution"
    ),
    "qvpi_annual_composite": (
        "equal-family annual book-to-market, gross-plus-operating profitability, "
        "conservative investment, and accrual-quality ranks within formation-month "
        "FF12 industry, using a fixed six-month accounting availability lag"
    ),
}


@dataclass(frozen=True)
class StrategyResult:
    monthly: pd.DataFrame
    metrics: dict[str, Any]


def _sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:  # pragma: no cover - non-Git execution
        return "unknown"


def _json_dump(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )


def _validate_selection_inputs(
    protocol_path: Path,
    panel_path: Path,
    panel_manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = load_protocol(protocol_path)
    panel_manifest = json.loads(panel_manifest_path.read_text(encoding="utf-8"))
    if panel_manifest.get("stage") != "selection":
        raise CRSPV2Error("Selection runner requires a selection-stage panel")
    if panel_manifest.get("protocol_sha256") != protocol_sha256(protocol_path):
        raise CRSPV2Error("Panel and protocol digests disagree")
    if panel_manifest.get("protocol_id") != protocol.get("protocol_id"):
        raise CRSPV2Error("Panel and protocol identifiers disagree")
    expected_panel_sha = str(panel_manifest.get("output", {}).get("sha256") or "")
    if not expected_panel_sha or sha256_file(panel_path) != expected_panel_sha:
        raise CRSPV2Error("Panel digest does not match its manifest")
    access = panel_manifest.get("access_contract", {})
    if access.get("primary_holdout_partitions_opened_for_outcome_rows") is not False:
        raise CRSPV2Error("Selection panel holdout access receipt is not sealed")
    if int(access.get("primary_post_validation_rows_materialized", -1)) != 0:
        raise CRSPV2Error("Selection panel contains post-validation daily rows")
    if int(access.get("post_validation_stocknames_rows_materialized", -1)) != 0:
        raise CRSPV2Error("Selection panel contains post-validation stocknames rows")
    if int(access.get("post_validation_delisting_rows_materialized", -1)) != 0:
        raise CRSPV2Error("Selection panel contains post-validation delisting rows")
    validation_end = str(protocol["windows"]["validation"]["end"])
    if str(panel_manifest.get("output", {}).get("max_date")) > validation_end:
        raise CRSPV2Error("Selection panel extends beyond validation")
    return protocol, panel_manifest


def _load_signal_frame(panel_path: Path, protocol: Mapping[str, Any]) -> pd.DataFrame:
    """Compute the three frozen signals without using the current month's return."""

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise CRSPV2Error("DuckDB is required for CRSP-v2 selection") from exc

    validation_start = pd.Timestamp(protocol["windows"]["validation"]["start"])
    validation_end = pd.Timestamp(protocol["windows"]["validation"]["end"])
    first_formation = validation_start - pd.offsets.MonthEnd(1)
    connection = duckdb.connect()
    try:
        frame = connection.execute(f"""
            WITH history AS (
                SELECT
                    *,
                    count(monthly_total_return) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN 11 PRECEDING AND 1 PRECEDING
                    ) AS mom12_count,
                    min(formation_date) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN 11 PRECEDING AND 1 PRECEDING
                    ) AS mom12_start,
                    product(1.0 + monthly_total_return) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN 11 PRECEDING AND 1 PRECEDING
                    ) - 1.0 AS mom12_raw,
                    count(monthly_total_return) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
                    ) AS mom6_count,
                    min(formation_date) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
                    ) AS mom6_start,
                    product(1.0 + monthly_total_return) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
                    ) - 1.0 AS mom6_raw
                FROM read_parquet({_sql_literal(panel_path)})
            ), scored AS (
                SELECT
                    permno,
                    formation_date,
                    industry,
                    eligible_at_formation,
                    price,
                    adv_60_usd,
                    volatility_126d,
                    full_spread_bps,
                    monthly_total_return,
                    delisting_pseudo_days,
                    CASE
                        WHEN mom12_count = 11
                         AND date_diff('month', mom12_start, formation_date) = 11
                        THEN mom12_raw
                    END AS mom_12_2,
                    CASE
                        WHEN mom6_count = 5
                         AND date_diff('month', mom6_start, formation_date) = 5
                        THEN mom6_raw
                    END AS mom_6_2
                FROM history
            )
            SELECT
                *,
                CASE
                    WHEN mom_12_2 IS NOT NULL AND mom_6_2 IS NOT NULL
                    THEN (mom_12_2 + mom_6_2) / 2.0
                END AS blend_12_2_6_2
            FROM scored
            WHERE formation_date BETWEEN DATE {_sql_literal(first_formation.date())}
                                     AND DATE {_sql_literal(validation_end.date())}
            ORDER BY formation_date, permno
            """).df()
    finally:
        connection.close()
    frame["formation_date"] = pd.to_datetime(frame["formation_date"])
    if frame.duplicated(["formation_date", "permno"]).any():
        raise CRSPV2Error("Selection frame formation-date/PERMNO keys are not unique")
    return frame


def _classic_weights(
    snapshot: pd.DataFrame,
    *,
    score_column: str,
    sleeve_fraction: float,
    max_single_name_weight: float,
) -> pd.Series:
    ranked = snapshot.dropna(subset=[score_column]).sort_values(
        [score_column, "permno"], ascending=[False, True]
    )
    count = len(ranked)
    sleeve_count = min(max(int(math.floor(count * sleeve_fraction)), 1), count // 2)
    if sleeve_count < 1:
        raise CRSPV2Error("Classic momentum baseline has no two-sided sleeve")
    per_name = 0.5 / sleeve_count
    if per_name > max_single_name_weight + 1e-12:
        raise CRSPV2Error("Classic momentum baseline violates the name cap")
    weights = pd.Series(0.0, index=ranked["permno"].astype(int))
    weights.loc[ranked.head(sleeve_count)["permno"].astype(int)] = per_name
    weights.loc[ranked.tail(sleeve_count)["permno"].astype(int)] = -per_name
    return weights.sort_index()


def _month_metrics(returns: pd.Series) -> dict[str, float]:
    values = pd.to_numeric(returns, errors="coerce").dropna().astype(float)
    if values.empty or values.le(-1.0).any():
        raise CRSPV2Error("Monthly return stream is empty or bankrupt")
    sharpe = sharpe_stats(values, periods=12, hac_lags=HAC_LAGS_MONTHLY)
    equity = (1.0 + values).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    cagr = float(equity.iloc[-1] ** (12.0 / len(values)) - 1.0)
    return {
        "net_sharpe_hac": float(sharpe["sharpe"]),
        "net_sharpe_hac_se": float(sharpe["se"]),
        "net_sharpe_hac_tstat": float(sharpe["tstat"]),
        "cagr": cagr,
        "max_drawdown": float(-drawdown.min()),
        "cumulative_return": float(equity.iloc[-1] - 1.0),
    }


def _run_strategy(
    frame: pd.DataFrame,
    protocol: Mapping[str, Any],
    *,
    signal: str,
    weighting: str,
    classic: bool = False,
    cost_multiplier: float = 1.0,
    annual_short_borrow_bps: float | None = None,
) -> StrategyResult:
    if signal not in SIGNAL_DEFINITIONS:
        raise CRSPV2Error(f"Unknown signal: {signal}")
    if cost_multiplier < 0.0:
        raise CRSPV2Error("Cost multiplier must be non-negative")

    portfolio = protocol["portfolio"]
    common = protocol["candidate_grid"]["common_rules"]
    costs = protocol["costs"]["primary"]
    capital = float(portfolio["capital_usd"])
    max_name = float(portfolio["max_single_name_weight"])
    max_industry = float(portfolio["max_industry_gross_weight"])
    max_participation = float(portfolio["max_participation_of_60d_adv"])
    sleeve_fraction = float(common["long_fraction"])
    borrow_bps = (
        float(costs["annual_short_borrow_bps"])
        if annual_short_borrow_bps is None
        else float(annual_short_borrow_bps)
    )

    validation_start = pd.Timestamp(protocol["windows"]["validation"]["start"])
    validation_end = pd.Timestamp(protocol["windows"]["validation"]["end"])
    realization_dates = pd.date_range(validation_start, validation_end, freq="ME")
    if len(realization_dates) != 72:
        raise CRSPV2Error("Frozen validation window must contain 72 months")
    by_date = {
        pd.Timestamp(date): group.set_index("permno", drop=False).sort_index()
        for date, group in frame.groupby("formation_date", sort=True)
    }

    previous = pd.Series(dtype=float)
    prior_adv = pd.Series(dtype=float)
    prior_industry = pd.Series(dtype="object")
    rows: list[dict[str, Any]] = []
    for realization_date in realization_dates:
        formation_date = realization_date - pd.offsets.MonthEnd(1)
        if formation_date not in by_date or realization_date not in by_date:
            raise CRSPV2Error(
                f"Missing formation or realization month: {formation_date.date()}"
            )
        formation = by_date[formation_date]
        realization = by_date[realization_date]
        eligible = formation.loc[
            formation["eligible_at_formation"].fillna(False).astype(bool)
            & formation[signal].notna()
        ].copy()
        if weighting == "inverse_vol_126d":
            eligible = eligible.loc[
                pd.to_numeric(eligible["volatility_126d"], errors="coerce").gt(0.0)
            ]
        eligible = eligible.reset_index(drop=True)
        if classic:
            target = _classic_weights(
                eligible,
                score_column=signal,
                sleeve_fraction=sleeve_fraction,
                max_single_name_weight=max_name,
            )
        else:
            target = industry_neutral_weights(
                eligible,
                score_column=signal,
                weighting=weighting,
                sleeve_fraction=sleeve_fraction,
                target_gross=float(portfolio["target_gross_exposure"]),
                max_industry_gross_weight=max_industry,
                max_single_name_weight=max_name,
            )

        target = target.loc[target.abs().gt(1e-15)]
        previous = previous.loc[previous.abs().gt(1e-15)]
        union = previous.index.union(target.index)
        current_adv = pd.to_numeric(
            formation["adv_60_usd"].reindex(union), errors="coerce"
        )
        adv = current_adv.combine_first(prior_adv.reindex(union))
        if adv.isna().any() or adv.le(0.0).any():
            raise CRSPV2Error("Active trade lacks positive point-in-time ADV")
        point_in_time_industry = formation["industry"].reindex(union).combine_first(
            prior_industry.reindex(union)
        )
        next_price = pd.to_numeric(realization["price"].reindex(union), errors="coerce")
        tradable = next_price.abs().gt(0.0).fillna(False)
        untradable_target_names = int(
            (target.reindex(union, fill_value=0.0).ne(0.0) & ~tradable).sum()
        )
        if classic:
            capacity = apply_trade_capacity(
                previous,
                target,
                adv,
                capital_usd=capital,
                max_participation=max_participation,
                max_single_name_weight=max_name,
                tradable=tradable,
            )
        else:
            capacity = apply_constrained_trade_capacity(
                previous,
                target,
                adv,
                point_in_time_industry,
                capital_usd=capital,
                max_participation=max_participation,
                max_single_name_weight=max_name,
                max_industry_gross_weight=max_industry,
                tradable=tradable,
            )
        executed = capacity.executed_weights.loc[
            capacity.executed_weights.abs().gt(1e-15)
        ]
        cost_index = previous.index.union(executed.index)
        spreads = pd.to_numeric(
            formation["full_spread_bps"].reindex(cost_index), errors="coerce"
        )
        holding_days = int((realization_date - formation_date).days)
        cost = estimate_rebalance_cost(
            previous,
            executed,
            adv.reindex(cost_index),
            spreads,
            capital_usd=capital,
            commission_bps_each_side=float(costs["commission_bps_each_side"]),
            impact_bps_at_one_percent_adv=10.0,
            annual_short_borrow_bps=borrow_bps,
            holding_days=holding_days,
            fallback_full_spread_bps=float(costs["fallback_full_spread_bps"]),
        )
        nonborrow_cost = (
            cost["commission_dollars"]
            + cost["spread_dollars"]
            + cost["impact_dollars"]
        ) * cost_multiplier
        total_cost = nonborrow_cost + cost["borrow_dollars"]

        realized_returns = pd.to_numeric(
            realization["monthly_total_return"].reindex(executed.index),
            errors="coerce",
        )
        realization_present = pd.Series(
            executed.index.isin(realization.index), index=executed.index
        )
        realized_delisting = (
            pd.to_numeric(
                realization["delisting_pseudo_days"].reindex(executed.index),
                errors="coerce",
            )
            .fillna(0)
            .gt(0)
        )
        executed_tradable = tradable.reindex(executed.index, fill_value=False)
        executable_or_terminal = executed_tradable | realized_delisting
        missing_executable_returns = (
            realization_present & executable_or_terminal & realized_returns.isna()
        )
        if missing_executable_returns.any():
            raise CRSPV2Error(
                "An executable or delisting observation lacks its CIZ return"
            )
        absent_rows_zero_marked = int((~realization_present).sum())
        present_no_session_rows_zero_marked = int(
            (
                realization_present
                & ~executable_or_terminal
                & realized_returns.isna()
            ).sum()
        )
        realized_returns = realized_returns.fillna(0.0)
        gross_return = float((executed * realized_returns).sum())
        net_return = gross_return - total_cost / capital
        if net_return <= -1.0:
            raise CRSPV2Error("Portfolio equity is non-positive")
        post = executed * (1.0 + realized_returns) / (1.0 + net_return)
        delisted = realized_delisting.reindex(post.index, fill_value=False)
        delisted_positions = int((delisted & executed.reindex(post.index).ne(0.0)).sum())
        post.loc[delisted] = 0.0
        previous = post.loc[post.abs().gt(1e-15)].sort_index()
        prior_adv = adv.reindex(previous.index).copy()
        prior_industry = point_in_time_industry.reindex(previous.index).copy()

        target_industry = eligible.set_index("permno")["industry"].reindex(target.index)
        target_industry_gross = target.abs().groupby(target_industry).sum()
        executed_industry = point_in_time_industry.reindex(executed.index)
        if executed_industry.isna().any():
            raise CRSPV2Error("Executed holding lacks point-in-time industry")
        executed_industry_gross = executed.abs().groupby(executed_industry).sum()
        executed_industry_net = executed.groupby(executed_industry).sum()
        rows.append(
            {
                "formation_date": formation_date,
                "realization_date": realization_date,
                "gross_return": gross_return,
                "net_return": net_return,
                "zero_cost_return": gross_return,
                "one_way_turnover": float(cost["one_way_turnover"]),
                "requested_turnover": float(capacity.requested_turnover),
                "fill_ratio": float(capacity.fill_ratio),
                "target_long_names": int(target.gt(0.0).sum()),
                "target_short_names": int(target.lt(0.0).sum()),
                "executed_names": int(executed.ne(0.0).sum()),
                "target_gross": float(target.abs().sum()),
                "executed_gross": float(executed.abs().sum()),
                "executed_net": float(executed.sum()),
                "maximum_executed_name_weight": float(executed.abs().max()),
                "max_target_industry_gross": float(target_industry_gross.max()),
                "max_executed_industry_gross": float(executed_industry_gross.max()),
                "max_abs_executed_industry_net": float(
                    executed_industry_net.abs().max()
                ),
                "delisted_positions_liquidated": delisted_positions,
                "untradable_target_names": untradable_target_names,
                "absent_rows_zero_marked": absent_rows_zero_marked,
                "present_no_session_rows_zero_marked": (
                    present_no_session_rows_zero_marked
                ),
                "total_cost_dollars": float(total_cost),
                "commission_dollars": float(cost["commission_dollars"] * cost_multiplier),
                "spread_dollars": float(cost["spread_dollars"] * cost_multiplier),
                "impact_dollars": float(cost["impact_dollars"] * cost_multiplier),
                "borrow_dollars": float(cost["borrow_dollars"]),
                "fallback_spread_count": int(cost["fallback_spread_count"]),
                "constrained_names": len(capacity.constrained_names),
            }
        )

    monthly = pd.DataFrame(rows)
    monthly_metrics = _month_metrics(monthly["net_return"])
    yearly_sharpes: list[float] = []
    yearly_returns: list[float] = []
    nondegenerate_years = 0
    for _, group in monthly.groupby(monthly["realization_date"].dt.year, sort=True):
        returns = group["net_return"]
        if len(group) == 12 and float(returns.std(ddof=0)) > 1e-12:
            nondegenerate_years += 1
        yearly_sharpes.append(
            float(sharpe_stats(returns, periods=12, hac_lags=HAC_LAGS_MONTHLY)["sharpe"])
        )
        yearly_returns.append(float((1.0 + returns).prod() - 1.0))

    sleeve_counts = pd.concat(
        [monthly["target_long_names"], monthly["target_short_names"]],
        ignore_index=True,
    )
    reasons: list[str] = []
    if nondegenerate_years != 6:
        reasons.append("not_all_six_validation_years_nondegenerate")
    if monthly_metrics["max_drawdown"] > 0.35 + 1e-12:
        reasons.append("validation_max_drawdown_gt_35pct")
    if float(sleeve_counts.median()) < 30.0:
        reasons.append("median_names_per_sleeve_lt_30")
    if monthly["max_target_industry_gross"].max() > max_industry + 1e-12 and not classic:
        reasons.append("target_industry_gross_cap_breach")
    if monthly["max_executed_industry_gross"].max() > max_industry + 1e-9 and not classic:
        reasons.append("executed_industry_gross_cap_breach")
    if monthly["max_abs_executed_industry_net"].max() > 1e-9 and not classic:
        reasons.append("executed_industry_net_neutrality_breach")
    if monthly["executed_net"].abs().max() > 1e-9 and not classic:
        reasons.append("executed_portfolio_net_neutrality_breach")
    if monthly["maximum_executed_name_weight"].max() > max_name + 1e-9:
        reasons.append("executed_single_name_cap_breach")
    if monthly["target_gross"].sub(1.0).abs().max() > 1e-10:
        reasons.append("target_gross_mismatch")

    metrics: dict[str, Any] = {
        **monthly_metrics,
        "eligible": not reasons,
        "eligibility_reasons": reasons,
        "validation_months": len(monthly),
        "nondegenerate_validation_years": nondegenerate_years,
        "median_calendar_year_net_sharpe_hac": float(np.median(yearly_sharpes)),
        "worst_calendar_year_net_return": float(min(yearly_returns)),
        "total_one_way_turnover": float(monthly["one_way_turnover"].sum()),
        "mean_monthly_one_way_turnover": float(monthly["one_way_turnover"].mean()),
        "median_names_per_sleeve": float(sleeve_counts.median()),
        "minimum_names_per_sleeve": int(sleeve_counts.min()),
        "mean_fill_ratio": float(monthly["fill_ratio"].mean()),
        "minimum_fill_ratio": float(monthly["fill_ratio"].min()),
        "total_cost_dollars": float(monthly["total_cost_dollars"].sum()),
        "mean_executed_gross": float(monthly["executed_gross"].mean()),
        "maximum_absolute_executed_net": float(monthly["executed_net"].abs().max()),
        "maximum_absolute_executed_industry_net": float(
            monthly["max_abs_executed_industry_net"].max()
        ),
        "maximum_executed_industry_gross": float(
            monthly["max_executed_industry_gross"].max()
        ),
        "maximum_executed_name_weight": float(
            monthly["maximum_executed_name_weight"].max()
        ),
        "delisted_positions_liquidated": int(
            monthly["delisted_positions_liquidated"].sum()
        ),
        "untradable_target_names": int(monthly["untradable_target_names"].sum()),
        "absent_rows_zero_marked": int(monthly["absent_rows_zero_marked"].sum()),
        "present_no_session_rows_zero_marked": int(
            monthly["present_no_session_rows_zero_marked"].sum()
        ),
        "maximum_target_industry_gross": float(
            monthly["max_target_industry_gross"].max()
        ),
        "hac_lags_monthly": HAC_LAGS_MONTHLY,
    }
    return StrategyResult(monthly=monthly, metrics=metrics)


def _read_daily_factor_zip(path: Path, value_name: str) -> pd.Series:
    with ZipFile(path) as archive:
        member = archive.namelist()[0]
        lines = archive.read(member).decode("utf-8", errors="replace").splitlines()
    dates: list[pd.Timestamp] = []
    values: list[float] = []
    for row in csv.reader(lines):
        key = row[0].strip() if row else ""
        if len(key) != 8 or not key.isdigit() or len(row) < 2:
            continue
        try:
            value = float(row[1].strip())
        except ValueError:
            continue
        if value <= -99.0:
            continue
        dates.append(pd.to_datetime(key, format="%Y%m%d"))
        values.append(value / 100.0)
    if not values:
        raise CRSPV2Error(f"No daily observations parsed for {value_name}")
    series = pd.Series(values, index=pd.DatetimeIndex(dates), name=value_name)
    return (1.0 + series).groupby(series.index.to_period("M")).prod() - 1.0


def _read_ff5_rf_zip(path: Path) -> pd.Series:
    with ZipFile(path) as archive:
        member = archive.namelist()[0]
        lines = archive.read(member).decode("utf-8", errors="replace").splitlines()
    dates: list[pd.Timestamp] = []
    values: list[float] = []
    for row in csv.reader(lines):
        key = row[0].strip() if row else ""
        if len(key) != 8 or not key.isdigit() or len(row) < 7:
            continue
        try:
            value = float(row[6].strip())
        except ValueError:
            continue
        if value <= -99.0:
            continue
        dates.append(pd.to_datetime(key, format="%Y%m%d"))
        values.append(value / 100.0)
    series = pd.Series(values, index=pd.DatetimeIndex(dates), name="cash_rf")
    return (1.0 + series).groupby(series.index.to_period("M")).prod() - 1.0


def _read_momentum_deciles_zip(path: Path) -> pd.Series:
    with ZipFile(path) as archive:
        member = archive.namelist()[0]
        lines = archive.read(member).decode("utf-8", errors="replace").splitlines()
    started = False
    dates: list[pd.Period] = []
    values: list[float] = []
    for row in csv.reader(lines):
        first = row[0].strip() if row else ""
        if not started:
            if len(row) >= 11 and row[1].strip() == "Lo PRIOR":
                started = True
            continue
        if len(first) != 6 or not first.isdigit() or len(row) < 11:
            if dates:
                break
            continue
        low = float(row[1].strip())
        high = float(row[10].strip())
        if low <= -99.0 or high <= -99.0:
            continue
        dates.append(pd.Period(pd.to_datetime(first, format="%Y%m"), freq="M"))
        values.append((high - low) / 100.0)
    if not values:
        raise CRSPV2Error("No monthly Ken French momentum deciles parsed")
    return pd.Series(values, index=pd.PeriodIndex(dates), name="kf_decile_wml")


def _read_dsi_monthly(path: Path) -> pd.DataFrame:
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise CRSPV2Error("DuckDB is required for CRSP DSI baselines") from exc
    connection = duckdb.connect()
    try:
        frame = connection.execute(f"""
            SELECT
                last_day(try_cast(date AS DATE)) AS date,
                product(1.0 + try_cast(vwretd AS DOUBLE)) - 1.0 AS crsp_vw_market,
                product(1.0 + try_cast(ewretd AS DOUBLE)) - 1.0 AS crsp_ew_market
            FROM read_csv({_sql_literal(path)}, header=true, all_varchar=true)
            WHERE try_cast(date AS DATE) IS NOT NULL
            GROUP BY last_day(try_cast(date AS DATE))
            ORDER BY date
            """).df()
    finally:
        connection.close()
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.set_index(frame["date"].dt.to_period("M")).drop(columns="date")


def _baseline_table(
    protocol: Mapping[str, Any],
    audit: Mapping[str, Any],
    selected: StrategyResult,
    classic: StrategyResult,
    protocol_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    public = {item["role"]: Path(item["path"]) for item in audit["public"]["files"]}
    dsi = _read_dsi_monthly(Path(audit["market"]["path"]))
    mom = _read_daily_factor_zip(public["momentum_daily"], "ken_french_mom")
    rf = _read_ff5_rf_zip(public["ff5_daily"])
    deciles = _read_momentum_deciles_zip(public["momentum_deciles_monthly"])
    periods = pd.period_range(
        pd.Timestamp(protocol["windows"]["validation"]["start"]),
        pd.Timestamp(protocol["windows"]["validation"]["end"]),
        freq="M",
    )
    selected_series = pd.Series(
        selected.monthly["net_return"].to_numpy(), index=periods, name="selected_flagship"
    )
    classic_series = pd.Series(
        classic.monthly["net_return"].to_numpy(),
        index=periods,
        name="identical_universe_classic_mom_12_2",
    )
    monthly = pd.concat(
        [
            selected_series,
            classic_series,
            dsi.reindex(periods),
            mom.reindex(periods),
            deciles.reindex(periods),
            rf.reindex(periods),
        ],
        axis=1,
    )
    monthly.index.name = "month"
    if monthly.isna().any().any():
        missing = monthly.isna().sum()
        raise CRSPV2Error(f"Baseline validation coverage is incomplete: {missing.to_dict()}")
    rows: list[dict[str, Any]] = []
    for column in monthly.columns:
        metrics = _month_metrics(monthly[column])
        if column == "selected_flagship":
            turnover = selected.metrics["total_one_way_turnover"]
        elif column == "identical_universe_classic_mom_12_2":
            turnover = classic.metrics["total_one_way_turnover"]
        else:
            turnover = None
        rows.append(
            {
                "baseline_id": column,
                **metrics,
                "months": len(monthly),
                "total_one_way_turnover": turnover,
                "classification": (
                    "investable_net"
                    if column == "selected_flagship"
                    else (
                        "constructed_net_academic_no_industry_neutrality"
                        if column == "identical_universe_classic_mom_12_2"
                        else "external_reference_gross"
                    )
                ),
                "source_path": None,
                "source_sha256": None,
            }
        )
    rows.append(_legacy_baseline_row(protocol, protocol_path))
    return pd.DataFrame(rows), monthly.reset_index()


def _legacy_baseline_row(
    protocol: Mapping[str, Any], protocol_path: Path
) -> dict[str, Any]:
    specs = [
        item
        for item in protocol.get("baselines", [])
        if item.get("id") == "legacy_40_name_wrds_run"
    ]
    if len(specs) != 1:
        raise CRSPV2Error("Frozen legacy baseline specification is missing or duplicated")
    source = Path(str(specs[0]["source"]))
    if not source.is_absolute():
        source = protocol_path.parents[2] / source
    source = source.resolve()
    evidence_path = source / "snippet.md" if source.is_dir() else source
    if not evidence_path.is_file():
        raise CRSPV2Error(f"Legacy baseline evidence is missing: {evidence_path}")
    text = evidence_path.read_text(encoding="utf-8")

    def extract(pattern: str, label: str) -> float:
        match = re.search(pattern, text)
        if match is None:
            raise CRSPV2Error(f"Legacy baseline evidence lacks {label}")
        return float(match.group(1))

    return {
        "baseline_id": "legacy_40_name_wrds_run",
        "net_sharpe_hac": extract(r"Sharpe_HAC\s+(-?[0-9.]+)", "Sharpe_HAC"),
        "net_sharpe_hac_se": None,
        "net_sharpe_hac_tstat": None,
        "cagr": extract(r"CAGR\s+(-?[0-9.]+)%", "CAGR") / 100.0,
        "max_drawdown": extract(r"MaxDD\s+([0-9.]+)%", "MaxDD") / 100.0,
        "cumulative_return": None,
        "months": 24,
        "total_one_way_turnover": None,
        "reported_turnover_dollars": extract(
            r"turnover\s+\$([0-9.]+)MM", "turnover"
        )
        * 1_000_000.0,
        "classification": "historical_noncomparable",
        "source_path": str(evidence_path),
        "source_sha256": sha256_file(evidence_path),
        "notes": (
            "Recovered historical headline only; source run artifacts and comparable "
            "current-universe provenance are incomplete"
        ),
    }


def _candidate_row(signal: str, weighting: str, result: StrategyResult) -> dict[str, Any]:
    candidate_id = f"{signal}__{weighting}"
    return {
        "candidate_id": candidate_id,
        "signal": signal,
        "weighting": weighting,
        **result.metrics,
    }


def _rank_candidates(candidates: pd.DataFrame) -> pd.DataFrame:
    ranked = candidates.sort_values(
        [
            "eligible",
            "median_calendar_year_net_sharpe_hac",
            "worst_calendar_year_net_return",
            "total_one_way_turnover",
            "candidate_id",
        ],
        ascending=[False, False, False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    ranked.insert(0, "selection_rank", np.arange(1, len(ranked) + 1))
    return ranked


def run_selection(
    protocol_path: str | Path,
    panel_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Run all six validation candidates and atomically freeze the winner."""

    protocol_path = Path(protocol_path).expanduser().resolve()
    panel_path = Path(panel_path).expanduser().resolve()
    panel_manifest_path = panel_path.with_suffix(panel_path.suffix + ".manifest.json")
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise CRSPV2Error(f"Refusing to overwrite selection output: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    protocol, panel_manifest = _validate_selection_inputs(
        protocol_path, panel_path, panel_manifest_path
    )
    audit = audit_source_protocol(protocol_path)
    frame = _load_signal_frame(panel_path, protocol)

    results: dict[str, StrategyResult] = {}
    candidate_rows: list[dict[str, Any]] = []
    for signal in protocol["candidate_grid"]["signals"]:
        for weighting in protocol["candidate_grid"]["weighting"]:
            result = _run_strategy(
                frame,
                protocol,
                signal=str(signal),
                weighting=str(weighting),
            )
            candidate_id = f"{signal}__{weighting}"
            results[candidate_id] = result
            candidate_rows.append(_candidate_row(str(signal), str(weighting), result))
    if len(candidate_rows) != int(protocol["candidate_grid"]["total_candidates"]):
        raise CRSPV2Error("Candidate grid did not produce the predeclared six rows")

    candidates = _rank_candidates(pd.DataFrame(candidate_rows))
    eligible = candidates.loc[candidates["eligible"].astype(bool)]
    if eligible.empty:
        raise CRSPV2Error("No candidate passes the frozen validation eligibility gates")
    selected_row = eligible.iloc[0]
    selected_id = str(selected_row["candidate_id"])
    selected = results[selected_id]

    classic = _run_strategy(
        frame,
        protocol,
        signal="mom_12_2",
        weighting="equal",
        classic=True,
    )
    baselines, baseline_monthly = _baseline_table(
        protocol, audit, selected, classic, protocol_path
    )

    stress_rows: list[dict[str, Any]] = []
    for borrow in protocol["costs"]["stress"]["annual_short_borrow_bps"]:
        for multiplier in protocol["costs"]["stress"]["cost_multiplier"]:
            result = _run_strategy(
                frame,
                protocol,
                signal=str(selected_row["signal"]),
                weighting=str(selected_row["weighting"]),
                cost_multiplier=float(multiplier),
                annual_short_borrow_bps=float(borrow),
            )
            stress_rows.append(
                {
                    "annual_short_borrow_bps": float(borrow),
                    "nonborrow_cost_multiplier": float(multiplier),
                    **result.metrics,
                }
            )
    stress = pd.DataFrame(stress_rows)

    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent)
    )
    try:
        source_manifest = {
            "schema_version": "microalpha-crsp-v2-selection-sources/v1",
            "protocol_path": str(protocol_path),
            "protocol_sha256": protocol_sha256(protocol_path),
            "panel_path": str(panel_path),
            "panel_sha256": sha256_file(panel_path),
            "panel_manifest_path": str(panel_manifest_path),
            "panel_manifest_sha256": sha256_file(panel_manifest_path),
            "primary_manifest": audit["primary"]["manifest"],
            "primary_manifest_sha256": audit["primary"]["manifest_sha256"],
            "market_manifest": audit["market"]["manifest"],
            "market_manifest_sha256": audit["market"]["manifest_sha256"],
            "public_manifest": audit["public"]["manifest"],
            "public_manifest_sha256": audit["public"]["manifest_sha256"],
            "public_files": audit["public"]["files"],
            "final_holdout_outcomes_read": False,
        }
        _json_dump(staging / "source_manifest.json", source_manifest)
        _json_dump(staging / "derived_panel_manifest.json", panel_manifest)
        candidates.to_csv(staging / "validation_candidate_table.csv", index=False)
        baselines.to_csv(staging / "baseline_comparison.csv", index=False)
        stress.to_csv(staging / "cost_stress.csv", index=False)

        monthly = pd.DataFrame(
            {
                "month": selected.monthly["realization_date"],
                **{
                    candidate_id: result.monthly["net_return"].to_numpy()
                    for candidate_id, result in sorted(results.items())
                },
                "selected_zero_cost": selected.monthly["zero_cost_return"].to_numpy(),
            }
        )
        monthly.to_csv(staging / "selection_monthly_returns.csv", index=False)
        baseline_monthly.to_csv(staging / "baseline_monthly_returns.csv", index=False)

        exposure = selected.monthly[
            [
                "formation_date",
                "realization_date",
                "target_long_names",
                "target_short_names",
                "executed_names",
                "target_gross",
                "executed_gross",
                "executed_net",
                "maximum_executed_name_weight",
                "max_target_industry_gross",
                "max_executed_industry_gross",
                "max_abs_executed_industry_net",
                "fill_ratio",
                "constrained_names",
                "delisted_positions_liquidated",
            ]
        ]
        exposure.to_csv(staging / "exposure_diagnostics.csv", index=False)

        selected_model = {
            "schema_version": "microalpha-crsp-v2-frozen-model/v1",
            "protocol_id": protocol["protocol_id"],
            "protocol_sha256": protocol_sha256(protocol_path),
            "validation_complete": True,
            "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
            "selected_candidate": {
                "candidate_id": selected_id,
                "signal": str(selected_row["signal"]),
                "weighting": str(selected_row["weighting"]),
            },
            "selection_rank": int(selected_row["selection_rank"]),
            "selection_metrics": selected.metrics,
            "selection_reducer": {
                "inputs": "validation_only_2017_2022",
                "ordered_objective": [
                    "maximize_median_calendar_year_net_sharpe_hac",
                    "maximize_worst_calendar_year_net_return",
                    "minimize_one_way_turnover",
                ],
                "hac_lags_monthly": HAC_LAGS_MONTHLY,
            },
            "signal_definitions": SIGNAL_DEFINITIONS,
            "execution_model": {
                "signal_time": "calendar month-end t",
                "trade_time_proxy": "first available session of the following month",
                "return_mapping": "following calendar month's CIZ total return",
                "liquidity_and_spread_information_set": "last observation at formation",
                "selection_proxy_limit": (
                    "Monthly aggregation does not isolate the first-session overnight "
                    "component; the same predeclared mapping is applied to every "
                    "candidate and is not final-holdout execution evidence"
                ),
                "no_session_rule": (
                    "A requested trade with no following-month observed session is "
                    "unfilled; an already-held security with no row is carried at an "
                    "unchanged mark using its last observed point-in-time metadata. A "
                    "present CIZ month containing no price, numeric return, or "
                    "delisting is the same non-trading placeholder state"
                ),
                "missing_return_rule": (
                    "Any present executable-price or delisting observation without a "
                    "CIZ return is a hard stop; a numeric return remains the mark even "
                    "without a price; only absent or all-null no-session placeholder "
                    "months are carried unchanged"
                ),
                "return_semantics_authority": (
                    "https://www.crsp.org/crsp_pdf/"
                    "crsp-us-stock-indexes-databases-guide-flat-file-format-2-0/"
                ),
            },
            "panel_sha256": sha256_file(panel_path),
            "panel_manifest_sha256": sha256_file(panel_manifest_path),
            "panel_builder_git_sha": panel_manifest["git_sha"],
            "selection_runner_git_sha": _git_sha(),
            "final_holdout_outcomes_read": False,
        }
        _json_dump(staging / "selected_model.json", selected_model)
        integrity = {
            "schema_version": "microalpha-crsp-v2-selection-integrity/v1",
            "candidate_count": len(candidates),
            "eligible_candidate_count": int(candidates["eligible"].sum()),
            "validation_months_per_candidate": {
                candidate_id: int(len(result.monthly))
                for candidate_id, result in sorted(results.items())
            },
            "panel_digest_verified": True,
            "protocol_digest_verified": True,
            "chronology_verified": True,
            "unique_keys_verified": True,
            "selected_executed_net_neutrality_verified": (
                selected.metrics["maximum_absolute_executed_net"] <= 1e-9
            ),
            "selected_executed_industry_neutrality_verified": (
                selected.metrics["maximum_absolute_executed_industry_net"] <= 1e-9
            ),
            "selected_executed_industry_gross_cap_verified": (
                selected.metrics["maximum_executed_industry_gross"]
                <= float(protocol["portfolio"]["max_industry_gross_weight"]) + 1e-9
            ),
            "selected_executed_name_cap_verified": (
                selected.metrics["maximum_executed_name_weight"]
                <= float(protocol["portfolio"]["max_single_name_weight"]) + 1e-9
            ),
            "final_holdout_outcomes_read": False,
            "selected_candidate": selected_id,
        }
        _json_dump(staging / "integrity_report.json", integrity)

        artifacts = {}
        for path in sorted(staging.iterdir()):
            if path.name == "selection_manifest.json":
                continue
            artifacts[path.name] = {
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        selection_manifest = {
            "schema_version": "microalpha-crsp-v2-selection-result/v1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "selected_candidate": selected_id,
            "protocol_sha256": protocol_sha256(protocol_path),
            "panel_sha256": sha256_file(panel_path),
            "artifacts": artifacts,
            "final_holdout_outcomes_read": False,
        }
        _json_dump(staging / "selection_manifest.json", selection_manifest)
        os.rename(staging, output_dir)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    return {
        "output_dir": str(output_dir),
        "selected_model": str(output_dir / "selected_model.json"),
        "selected_candidate": selected_id,
        "candidate_count": len(candidates),
        "eligible_candidate_count": int(candidates["eligible"].sum()),
        "panel_sha256": sha256_file(panel_path),
        "final_holdout_outcomes_read": False,
    }


__all__ = ["run_selection"]
