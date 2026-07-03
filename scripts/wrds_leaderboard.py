#!/usr/bin/env python3
"""Build a provenance-aware WRDS real-data leaderboard from existing artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

TRACKED_PATTERN = "artifacts/wrds_flagship/*/metrics.json"
LOCAL_PATTERN = "artifacts/_local/**/wrds_flagship/*/metrics.json"

MIN_TRADES = 20
MAX_MAXDD_PCT = 15.0

CSV_FIELDS = [
    "rank",
    "best_eligible",
    "ineligible_reasons",
    "run_id",
    "dataset_id",
    "dataset_id_source",
    "provenance_complete",
    "window_label",
    "selection_window_start",
    "selection_window_end",
    "holdout_start",
    "holdout_end",
    "overall_sharpe_hac",
    "overall_cagr",
    "overall_maxdd_pct",
    "overall_mar",
    "overall_turnover",
    "overall_trades",
    "holdout_sharpe_hac",
    "holdout_cagr",
    "holdout_maxdd_pct",
    "holdout_mar",
    "holdout_turnover",
    "holdout_trades",
    "spa_p_value",
    "reality_check_p_value",
    "config_path",
    "git_sha",
    "artifact_dir",
    "metrics_path",
    "holdout_metrics_path",
    "manifest_path",
    "holdout_manifest_path",
    "spa_path",
    "reality_check_path",
]


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        return payload
    return None


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _as_int(value: Any) -> int | None:
    number = _as_float(value)
    if number is None:
        return None
    return int(round(number))


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _first_float(*values: Any) -> float | None:
    for value in values:
        parsed = _as_float(value)
        if parsed is not None:
            return parsed
    return None


def _to_repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _normalize_config_path(raw_config_path: str) -> str:
    if not raw_config_path:
        return ""
    path = Path(raw_config_path)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def _extract_metric_block(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {
            "sharpe_hac": None,
            "cagr": None,
            "maxdd_pct": None,
            "mar": None,
            "turnover": None,
            "trades": None,
        }

    sharpe = _first_float(payload.get("sharpe_ratio"), payload.get("sharpe_hac"))
    cagr = _first_float(payload.get("cagr"))

    maxdd_pct = _first_float(payload.get("max_drawdown_pct"))
    if maxdd_pct is None:
        maxdd = _first_float(payload.get("max_drawdown"))
        if maxdd is not None:
            maxdd_pct = maxdd * 100.0

    mar = _first_float(payload.get("calmar_ratio"), payload.get("mar"))
    turnover = _first_float(payload.get("total_turnover"), payload.get("turnover"))
    trades = _as_int(payload.get("num_trades") if "num_trades" in payload else payload.get("trades"))

    return {
        "sharpe_hac": sharpe,
        "cagr": cagr,
        "maxdd_pct": maxdd_pct,
        "mar": mar,
        "turnover": turnover,
        "trades": trades,
    }


def _window_label(has_holdout: bool) -> str:
    if has_holdout:
        return "holdout-only"
    return "overall-wfv-oos"


def _window_span(start: str, end: str) -> str:
    if start and end:
        return f"{start} to {end}"
    if start:
        return f"{start} to ?"
    if end:
        return f"? to {end}"
    return "n/a"


def _eligibility_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if not row["dataset_id"]:
        reasons.append("missing_dataset_id")
    if row["holdout_sharpe_hac"] is None:
        reasons.append("missing_holdout_sharpe")
    holdout_trades = row["holdout_trades"]
    if holdout_trades is None:
        reasons.append("missing_holdout_trades")
    elif holdout_trades < MIN_TRADES:
        reasons.append(f"holdout_trades_lt_{MIN_TRADES}")

    holdout_maxdd = row["holdout_maxdd_pct"]
    if holdout_maxdd is None:
        reasons.append("missing_holdout_maxdd")
    elif holdout_maxdd > MAX_MAXDD_PCT:
        reasons.append(f"holdout_maxdd_gt_{MAX_MAXDD_PCT:.1f}")
    return reasons


def _extract_row(metrics_path: Path) -> dict[str, Any]:
    run_dir = metrics_path.parent

    metrics_payload = _read_json(metrics_path)
    holdout_metrics_path = run_dir / "holdout_metrics.json"
    holdout_payload = _read_json(holdout_metrics_path)

    manifest_path = run_dir / "manifest.json"
    manifest = _read_json(manifest_path) or {}

    holdout_manifest_path = run_dir / "holdout_manifest.json"
    holdout_manifest = _read_json(holdout_manifest_path) or {}

    spa_path = run_dir / "spa.json"
    spa = _read_json(spa_path)

    reality_path = run_dir / "reality_check.json"
    reality = _read_json(reality_path)

    walkforward = manifest.get("walkforward") if isinstance(manifest.get("walkforward"), dict) else {}
    wrds_meta = manifest.get("wrds") if isinstance(manifest.get("wrds"), dict) else {}

    run_id = _as_str(manifest.get("run_id") or holdout_manifest.get("run_id") or run_dir.name)
    dataset_id = _as_str(wrds_meta.get("dataset_id") or manifest.get("dataset_id"))
    dataset_id_source = _as_str(wrds_meta.get("dataset_id_source") or manifest.get("dataset_id_source"))

    selection_window_start = _as_str(holdout_manifest.get("selection_window_start") or walkforward.get("selection_window_start"))
    selection_window_end = _as_str(holdout_manifest.get("selection_window_end") or walkforward.get("selection_window_end"))
    holdout_start = _as_str(holdout_manifest.get("holdout_start") or walkforward.get("holdout_start"))
    holdout_end = _as_str(holdout_manifest.get("holdout_end") or walkforward.get("holdout_end"))

    overall = _extract_metric_block(metrics_payload)
    holdout = _extract_metric_block(holdout_payload)

    spa_p = _first_float(
        spa.get("p_value") if spa else None,
        spa.get("pvalue") if spa else None,
        spa.get("p_val") if spa else None,
        metrics_payload.get("spa_p_value") if metrics_payload else None,
        holdout_payload.get("spa_p_value") if holdout_payload else None,
    )
    reality_p = _first_float(
        reality.get("p_value") if reality else None,
        reality.get("pvalue") if reality else None,
        reality.get("p_val") if reality else None,
        metrics_payload.get("reality_check_p_value") if metrics_payload else None,
        holdout_payload.get("reality_check_p_value") if holdout_payload else None,
    )

    row: dict[str, Any] = {
        "rank": None,
        "best_eligible": "no",
        "ineligible_reasons": "",
        "run_id": run_id,
        "dataset_id": dataset_id,
        "dataset_id_source": dataset_id_source,
        "provenance_complete": "yes" if run_id and dataset_id else "no",
        "window_label": _window_label(holdout_payload is not None),
        "selection_window_start": selection_window_start,
        "selection_window_end": selection_window_end,
        "holdout_start": holdout_start,
        "holdout_end": holdout_end,
        "overall_sharpe_hac": overall["sharpe_hac"],
        "overall_cagr": overall["cagr"],
        "overall_maxdd_pct": overall["maxdd_pct"],
        "overall_mar": overall["mar"],
        "overall_turnover": overall["turnover"],
        "overall_trades": overall["trades"],
        "holdout_sharpe_hac": holdout["sharpe_hac"],
        "holdout_cagr": holdout["cagr"],
        "holdout_maxdd_pct": holdout["maxdd_pct"],
        "holdout_mar": holdout["mar"],
        "holdout_turnover": holdout["turnover"],
        "holdout_trades": holdout["trades"],
        "spa_p_value": spa_p,
        "reality_check_p_value": reality_p,
        "config_path": _normalize_config_path(_as_str(manifest.get("config_path"))),
        "git_sha": _as_str(manifest.get("git_sha")),
        "artifact_dir": _to_repo_relative(run_dir),
        "metrics_path": _to_repo_relative(metrics_path),
        "holdout_metrics_path": _to_repo_relative(holdout_metrics_path) if holdout_metrics_path.exists() else "",
        "manifest_path": _to_repo_relative(manifest_path) if manifest_path.exists() else "",
        "holdout_manifest_path": _to_repo_relative(holdout_manifest_path) if holdout_manifest_path.exists() else "",
        "spa_path": _to_repo_relative(spa_path) if spa_path.exists() else "",
        "reality_check_path": _to_repo_relative(reality_path) if reality_path.exists() else "",
    }

    reasons = _eligibility_reasons(row)
    if not reasons:
        row["best_eligible"] = "yes"
    row["ineligible_reasons"] = "|".join(reasons)
    return row


def _row_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    eligible_rank = 0 if row["best_eligible"] == "yes" else 1
    sharpe = row["holdout_sharpe_hac"] if row["holdout_sharpe_hac"] is not None else float("-inf")
    maxdd = row["holdout_maxdd_pct"] if row["holdout_maxdd_pct"] is not None else float("inf")
    mar = row["holdout_mar"] if row["holdout_mar"] is not None else float("-inf")
    return (
        eligible_rank,
        -sharpe,
        maxdd,
        -mar,
        row["artifact_dir"],
    )


def _serialize_csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.15g}"
    return str(value)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _serialize_csv_value(row.get(field)) for field in CSV_FIELDS})


def _fmt_float(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _fmt_pct(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}%"


def _fmt_currency_millions(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"${value / 1_000_000.0:.2f}MM"


def _write_markdown(path: Path, rows: list[dict[str, Any]], best_row: dict[str, Any] | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# WRDS Real-Data Leaderboard")
    lines.append("")
    lines.append("Pre-registered best rule:")
    lines.append("- Primary: maximize holdout `sharpe_hac`.")
    lines.append(
        f"- Guardrails: `dataset_id` must be present, holdout trades >= {MIN_TRADES}, holdout max drawdown <= {MAX_MAXDD_PCT:.1f}%"
    )
    lines.append("- Tie-breakers: lower holdout max drawdown, then higher holdout MAR, then stable path order.")
    lines.append("")
    lines.append(f"Candidates scanned: {len(rows)}")
    if best_row is None:
        lines.append("Best eligible row: none")
    else:
        lines.append(f"Best eligible row: rank {best_row['rank']} (run_id={best_row['run_id']})")
    lines.append("")
    lines.append(
        "| rank | run_id | dataset_id | selection_window | holdout_window | holdout_sharpe_hac | holdout_cagr | holdout_maxdd | holdout_mar | holdout_turnover | holdout_trades | SPA p | RC p | eligible | reasons | config_path | artifact_dir |"
    )
    lines.append("|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|")

    for row in rows:
        selection_window = _window_span(row["selection_window_start"], row["selection_window_end"])
        holdout_window = _window_span(row["holdout_start"], row["holdout_end"])
        reasons = row["ineligible_reasons"] or "-"
        lines.append(
            "| {rank} | {run_id} | {dataset_id} | {selection_window} | {holdout_window} | {sharpe} | {cagr} | {maxdd} | {mar} | {turnover} | {trades} | {spa} | {rc} | {eligible} | {reasons} | {config_path} | {artifact_dir} |".format(
                rank=row["rank"],
                run_id=row["run_id"],
                dataset_id=row["dataset_id"] or "missing",
                selection_window=selection_window,
                holdout_window=holdout_window,
                sharpe=_fmt_float(row["holdout_sharpe_hac"], 3),
                cagr=_fmt_pct((row["holdout_cagr"] * 100.0) if row["holdout_cagr"] is not None else None, 2),
                maxdd=_fmt_pct(row["holdout_maxdd_pct"], 2),
                mar=_fmt_float(row["holdout_mar"], 3),
                turnover=_fmt_currency_millions(row["holdout_turnover"]),
                trades=row["holdout_trades"] if row["holdout_trades"] is not None else "n/a",
                spa=_fmt_float(row["spa_p_value"], 3),
                rc=_fmt_float(row["reality_check_p_value"], 3),
                eligible=row["best_eligible"],
                reasons=reasons,
                config_path=row["config_path"] or "n/a",
                artifact_dir=row["artifact_dir"],
            )
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_resume_line(path: Path, best_row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    holdout_window = _window_span(best_row["holdout_start"], best_row["holdout_end"])
    sharpe = _fmt_float(best_row["holdout_sharpe_hac"], 3)
    cagr_pct = _fmt_pct((best_row["holdout_cagr"] * 100.0) if best_row["holdout_cagr"] is not None else None, 2)
    maxdd = _fmt_pct(best_row["holdout_maxdd_pct"], 2)
    mar = _fmt_float(best_row["holdout_mar"], 2)
    turnover = _fmt_currency_millions(best_row["holdout_turnover"])
    trades = best_row["holdout_trades"] if best_row["holdout_trades"] is not None else "n/a"
    spa_p = _fmt_float(best_row["spa_p_value"], 3)
    rc_p = _fmt_float(best_row["reality_check_p_value"], 3)

    headline = (
        "WRDS/CRSP flagship momentum (window=holdout-only, {window}): "
        "Sharpe_HAC {sharpe}, CAGR {cagr}, MaxDD {maxdd}, MAR {mar}, "
        "turnover {turnover} ({trades} trades), RealityCheck p={rc_p}, SPA p={spa_p}. "
        "run_id={run_id}; dataset_id={dataset_id}."
    ).format(
        window=holdout_window,
        sharpe=sharpe,
        cagr=cagr_pct,
        maxdd=maxdd,
        mar=mar,
        turnover=turnover,
        trades=trades,
        rc_p=rc_p,
        spa_p=spa_p,
        run_id=best_row["run_id"],
        dataset_id=best_row["dataset_id"],
    )

    lines = [
        headline,
        "",
        "Window label: holdout-only",
        f"Holdout window: {holdout_window}",
        "Selection rule: primary=max holdout Sharpe_HAC; guardrails=dataset_id present, trades>=20, maxdd<=15%; tie-breakers=lower MaxDD then higher MAR.",
        "",
        "Source files:",
        f"- manifest: `{best_row['manifest_path'] or 'missing'}`",
        f"- holdout_manifest: `{best_row['holdout_manifest_path'] or 'missing'}`",
        f"- holdout_metrics: `{best_row['holdout_metrics_path'] or 'missing'}`",
        f"- spa: `{best_row['spa_path'] or 'missing'}`",
        f"- reality_check: `{best_row['reality_check_path'] or 'missing'}`",
        f"- leaderboard_row: `{best_row['artifact_dir']}`",
    ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _discover_metric_files() -> list[Path]:
    paths: set[Path] = set()
    for pattern in (TRACKED_PATTERN, LOCAL_PATTERN):
        for path in REPO_ROOT.glob(pattern):
            if path.is_file():
                paths.add(path.resolve())
    return sorted(paths)


def _default_csv_path() -> Path:
    return REPO_ROOT / "docs/artifacts/resume/wrds/leaderboard/leaderboard.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan WRDS flagship artifact metrics and build a provenance-aware leaderboard "
            "plus a best resume line using holdout-first selection rules."
        )
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_default_csv_path(),
        help="Leaderboard CSV output path (default: docs/artifacts/resume/wrds/leaderboard/leaderboard.csv).",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=None,
        help="Leaderboard markdown output path (default: <out-dir>/leaderboard.md).",
    )
    parser.add_argument(
        "--resume-out",
        type=Path,
        default=None,
        help="Best resume line output path (default: <out-dir>/resume_line_best.md).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    out_csv = args.out.resolve()
    out_md = args.md_out.resolve() if args.md_out else out_csv.parent / "leaderboard.md"
    out_resume = args.resume_out.resolve() if args.resume_out else out_csv.parent / "resume_line_best.md"

    metric_files = _discover_metric_files()
    if not metric_files:
        raise SystemExit("No candidate metrics files found in wrds_flagship artifact roots.")

    rows = [_extract_row(path) for path in metric_files]
    rows.sort(key=_row_sort_key)

    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx

    best_row = next((row for row in rows if row["best_eligible"] == "yes"), None)

    _write_csv(out_csv, rows)
    _write_markdown(out_md, rows, best_row)

    if best_row is None:
        out_resume.parent.mkdir(parents=True, exist_ok=True)
        out_resume.write_text(
            "No eligible WRDS real-data row found under the pre-registered selection rule.\n",
            encoding="utf-8",
        )
        print(f"wrote {out_csv}")
        print(f"wrote {out_md}")
        print(f"wrote {out_resume}")
        print("best_eligible: none")
        return 2

    _write_resume_line(out_resume, best_row)
    print(f"wrote {out_csv}")
    print(f"wrote {out_md}")
    print(f"wrote {out_resume}")
    print(
        "best_eligible: run_id={run_id} dataset_id={dataset_id} holdout_sharpe_hac={sharpe:.6f}".format(
            run_id=best_row["run_id"],
            dataset_id=best_row["dataset_id"],
            sharpe=best_row["holdout_sharpe_hac"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
