"""Utilities for recording reproducibility manifests."""

from __future__ import annotations

import importlib.metadata as importlib_metadata
import json
import os
import platform
import random
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

import numpy as np

try:
    import pandas as pd
except Exception:  # pragma: no cover - pandas is a required runtime dep
    pd = None  # type: ignore[assignment]


@dataclass
class Manifest:
    run_id: str
    git_sha: str
    microalpha_version: str
    python: str
    platform: str
    numpy_version: str
    pandas_version: str
    seed: int
    config_sha256: str


def resolve_git_sha() -> str:
    """Return the current Git SHA or ``"unknown"`` when unavailable."""

    try:
        sha = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:  # pragma: no cover - exercised when Git missing
        sha = "unknown"
    return sha


def _short_sha(git_sha: str) -> str:
    if not git_sha or git_sha == "unknown":
        return "nogit"
    return git_sha[:7]


def generate_run_id(git_sha: str, timestamp: Optional[datetime] = None) -> str:
    """Create a run identifier combining UTC timestamp and short SHA."""

    ts = (timestamp or datetime.utcnow()).strftime("%Y-%m-%dT%H-%M-%SZ")
    return f"{ts}-{_short_sha(git_sha)}"


def _resolve_version(distribution: str, fallback: Optional[str] = None) -> str:
    try:
        return importlib_metadata.version(distribution)
    except importlib_metadata.PackageNotFoundError:
        return fallback or "unknown"


def _resolve_microalpha_version() -> str:
    packages = importlib_metadata.packages_distributions().get("microalpha", [])
    for dist_name in packages:
        version = _resolve_version(dist_name)
        if version != "unknown":
            return version
    return _resolve_version("microalpha")


def _numpy_version() -> str:
    return _resolve_version("numpy", getattr(np, "__version__", None))


def _pandas_version() -> str:
    version = _resolve_version("pandas")
    if version != "unknown":
        return version
    if pd is not None:
        return getattr(pd, "__version__", "unknown")
    return "unknown"


def build(
    seed: Optional[int],
    config_sha256: str,
    git_sha: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Manifest:
    """Construct a manifest and synchronise global RNG state."""

    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    random.seed(seed)
    np.random.seed(seed)

    resolved_git_sha = git_sha or resolve_git_sha()
    resolved_run_id = run_id or generate_run_id(resolved_git_sha)

    return Manifest(
        run_id=resolved_run_id,
        git_sha=resolved_git_sha,
        microalpha_version=_resolve_microalpha_version(),
        python=sys.version,
        platform=platform.platform(),
        numpy_version=_numpy_version(),
        pandas_version=_pandas_version(),
        seed=seed,
        config_sha256=config_sha256,
    )


def write(manifest: Manifest, outdir: str) -> None:
    """Write the manifest to ``outdir/manifest.json``."""

    os.makedirs(outdir, exist_ok=True)
    manifest_path = os.path.join(outdir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(asdict(manifest), handle, indent=2)
