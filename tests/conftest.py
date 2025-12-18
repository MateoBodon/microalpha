from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import pytest

from microalpha.wrds import has_wrds_credentials, has_wrds_data

LOGGER = logging.getLogger("microalpha.pytest")


def _ensure_log_handler(config: pytest.Config) -> None:
    log_dir = Path("artifacts/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"pytest-{timestamp}.log"
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logging.getLogger().addHandler(handler)
    config._microalpha_log_handler = handler  # type: ignore[attr-defined]
    config._microalpha_log_path = log_path  # type: ignore[attr-defined]
    LOGGER.info("Pytest log file initialised at %s", log_path)


def pytest_configure(config: pytest.Config) -> None:
    _ensure_log_handler(config)
    config.addinivalue_line(
        "markers",
        "wrds: mark tests that rely on WRDS credentials or cached exports",
    )


def pytest_unconfigure(config: pytest.Config) -> None:
    handler = getattr(config, "_microalpha_log_handler", None)
    if handler:
        logging.getLogger().removeHandler(handler)
        handler.flush()
        handler.close()


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if has_wrds_credentials() or has_wrds_data():
        return
    skip_marker = pytest.mark.skip(reason="WRDS credentials/data not configured")
    for item in items:
        if "wrds" in item.keywords:
            item.add_marker(skip_marker)


@pytest.fixture(scope="session")
def wrds_ready() -> bool:
    return has_wrds_credentials() or has_wrds_data()


@pytest.fixture(scope="session")
def session_log_path() -> Path | None:
    handler = None
    for existing in logging.getLogger().handlers:
        if isinstance(existing, logging.FileHandler):
            handler = existing
            break
    if handler and isinstance(getattr(handler, "baseFilename", None), str):
        return Path(handler.baseFilename)
    return None
