from __future__ import annotations

import pytest

import tests.conftest as conf


class DummyItem:
    def __init__(self, *, wrds: bool = False) -> None:
        self.keywords = {"wrds": wrds}
        self._markers: list[pytest.Mark] = []

    def add_marker(self, marker: pytest.Mark) -> None:  # pragma: no cover - pytest interface shim
        self._markers.append(marker)


def test_wrds_marker_skips_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(conf, "has_wrds_credentials", lambda: False)
    monkeypatch.setattr(conf, "has_wrds_data", lambda: False)
    item = DummyItem(wrds=True)
    conf.pytest_collection_modifyitems(object(), [item])
    assert any(getattr(marker, "name", "") == "skip" for marker in item._markers)


def test_wrds_marker_allows_when_data_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(conf, "has_wrds_credentials", lambda: False)
    monkeypatch.setattr(conf, "has_wrds_data", lambda: True)
    item = DummyItem(wrds=True)
    conf.pytest_collection_modifyitems(object(), [item])
    assert not item._markers
