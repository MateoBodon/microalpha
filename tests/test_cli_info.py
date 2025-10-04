import importlib.metadata as md
import json
import platform
import sys

import microalpha.cli as cli


def test_cli_info_outputs_json(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["microalpha", "info"])
    monkeypatch.setattr(cli, "_resolve_version", lambda: "test-version")

    cli.main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload["python"] == platform.python_version()
    assert payload["platform"] == platform.platform()
    assert payload["microalpha"] == "test-version"
    assert payload["executable"] == sys.executable


def test_cli_run_invokes_runner(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["microalpha", "run", "-c", "config.yml"])

    calls = {}

    def fake_run(cfg):
        calls["run"] = cfg
        return {"config": cfg}

    monkeypatch.setattr(cli, "run_from_config", fake_run)
    monkeypatch.setattr(cli, "run_walk_forward", lambda cfg: {"walk": cfg})
    monkeypatch.setattr(cli, "_resolve_version", lambda: "v-test")

    times = iter([10.0, 11.5])
    monkeypatch.setattr(cli.time, "time", lambda: next(times))

    cli.main()
    payload = json.loads(capsys.readouterr().out)

    assert calls["run"] == "config.yml"
    assert payload["config"] == "config.yml"
    assert payload["runtime_sec"] == 1.5
    assert payload["version"] == "v-test"


def test_cli_version_falls_back(monkeypatch):
    def raise_error(_):
        raise md.PackageNotFoundError  # type: ignore[misc]

    monkeypatch.setattr(cli.md, "version", raise_error)
    assert cli._resolve_version() == "unknown"
