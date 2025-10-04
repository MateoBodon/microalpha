"""Utilities for recording reproducibility manifests."""

from __future__ import annotations

import importlib.metadata as importlib_metadata
import json
import os
import platform
import random
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple

import numpy as np
import pandas as pd


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


def resolve_git_sha() -> Tuple[str, str]:
    """Return ``(full_sha, short_sha)`` for the current Git HEAD."""

    try:
        sha = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown", "unknown"

    short = sha[:7] if sha else "unknown"
    return sha, short


def generate_run_id(short_sha: str, timestamp: Optional[datetime] = None) -> str:
    """Create a run identifier using a UTC timestamp and short SHA."""

    current = timestamp or datetime.now(timezone.utc)
    ts = current.strftime("%Y-%m-%dT%H-%M-%SZ")
    suffix = short_sha if short_sha and short_sha != "unknown" else "nogit"
    return f"{ts}-{suffix}"


def _resolve_distribution_version() -> str:
    """Resolve the installed distribution version for microalpha."""

    try:
        return importlib_metadata.version("microalpha")
    except importlib_metadata.PackageNotFoundError:
        packages = importlib_metadata.packages_distributions()
        distributions = packages.get("microalpha") or []
        for dist in distributions:
            try:
                return importlib_metadata.version(dist)
            except importlib_metadata.PackageNotFoundError:
                continue
    return "unknown"


def build(
    seed: Optional[int],
    run_id: str,
    config_sha256: str,
    git_sha: Optional[str] = None,
) -> Manifest:
    """Construct a manifest and synchronise global RNG state."""

    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    random.seed(seed)
    np.random.seed(seed)

    full_sha = git_sha
    if not full_sha:
        full_sha, _ = resolve_git_sha()

    version = _resolve_distribution_version()

    return Manifest(
        run_id=run_id,
        git_sha=full_sha,
        microalpha_version=version,
        python=platform.python_version(),
        platform=platform.platform(),
        numpy_version=np.__version__,
        pandas_version=pd.__version__,
        seed=seed,
        config_sha256=config_sha256,
    )


def write(manifest: Manifest, outdir: str) -> None:
    """Write the manifest to ``outdir/manifest.json``."""

    os.makedirs(outdir, exist_ok=True)
    manifest_path = os.path.join(outdir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(asdict(manifest), handle, indent=2)
