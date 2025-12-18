from __future__ import annotations

import pytest

from microalpha.wrds import get_wrds_data_root, has_wrds_data


def test_has_wrds_data_with_env(monkeypatch, tmp_path) -> None:
    (tmp_path / "dummy.csv").write_text("x", encoding="utf-8")
    monkeypatch.setenv("WRDS_DATA_ROOT", str(tmp_path))
    assert has_wrds_data()


@pytest.mark.wrds
def test_wrds_data_root_exists() -> None:
    data_root = get_wrds_data_root()
    if data_root is None:
        pytest.skip("WRDS_DATA_ROOT not configured")
    assert data_root.exists()
