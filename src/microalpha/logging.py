"""Lightweight logging utilities for structured artifacts."""

from __future__ import annotations

import json
import os
from typing import Any, Dict


class JsonlWriter:
    """Append-only JSON Lines writer."""

    def __init__(self, path: str):
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self.path = path
        self._handle = open(path, "w", encoding="utf-8")

    def write(self, obj: Dict[str, Any]) -> None:
        self._handle.write(json.dumps(obj) + "\n")
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()
