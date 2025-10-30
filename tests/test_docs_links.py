from __future__ import annotations

from pathlib import Path


def test_readme_references_docs_and_artifacts() -> None:
    readme = Path("README.md").read_text()

    assert "mateobodon.github.io/microalpha" in readme
    assert "[![Docs]" in readme

    for rel_path in ("artifacts/sample_flagship", "artifacts/sample_wfv"):
        assert rel_path in readme
        assert Path(rel_path).exists()
