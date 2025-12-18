from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from microalpha.reporting.wrds_summary import render_wrds_summary

_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def _write_png(path: Path) -> None:
    path.write_bytes(_PNG_BYTES)


def test_wrds_summary_renders_markdown_and_docs(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "wrds"
    artifact_dir.mkdir()
    (artifact_dir / "metrics.json").write_text(
        json.dumps(
            {
                "sharpe_ratio": 1.23,
                "calmar_ratio": 0.98,
                "max_drawdown": -0.12,
                "total_turnover": 12500000,
                "reality_check_p_value": 0.02,
                "turnover_per_day": 100000.0,
                "traded_days": 10,
            }
        ),
        encoding="utf-8",
    )
    _write_png(artifact_dir / "equity_curve.png")
    _write_png(artifact_dir / "bootstrap_hist.png")
    (artifact_dir / "spa.json").write_text(
        json.dumps(
            {
                "p_value": 0.04,
                "best_model": "alpha",
                "candidate_stats": [
                    {"model": "beta", "t_stat": 1.2},
                    {"model": "gamma", "t_stat": 0.5},
                ],
                "num_bootstrap": 2000,
                "avg_block": 63,
            }
        ),
        encoding="utf-8",
    )
    (artifact_dir / "spa.md").write_text(
        """# Hansen SPA Summary

- **Best model:** alpha
- **Observed max t-stat:** 1.234
- **p-value:** 0.040
- **Bootstrap draws:** 2000 (avg block 63)

| Comparator | Mean Diff | t-stat |
| --- | ---:| ---:|
| beta | 0.0100 | 1.20 |
""",
        encoding="utf-8",
    )
    factors_md = artifact_dir / "factors_ff5_mom.md"
    factors_md.write_text(
        """| Factor | Beta | t-stat |
| --- | ---:| ---:|
| Alpha | 0.0100 | 1.20 |
| Mkt_RF | 0.9500 | 5.00 |
""",
        encoding="utf-8",
    )
    manifest = {
        "run_id": "2025-11-12T08-51-11Z-65187e4",
        "config_path": str(tmp_path / "configs" / "wfv.yaml"),
    }
    (artifact_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "wfv.yaml").write_text(
        """
walkforward:
  testing_days: 189
  training_days: 756
template:
  strategy:
    params:
      lookback_months: 12
      skip_months: 1
      min_adv: 30000000
      turnover_target_pct_adv: 0.12
      max_positions_per_sector: 10
""",
        encoding="utf-8",
    )
    folds_payload = [
        {
            "train_start": "2012-01-03",
            "train_end": "2012-12-31",
            "test_start": "2013-01-01",
            "test_end": "2013-04-01",
        }
    ]
    (artifact_dir / "folds.json").write_text(json.dumps(folds_payload), encoding="utf-8")

    plots_dir = tmp_path / "plots"
    plots_dir.mkdir()
    for suffix in ("ic_ir", "deciles", "rolling_betas"):
        _write_png(plots_dir / f"{manifest['run_id']}_{suffix}.png")

    summary_path = tmp_path / "summary.md"
    docs_results = tmp_path / "docs" / "results_wrds.md"
    docs_image_root = tmp_path / "docs" / "img" / "wrds_flagship"
    metrics_out = tmp_path / "reports" / "metrics.json"
    spa_json_out = tmp_path / "reports" / "spa.json"
    spa_md_out = tmp_path / "reports" / "spa.md"

    output = render_wrds_summary(
        artifact_dir,
        summary_path,
        factors_md=factors_md,
        docs_results=docs_results,
        docs_image_root=docs_image_root,
        analytics_plots=plots_dir,
        metrics_json_out=metrics_out,
        spa_json_out=spa_json_out,
        spa_md_out=spa_md_out,
    )
    content = output.read_text(encoding="utf-8")
    assert "Sharpe_HAC" in content
    assert "SPA Comparator" in content
    doc_text = docs_results.read_text(encoding="utf-8")
    assert manifest["run_id"] in doc_text
    assert "Key Visuals" in doc_text
    assert docs_image_root.joinpath(manifest["run_id"], "spa_tstats.png").exists()
    metrics_copy = json.loads(metrics_out.read_text(encoding="utf-8"))
    assert metrics_copy["run_id"] == manifest["run_id"]


def test_wrds_summary_missing_equity(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "missing"
    artifact_dir.mkdir()
    (artifact_dir / "metrics.json").write_text(json.dumps({"sharpe_ratio": 1.0}), encoding="utf-8")
    _write_png(artifact_dir / "bootstrap_hist.png")
    (artifact_dir / "spa.json").write_text(
        json.dumps(
            {
                "p_value": 0.1,
                "best_model": "alpha",
                "candidate_stats": [{"model": "beta", "t_stat": 0.5}],
            }
        ),
        encoding="utf-8",
    )
    (artifact_dir / "spa.md").write_text("# Hansen SPA Summary\n", encoding="utf-8")
    factors_md = artifact_dir / "factors_ff5_mom.md"
    factors_md.write_text(
        """| Factor | Beta | t-stat |
| --- | ---:| ---:|
| Alpha | 0.0100 | 1.20 |
| Mkt_RF | 0.9500 | 5.00 |
""",
        encoding="utf-8",
    )
    (artifact_dir / "manifest.json").write_text(
        json.dumps({"run_id": "run", "config_path": str(tmp_path / "cfg.yaml")}),
        encoding="utf-8",
    )
    (tmp_path / "cfg.yaml").write_text("walkforward: {testing_days: 10}\n", encoding="utf-8")
    (artifact_dir / "folds.json").write_text(
        json.dumps(
            [
                {
                    "train_start": "2020-01-01",
                    "train_end": "2020-06-01",
                    "test_start": "2020-06-02",
                    "test_end": "2020-08-01",
                }
            ]
        ),
        encoding="utf-8",
    )
    plots_dir = tmp_path / "plots"
    plots_dir.mkdir()
    for suffix in ("ic_ir", "deciles", "rolling_betas"):
        _write_png(plots_dir / f"run_{suffix}.png")

    with pytest.raises(FileNotFoundError):
        render_wrds_summary(
            artifact_dir,
            tmp_path / "summary.md",
            factors_md=factors_md,
            analytics_plots=plots_dir,
        )
