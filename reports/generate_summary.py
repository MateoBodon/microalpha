#!/usr/bin/env python3
"""Run highlighted configs and build a Markdown summary of key metrics."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from microalpha.runner import run_from_config
from microalpha.walkforward import run_walk_forward


@dataclass
class RunSummary:
    config: Path
    run_type: str
    manifest: Dict[str, Any]
    metrics: Dict[str, Any]
    notes: List[str]

    @property
    def label(self) -> str:
        return self.config.stem

    def to_row(self) -> List[str]:
        sharpe = self.metrics.get("sharpe_ratio", 0.0)
        cagr = self.metrics.get("cagr", 0.0)
        max_dd = self.metrics.get("max_drawdown", 0.0)
        turnover = self.metrics.get("total_turnover", 0.0)
        return [
            self.label,
            self.run_type,
            f"{sharpe:.2f}",
            f"{cagr * 100:.1f}%",
            f"{max_dd * 100:.1f}%",
            f"${turnover:,.0f}",
        ]


def _load_metrics(manifest: Dict[str, Any]) -> Dict[str, Any]:
    metrics_info = manifest.get("metrics", {})
    metrics_path = metrics_info.get("metrics_path")
    if not metrics_path:
        return {}
    payload = json.loads(Path(metrics_path).read_text(encoding="utf-8"))
    return payload


def _detect_run_type(cfg: Dict[str, Any]) -> str:
    if "walkforward" in cfg:
        return "walkforward"
    if "template" in cfg and "walkforward" in cfg:  # nested WFVs
        return "walkforward"
    return "single"


def _run_config(config_path: Path, artifact_root: Path) -> Dict[str, Any]:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    run_type = _detect_run_type(cfg)
    artifact_root.mkdir(parents=True, exist_ok=True)
    if run_type == "walkforward":
        manifest = run_walk_forward(
            str(config_path), override_artifacts_dir=str(artifact_root)
        )
    else:
        manifest = run_from_config(
            str(config_path), override_artifacts_dir=str(artifact_root)
        )
    return manifest


def _summarise_folds(manifest: Dict[str, Any]) -> List[str]:
    folds = manifest.get("folds") or []
    if not folds:
        return []
    test_sharpes = [
        fold.get("test_metrics", {}).get("sharpe_ratio")
        for fold in folds
        if fold.get("test_metrics")
    ]
    if not test_sharpes:
        return []
    avg = sum(test_sharpes) / len(test_sharpes)
    best = max(test_sharpes)
    return [
        f"Average test Sharpe across {len(test_sharpes)} folds: {avg:.2f}",
        f"Best fold Sharpe: {best:.2f}",
    ]


def build_table(rows: Iterable[List[str]]) -> str:
    rows = list(rows)
    header = ["Config", "Type", "Sharpe", "CAGR", "Max DD", "Turnover"]
    sep = ["---"] * len(header)
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_summary(summaries: List[RunSummary], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    table = build_table(summary.to_row() for summary in summaries)
    sections = ["# Microalpha Highlight Summary", ""]
    sections.append(table)
    sections.append("")
    for summary in summaries:
        if summary.notes:
            sections.append(f"## {summary.label}")
            sections.extend(f"- {note}" for note in summary.notes)
            sections.append("")
    output_path.write_text("\n".join(sections).strip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Markdown performance summary."
    )
    parser.add_argument(
        "configs",
        nargs="*",
        default=["configs/breakout.yaml", "configs/wfv_cs_mom_small.yaml"],
        help="Config files to run",
    )
    parser.add_argument(
        "--artifact-root",
        default="reports/summaries/_artifacts",
        help="Where to stash run artifacts",
    )
    parser.add_argument(
        "--output",
        default="reports/summaries/quant_summary.md",
        help="Path to the rendered Markdown summary",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact_root = Path(args.artifact_root).resolve()
    summaries: List[RunSummary] = []
    for cfg in args.configs:
        config_path = Path(cfg).resolve()
        manifest = _run_config(config_path, artifact_root)
        metrics = _load_metrics(manifest)
        notes = _summarise_folds(manifest)
        summaries.append(
            RunSummary(
                config=config_path,
                run_type="walkforward" if "folds" in manifest else "single",
                manifest=manifest,
                metrics=metrics,
                notes=notes,
            )
        )
    write_summary(summaries, Path(args.output).resolve())
    print(f"Summary written to {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
