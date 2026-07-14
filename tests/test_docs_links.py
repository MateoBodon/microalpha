from __future__ import annotations

from pathlib import Path


def test_public_install_and_artifact_links_are_safe() -> None:
    readme = Path("README.md").read_text()
    docs_home = Path("docs/index.md").read_text()

    assert "git clone https://github.com/MateoBodon/microalpha.git" in readme
    assert "git clone https://github.com/MateoBodon/microalpha.git" in docs_home
    assert "Do not use `pip install microalpha`" in docs_home
    assert "\n   pip install microalpha\n" not in docs_home

    for rel_path in ("artifacts/sample_flagship", "artifacts/sample_wfv"):
        assert rel_path in readme
        assert Path(rel_path).exists()
