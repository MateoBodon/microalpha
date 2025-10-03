"""Utilities for recording reproducibility manifests."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

import json
import os
import platform
import random
import subprocess
import sys

import numpy as np


@dataclass
class Manifest:
    git_sha: str
    python: str
    platform: str
    seed: int
    config_path: str


def build(seed: Optional[int], config_path: str) -> Manifest:
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

    return Manifest(sha, sys.version, platform.platform(), seed, os.path.abspath(config_path))


def write(manifest: Manifest, outdir: str) -> None:
    """Write the manifest to ``outdir/manifest.json``."""

    os.makedirs(outdir, exist_ok=True)
    manifest_path = os.path.join(outdir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(asdict(manifest), handle, indent=2)

