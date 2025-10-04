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
from typing import Optional

import numpy as np


@dataclass
class Manifest:
    run_id: str
    git_sha: str
    python: str
    platform: str
    microalpha_version: str
    seed: int
    config_path: str
    config_sha256: str


def build(
    seed: Optional[int],
    config_path: str,
    run_id: str,
    config_sha256: str,
) -> Manifest:
    """Construct a manifest and synchronise global RNG state."""

    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    random.seed(seed)
    np.random.seed(seed)

    try:
        sha = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        sha = "unknown"

    try:
        version = importlib_metadata.version("microalpha")
    except importlib_metadata.PackageNotFoundError:
        version = "unknown"

    return Manifest(
        run_id,
        sha,
        sys.version,
        platform.platform(),
        version,
        seed,
        os.path.abspath(config_path),
        config_sha256,
    )


def write(manifest: Manifest, outdir: str) -> None:
    """Write the manifest to ``outdir/manifest.json``."""

    os.makedirs(outdir, exist_ok=True)
    manifest_path = os.path.join(outdir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(asdict(manifest), handle, indent=2)

