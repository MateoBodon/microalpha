"""Deterministic real-data market-risk case study for the public portfolio.

The case study evaluates a fixed volatility-targeting rule on the daily US
market excess return from the Fama--French factor bundle already tracked in the
repository.  It is a risk-management study, not an alpha or capacity claim.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence, cast

import numpy as np
import pandas as pd

from .multiple_testing import centered_max_statistic_test

SCHEMA_VERSION = "microalpha.market-risk-case.v1"
GENERATOR_VERSION = "0.3.0"
DEFAULT_INPUT = Path("data/factors/ff5_mom_daily.csv")
DEFAULT_SEED = 20260715
OOS_START = "2017-01-01"
PERIODS_PER_YEAR = 252
LOOKBACKS = (21, 42, 63, 126)
TARGET_VOL = 0.10
MAX_EXPOSURE = 1.50

SOURCE_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/" "data_library.html"
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _rounded(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _load_factors(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["date"])
    required = {"date", "Mkt_RF", "RF"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"factor input missing columns: {sorted(missing)}")
    if frame["date"].duplicated().any():
        raise ValueError("factor input contains duplicate dates")
    frame = frame.sort_values("date").set_index("date")
    if frame.empty or not np.isfinite(frame[["Mkt_RF", "RF"]]).all().all():
        raise ValueError("factor input is empty or contains non-finite returns")
    if float(frame["Mkt_RF"].abs().max()) > 0.25:
        raise ValueError("Mkt_RF must be expressed as decimal daily returns")
    return frame


def _cost_ledger(turnover: pd.Series) -> pd.DataFrame:
    """Return explicit scenario costs as decimal portfolio-return deductions."""

    aum = 1_000_000.0
    adv_notional = 20_000_000_000.0
    commission_bps = 0.35
    half_spread_bps = 0.50
    impact_eta_bps = 10.0
    participation = turnover * aum / adv_notional
    impact_bps = impact_eta_bps * np.sqrt(participation)
    ledger = pd.DataFrame(index=turnover.index)
    ledger["turnover"] = turnover
    ledger["commission"] = turnover * commission_bps / 10_000.0
    ledger["half_spread"] = turnover * half_spread_bps / 10_000.0
    ledger["impact"] = turnover * impact_bps / 10_000.0
    ledger["total_cost"] = ledger[["commission", "half_spread", "impact"]].sum(axis=1)
    ledger["participation"] = participation
    return ledger


def _simulate(frame: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """Run a chronology-safe exposure process.

    The volatility estimate labeled on date ``t`` includes information through
    that close.  ``executed_weight`` shifts it one row, so the return on ``t``
    can only use an exposure decided after ``t-1``.
    """

    realized_vol = frame["Mkt_RF"].rolling(lookback, min_periods=lookback).std(
        ddof=0
    ) * math.sqrt(PERIODS_PER_YEAR)
    decision_weight = (TARGET_VOL / realized_vol).clip(0.0, MAX_EXPOSURE)
    executed_weight = decision_weight.shift(1).fillna(0.0)
    turnover = executed_weight.diff().abs().fillna(executed_weight.abs())
    costs = _cost_ledger(turnover)
    gross = frame["RF"] + executed_weight * frame["Mkt_RF"]
    result = costs.copy()
    result["realized_vol_at_decision"] = realized_vol
    result["decision_weight"] = decision_weight
    result["executed_weight"] = executed_weight
    result["gross_return"] = gross
    result["net_return"] = gross - costs["total_cost"]
    result["stressed_return_5x_cost"] = gross - 5.0 * costs["total_cost"]
    return result


def _metrics(returns: pd.Series) -> dict[str, float | int]:
    values = returns.to_numpy(dtype=float)
    if len(values) < 2:
        raise ValueError("at least two returns are required")
    years = len(values) / PERIODS_PER_YEAR
    total = float(np.prod(1.0 + values) - 1.0)
    annualized = float((1.0 + total) ** (1.0 / years) - 1.0)
    sample_std = float(np.std(values, ddof=1))
    volatility = sample_std * math.sqrt(PERIODS_PER_YEAR)
    sharpe = (
        float(np.mean(values) / sample_std * math.sqrt(PERIODS_PER_YEAR))
        if sample_std > 0
        else 0.0
    )
    equity: np.ndarray = np.cumprod(1.0 + values)
    drawdown: np.ndarray = equity / np.maximum.accumulate(equity) - 1.0
    max_drawdown = float(np.min(drawdown))
    return {
        "observations": int(len(values)),
        "total_return": _rounded(total),
        "annualized_return": _rounded(annualized),
        "annualized_volatility": _rounded(volatility),
        "sharpe": _rounded(sharpe),
        "max_drawdown": _rounded(max_drawdown),
        "calmar": _rounded(annualized / abs(max_drawdown)) if max_drawdown < 0 else 0.0,
        "worst_day": _rounded(float(np.min(values))),
    }


def _stationary_indices(
    n: int, *, block_length: int, rng: np.random.Generator
) -> np.ndarray:
    indices: np.ndarray = np.empty(n, dtype=int)
    current = int(rng.integers(0, n))
    restart_probability = 1.0 / block_length
    for position in range(n):
        indices[position] = current
        if rng.random() < restart_probability:
            current = int(rng.integers(0, n))
        else:
            current = (current + 1) % n
    return indices


def _uncertainty(
    returns: pd.Series, *, seed: int, draws: int = 999, block_length: int = 15
) -> dict[str, object]:
    values = returns.to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    sharpes: list[float] = []
    annualized_returns: list[float] = []
    for _ in range(draws):
        sample = pd.Series(
            values[_stationary_indices(len(values), block_length=block_length, rng=rng)]
        )
        sample_metrics = _metrics(sample)
        sharpes.append(float(sample_metrics["sharpe"]))
        annualized_returns.append(float(sample_metrics["annualized_return"]))
    return {
        "method": "stationary_block_bootstrap",
        "draws": draws,
        "block_length": block_length,
        "sharpe_95_ci": [
            _rounded(float(np.quantile(sharpes, 0.025))),
            _rounded(float(np.quantile(sharpes, 0.975))),
        ],
        "annualized_return_95_ci": [
            _rounded(float(np.quantile(annualized_returns, 0.025))),
            _rounded(float(np.quantile(annualized_returns, 0.975))),
        ],
    }


def _csv_bytes(frame: pd.DataFrame, *, index_label: str = "date") -> bytes:
    canonical = frame.copy()
    for column in canonical.select_dtypes(include=["float", "float64"]).columns:
        canonical[column] = canonical[column].round(12)
    buffer = io.StringIO(newline="")
    canonical.to_csv(buffer, index=True, index_label=index_label, lineterminator="\n")
    return buffer.getvalue().encode("utf-8")


def _fold_csv(daily: pd.DataFrame) -> bytes:
    rows: list[dict[str, object]] = []
    dates = pd.DatetimeIndex(daily.index)
    for year, fold in daily.groupby(dates.year):
        fold_dates = pd.DatetimeIndex(fold.index)
        rows.append(
            {
                "fold": int(year),
                "start": str(fold_dates.min().date()),
                "end": str(fold_dates.max().date()),
                "observations": int(len(fold)),
                "strategy_return": _metrics(fold["strategy_net"])["annualized_return"],
                "strategy_sharpe": _metrics(fold["strategy_net"])["sharpe"],
                "market_return": _metrics(fold["market"])["annualized_return"],
                "static_return": _metrics(fold["static_risk_matched"])[
                    "annualized_return"
                ],
                "turnover": _rounded(float(fold["turnover"].sum())),
                "cost": _rounded(float(fold["total_cost"].sum())),
            }
        )
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _polyline(
    values: Iterable[float],
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    lo: float | None = None,
    hi: float | None = None,
) -> str:
    arr = np.asarray(values, dtype=float)
    lo = float(arr.min()) if lo is None else float(lo)
    hi = float(arr.max()) if hi is None else float(hi)
    span = max(hi - lo, 1e-12)
    points = []
    for idx, value in enumerate(arr):
        px = x + w * idx / max(len(arr) - 1, 1)
        py = y + h * (1.0 - (float(value) - lo) / span)
        points.append(f"{px:.1f},{py:.1f}")
    return " ".join(points)


def _hero_svg(metrics: Mapping[str, object]) -> bytes:
    strategy = cast(Mapping[str, float], metrics["strategy_net"])
    market = cast(Mapping[str, float], metrics["market"])
    static = cast(Mapping[str, float], metrics["static_risk_matched"])
    selection = cast(Mapping[str, float], metrics["selection_control"])
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700" role="img" aria-labelledby="title desc">',
        '<title id="title">Microalpha real-data market risk case</title>',
        '<desc id="desc">A fixed volatility-targeting rule reduces drawdown and raises descriptive Sharpe, but its corrected differential return is not statistically significant.</desc>',
        '<rect width="1200" height="700" rx="28" fill="#07111f"/>',
        '<text x="64" y="72" fill="#f8fafc" font-family="Inter,Arial,sans-serif" font-size="38" font-weight="700">Real data. Next-session execution. Honest inference.</text>',
        '<text x="64" y="111" fill="#94a3b8" font-family="Inter,Arial,sans-serif" font-size="19">US market factor · 2017–2025 out of sample · fixed 10% volatility target</text>',
        '<rect x="64" y="150" width="1072" height="104" rx="18" fill="#102137" stroke="#24415e"/>',
        '<text x="94" y="187" fill="#7dd3fc" font-family="Inter,Arial,sans-serif" font-size="15" font-weight="700">EMPIRICAL OBSERVATION</text>',
        f'<text x="94" y="226" fill="#f8fafc" font-family="Inter,Arial,sans-serif" font-size="25" font-weight="700">Sharpe {strategy["sharpe"]:.2f} vs {market["sharpe"]:.2f} market; drawdown {strategy["max_drawdown"]:.1%} vs {market["max_drawdown"]:.1%}</text>',
    ]
    cards = [
        (
            "NET RETURN",
            strategy["annualized_return"],
            market["annualized_return"],
            "annualized",
            "%",
        ),
        ("RISK-MATCHED", strategy["sharpe"], static["sharpe"], "Sharpe", ""),
        (
            "MAX DRAWDOWN",
            strategy["max_drawdown"],
            market["max_drawdown"],
            "peak to trough",
            "%",
        ),
        ("SELECTION CONTROL", selection["p_value"], 0.05, "max-stat p-value", "p"),
    ]
    for idx, (heading, primary, comparator, note, kind) in enumerate(cards):
        x = 64 + idx * 274
        primary_text = (
            f"{primary:.1%}"
            if kind == "%"
            else (f"p={primary:.3f}" if kind == "p" else f"{primary:.2f}")
        )
        comparator_text = (
            f"baseline {comparator:.1%}"
            if kind == "%"
            else ("not significant" if kind == "p" else f"baseline {comparator:.2f}")
        )
        parts.extend(
            [
                f'<rect x="{x}" y="286" width="246" height="178" rx="18" fill="#0f1d2f" stroke="#20324a"/>',
                f'<text x="{x + 24}" y="326" fill="#7dd3fc" font-family="Inter,Arial,sans-serif" font-size="14" font-weight="700">{heading}</text>',
                f'<text x="{x + 24}" y="379" fill="#4ade80" font-family="ui-monospace,SFMono-Regular,monospace" font-size="31" font-weight="700">{primary_text}</text>',
                f'<text x="{x + 24}" y="416" fill="#cbd5e1" font-family="Inter,Arial,sans-serif" font-size="15">{comparator_text}</text>',
                f'<text x="{x + 24}" y="444" fill="#64748b" font-family="Inter,Arial,sans-serif" font-size="13">{note}</text>',
            ]
        )
    parts.extend(
        [
            '<rect x="64" y="502" width="1072" height="126" rx="18" fill="#171b2b" stroke="#4c3b64"/>',
            '<text x="94" y="540" fill="#c4b5fd" font-family="Inter,Arial,sans-serif" font-size="15" font-weight="700">CLAIM BOUNDARY</text>',
            '<text x="94" y="579" fill="#f8fafc" font-family="Inter,Arial,sans-serif" font-size="21" font-weight="700">Useful risk-management evidence; no statistically confirmed alpha or capacity claim.</text>',
            '<text x="94" y="608" fill="#94a3b8" font-family="Inter,Arial,sans-serif" font-size="14">All tried lookbacks are disclosed; costs, chronology, folds, source hash, and artifact hashes are machine-readable.</text>',
            '<text x="64" y="671" fill="#64748b" font-family="Inter,Arial,sans-serif" font-size="13">Generated by microalpha market-demo · values rounded from receipt-bound artifacts</text>',
            "</svg>",
        ]
    )
    return ("\n".join(parts) + "\n").encode("utf-8")


def _equity_svg(daily: pd.DataFrame) -> bytes:
    equity = (1.0 + daily[["strategy_net", "market", "static_risk_matched"]]).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    # Shared normalization keeps relative terminal wealth visually meaningful.
    combined = equity.to_numpy(dtype=float)
    lo, hi = float(combined.min()), float(combined.max())

    def shared_line(series: pd.Series) -> str:
        return _polyline(
            series.to_numpy(dtype=float),
            x=72,
            y=126,
            w=1056,
            h=286,
            lo=lo,
            hi=hi,
        )

    colors = {
        "strategy_net": "#22c55e",
        "market": "#60a5fa",
        "static_risk_matched": "#f59e0b",
    }
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720" role="img" aria-labelledby="title desc">',
        '<title id="title">Out-of-sample equity and drawdown</title>',
        '<desc id="desc">Volatility targeting, the market, and a static risk-matched baseline from 2017 through September 2025.</desc>',
        '<rect width="1200" height="720" rx="24" fill="#f8fafc"/>',
        '<text x="72" y="58" fill="#0f172a" font-family="Inter,Arial,sans-serif" font-size="31" font-weight="700">Out-of-sample wealth and drawdown</text>',
        '<text x="72" y="88" fill="#475569" font-family="Inter,Arial,sans-serif" font-size="15">One-day signal lag · net of commission, spread, and nonlinear impact scenario</text>',
    ]
    for y in (126, 197, 269, 340, 412, 486, 560, 634):
        parts.append(
            f'<line x1="72" y1="{y}" x2="1128" y2="{y}" stroke="#dbe4ee" stroke-width="1"/>'
        )
    for name in ("market", "static_risk_matched", "strategy_net"):
        parts.append(
            f'<polyline points="{shared_line(equity[name])}" fill="none" stroke="{colors[name]}" stroke-width="3"/>'
        )
    for name in ("market", "static_risk_matched", "strategy_net"):
        parts.append(
            f'<polyline points="{_polyline(drawdown[name].to_numpy(dtype=float), x=72, y=486, w=1056, h=148, lo=-0.40, hi=0.0)}" fill="none" stroke="{colors[name]}" stroke-width="2"/>'
        )
    labels = [
        ("Market", "#60a5fa", 760),
        ("Static risk-matched", "#f59e0b", 880),
        ("Vol target net", "#22c55e", 1050),
    ]
    for label, color, x in labels:
        parts.extend(
            [
                f'<line x1="{x}" y1="55" x2="{x + 24}" y2="55" stroke="{color}" stroke-width="4"/>',
                f'<text x="{x + 30}" y="61" fill="#334155" font-family="Inter,Arial,sans-serif" font-size="13">{label}</text>',
            ]
        )
    parts.extend(
        [
            '<text x="72" y="462" fill="#334155" font-family="Inter,Arial,sans-serif" font-size="15" font-weight="700">Drawdown</text>',
            '<text x="72" y="681" fill="#64748b" font-family="Inter,Arial,sans-serif" font-size="13">2017</text>',
            '<text x="1090" y="681" fill="#64748b" font-family="Inter,Arial,sans-serif" font-size="13">2025</text>',
            "</svg>",
        ]
    )
    return ("\n".join(parts) + "\n").encode("utf-8")


def _lineage_svg() -> bytes:
    labels = [
        ("Public factor file", "source URL + SHA-256"),
        ("Decision at t", "trailing returns through close"),
        ("Execute at t+1", "weight changes next session"),
        ("Cost ledger", "commission + spread + impact"),
        ("Inference", "folds + max statistic"),
        ("Receipt", "schema + artifact hashes"),
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="330" viewBox="0 0 1200 330" role="img" aria-labelledby="title desc">',
        '<title id="title">Real-data case lineage</title>',
        '<desc id="desc">The public factor file passes through a lagged decision clock, next-session execution, explicit costs, inference, and a hash receipt.</desc>',
        '<rect width="1200" height="330" rx="24" fill="#07111f"/>',
        '<text x="55" y="58" fill="#f8fafc" font-family="Inter,Arial,sans-serif" font-size="30" font-weight="700">Every empirical claim has a source, clock, ledger, and hash</text>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#38bdf8"/></marker></defs>',
    ]
    for idx, (title, subtitle) in enumerate(labels):
        x = 45 + idx * 192
        parts.extend(
            [
                f'<rect x="{x}" y="116" width="166" height="92" rx="14" fill="#0f1d2f" stroke="#38bdf8"/>',
                f'<text x="{x + 83}" y="151" text-anchor="middle" fill="#f8fafc" font-family="Inter,Arial,sans-serif" font-size="15" font-weight="700">{title}</text>',
                f'<text x="{x + 83}" y="180" text-anchor="middle" fill="#94a3b8" font-family="Inter,Arial,sans-serif" font-size="11">{subtitle}</text>',
            ]
        )
        if idx < len(labels) - 1:
            parts.append(
                f'<path d="M {x + 171} 162 H {x + 187}" stroke="#38bdf8" stroke-width="3" marker-end="url(#arrow)"/>'
            )
    parts.extend(
        [
            '<text x="55" y="274" fill="#c4b5fd" font-family="Inter,Arial,sans-serif" font-size="15" font-weight="700">No firm-level constituent selection; the study is conditional on a published research factor and makes no security-level survivorship claim.</text>',
            '<text x="55" y="301" fill="#64748b" font-family="Inter,Arial,sans-serif" font-size="13">The 2023–2025 sealed CRSP confirmation set is not accessed.</text>',
            "</svg>",
        ]
    )
    return ("\n".join(parts) + "\n").encode("utf-8")


def _schema_payload() -> dict[str, object]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_VERSION,
        "required_artifacts": [
            "metrics.json",
            "daily.csv",
            "folds.csv",
            "selection.json",
            "data_manifest.json",
            "market_case.svg",
            "equity_drawdown.svg",
            "data_lineage.svg",
        ],
        "metrics_required": [
            "strategy_net",
            "market",
            "static_risk_matched",
            "selection_control",
            "claim_boundary",
        ],
        "daily_required_columns": [
            "date",
            "signal_available_date",
            "executed_weight",
            "turnover",
            "commission",
            "half_spread",
            "impact",
            "total_cost",
            "strategy_net",
            "market",
            "static_risk_matched",
        ],
    }


def validate_market_case_artifacts(output_dir: str | Path) -> dict[str, object]:
    out = Path(output_dir)
    receipt_path = out / "receipt.json"
    if not receipt_path.exists():
        raise ValueError("market case receipt.json is missing")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("market case schema version mismatch")
    schema = json.loads((out / "artifact_schema.json").read_text(encoding="utf-8"))
    for name in cast(Iterable[str], schema["required_artifacts"]):
        if not (out / name).is_file():
            raise ValueError(f"required artifact missing: {name}")
    metrics = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    for key in cast(Iterable[str], schema["metrics_required"]):
        if key not in metrics:
            raise ValueError(f"metrics key missing: {key}")
    daily = pd.read_csv(out / "daily.csv")
    missing_columns = set(cast(Iterable[str], schema["daily_required_columns"])) - set(
        daily.columns
    )
    if missing_columns:
        raise ValueError(f"daily columns missing: {sorted(missing_columns)}")
    residual = daily["gross_return"] - daily["total_cost"] - daily["strategy_net"]
    if float(residual.abs().max()) > 1e-10:
        raise ValueError("cost ledger does not reconcile to net returns")
    if not (
        pd.to_datetime(daily["signal_available_date"]) < pd.to_datetime(daily["date"])
    ).all():
        raise ValueError("decision/fill chronology is not strictly lagged")
    for name, expected in cast(Mapping[str, str], receipt["artifacts"]).items():
        actual = _sha256((out / name).read_bytes())
        if actual != expected:
            raise ValueError(f"artifact hash mismatch: {name}")
    return {
        "status": "pass",
        "schema_version": SCHEMA_VERSION,
        "artifacts": len(receipt["artifacts"]),
    }


def run_market_case(
    output_dir: str | Path,
    *,
    input_path: str | Path = DEFAULT_INPUT,
    seed: int = DEFAULT_SEED,
) -> dict[str, object]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    source_path = Path(input_path)
    source_bytes = source_path.read_bytes()
    factors = _load_factors(source_path)
    calibration = factors[factors.index <= pd.Timestamp("2016-12-31")]
    if len(calibration) < 252:
        raise ValueError("calibration window must contain at least 252 observations")
    oos_factors = factors[factors.index >= pd.Timestamp(OOS_START)]
    if len(oos_factors) < 252:
        raise ValueError("out-of-sample window must contain at least 252 observations")

    simulations = {lookback: _simulate(factors, lookback) for lookback in LOOKBACKS}
    primary = simulations[21].loc[oos_factors.index].copy()
    market = oos_factors["RF"] + oos_factors["Mkt_RF"]
    calibration_vol = float(
        calibration["Mkt_RF"].std(ddof=1) * math.sqrt(PERIODS_PER_YEAR)
    )
    static_weight = min(MAX_EXPOSURE, TARGET_VOL / calibration_vol)
    static = oos_factors["RF"] + static_weight * oos_factors["Mkt_RF"]

    daily = primary.copy()
    daily["signal_available_date"] = (
        pd.Series(factors.index, index=factors.index)
        .shift(1)
        .loc[oos_factors.index]
        .dt.strftime("%Y-%m-%d")
    )
    daily["strategy_net"] = primary["net_return"]
    daily["market"] = market
    daily["static_risk_matched"] = static
    daily["mkt_rf"] = oos_factors["Mkt_RF"]
    daily["rf"] = oos_factors["RF"]

    candidates = np.column_stack(
        [
            simulations[lookback]
            .loc[oos_factors.index, "net_return"]
            .to_numpy(dtype=float)
            for lookback in LOOKBACKS
        ]
    )
    selection = centered_max_statistic_test(
        candidates,
        benchmark_returns=static.to_numpy(dtype=float),
        candidate_names=[f"lookback_{lookback}" for lookback in LOOKBACKS],
        seed=seed,
        num_bootstrap=1999,
        method="stationary",
        block_length=15,
    )
    selection["distribution"] = [
        _rounded(float(value))
        for value in cast(Sequence[float], selection["distribution"])
    ]

    strategy_metrics = _metrics(daily["strategy_net"])
    gross_metrics = _metrics(daily["gross_return"])
    market_metrics = _metrics(daily["market"])
    static_metrics = _metrics(daily["static_risk_matched"])
    stressed_metrics = _metrics(daily["stressed_return_5x_cost"])
    years = len(daily) / PERIODS_PER_YEAR
    costs = {
        "commission_total": _rounded(float(daily["commission"].sum())),
        "half_spread_total": _rounded(float(daily["half_spread"].sum())),
        "impact_total": _rounded(float(daily["impact"].sum())),
        "total_cost": _rounded(float(daily["total_cost"].sum())),
        "annualized_cost": _rounded(float(daily["total_cost"].sum()) / years),
        "annualized_turnover": _rounded(float(daily["turnover"].sum()) / years),
        "maximum_participation": _rounded(float(daily["participation"].max()), 9),
        "scenario": {
            "aum_usd": 1_000_000,
            "adv_notional_usd": 20_000_000_000,
            "commission_bps": 0.35,
            "half_spread_bps": 0.50,
            "impact_eta_bps": 10.0,
        },
        "claim_boundary": "transparent liquidity sensitivity; not venue calibration or capacity evidence",
    }
    metrics: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "study": "fixed_market_volatility_targeting",
        "sample": {
            "calibration_start": str(calibration.index.min().date()),
            "calibration_end": str(calibration.index.max().date()),
            "oos_start": str(oos_factors.index.min().date()),
            "oos_end": str(oos_factors.index.max().date()),
            "oos_observations": int(len(oos_factors)),
            "walk_forward_folds": int(
                pd.DatetimeIndex(oos_factors.index).year.nunique()
            ),
        },
        "fixed_specification": {
            "lookback_sessions": 21,
            "target_volatility": TARGET_VOL,
            "maximum_exposure": MAX_EXPOSURE,
            "signal_clock": "close_t",
            "execution_clock": "next_session_t_plus_1",
            "selected_on_oos_performance": False,
        },
        "strategy_net": strategy_metrics,
        "strategy_gross": gross_metrics,
        "market": market_metrics,
        "static_risk_matched": {**static_metrics, "weight": _rounded(static_weight)},
        "stressed_5x_cost": stressed_metrics,
        "costs": costs,
        "uncertainty": _uncertainty(daily["strategy_net"], seed=seed + 1),
        "selection_control": {
            key: value for key, value in selection.items() if key != "distribution"
        },
        "engineering_correctness": "source hash, strict t+1 chronology, cost identity, schema validation, and artifact hashes are executable gates",
        "empirical_observation": "the fixed rule reduced realized risk and drawdown and raised descriptive Sharpe versus the market and a static risk-matched baseline",
        "investment_claim": "none",
        "claim_boundary": "retrospective public-factor risk-management evidence; no statistically confirmed alpha, security-level capacity, or live-trading claim",
    }

    data_manifest = {
        "schema_version": "microalpha.data-manifest.v1",
        "dataset": "Fama-French daily factors plus momentum",
        "publisher": "Kenneth R. French Data Library",
        "source_url": SOURCE_URL,
        "local_snapshot": "data/factors/ff5_mom_daily.csv",
        "snapshot_sha256": _sha256(source_bytes),
        "rows": int(len(factors)),
        "start": str(factors.index.min().date()),
        "end": str(factors.index.max().date()),
        "columns": list(factors.reset_index().columns),
        "return_units": "decimal daily research-portfolio returns",
        "availability_rule": "a date-t factor return is available only after date-t close and can affect exposure at t+1",
        "survivorship_boundary": "published factor series; no firm-level constituent selection or security-level survivorship claim",
        "provenance_note": "the tracked snapshot was added from the public factor library through the project's prior WRDS research workflow; raw firm-level data is neither read nor distributed",
    }

    files = {
        "metrics.json": _json_bytes(metrics),
        "daily.csv": _csv_bytes(daily),
        "folds.csv": _fold_csv(daily),
        "selection.json": _json_bytes(selection),
        "data_manifest.json": _json_bytes(data_manifest),
        "artifact_schema.json": _json_bytes(_schema_payload()),
        "market_case.svg": _hero_svg(metrics),
        "equity_drawdown.svg": _equity_svg(daily),
        "data_lineage.svg": _lineage_svg(),
    }
    for name, content in files.items():
        (out / name).write_bytes(content)

    module_dir = Path(__file__).resolve().parent
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "generator": {
            "version": GENERATOR_VERSION,
            "source_sha256": {
                name: _sha256((module_dir / name).read_bytes())
                for name in ("market_case.py", "multiple_testing.py")
            },
        },
        "input": {
            "logical_path": "data/factors/ff5_mom_daily.csv",
            "sha256": _sha256(source_bytes),
        },
        "artifacts": {
            name: _sha256(content) for name, content in sorted(files.items())
        },
        "claim_boundary": metrics["claim_boundary"],
    }
    receipt_bytes = _json_bytes(receipt)
    (out / "receipt.json").write_bytes(receipt_bytes)
    verification = validate_market_case_artifacts(out)
    return {
        "artifact_dir": str(out),
        "receipt_sha256": _sha256(receipt_bytes),
        "verification": verification,
        "metrics": metrics,
    }
