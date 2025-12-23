"""Helpers for detecting execution modes that can violate timing assumptions."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .config import ExecModelCfg


def evaluate_execution_safety(
    exec_cfg: ExecModelCfg,
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Return (unsafe_execution, reasons, alignment_metadata)."""

    exec_type = (exec_cfg.type or "").lower()
    reasons: List[str] = []

    if exec_type == "lob" and exec_cfg.lob_tplus1 is False:
        reasons.append("same_bar_fills_enabled")

    alignment = {
        "lob_tplus1": exec_cfg.lob_tplus1,
        "exec_type": exec_type,
    }
    return bool(reasons), reasons, alignment
