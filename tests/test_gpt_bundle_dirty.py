import importlib.util


def test_gpt_bundle_stashes_when_dirty() -> None:
    spec = importlib.util.spec_from_file_location("gpt_bundle", "tools/gpt_bundle.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    statuses = [" M dirty.txt\n", ""]
    stash_calls: list[str] = []

    def fake_status() -> str:
        return statuses.pop(0) if statuses else ""

    def fake_stash_push(label: str) -> str:
        stash_calls.append(label)
        return "stash@{0}"

    mod._git_status_porcelain = fake_status
    mod._stash_push = fake_stash_push

    status_before, stash_ref, dirty = mod._prepare_worktree("temp: gpt_bundle", no_stash=False)
    assert dirty is True
    assert status_before.strip() == "M dirty.txt"
    assert stash_ref == "stash@{0}"
    assert stash_calls == ["temp: gpt_bundle"]


def test_gpt_bundle_root_is_local() -> None:
    spec = importlib.util.spec_from_file_location("gpt_bundle", "tools/gpt_bundle.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    bundle_root = mod._bundle_root()
    assert str(bundle_root).endswith("artifacts/_local/gpt_bundles")
