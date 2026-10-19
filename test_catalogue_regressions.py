"""Synthetic regressions for cache identity and profile-safe loading."""
import os
from pathlib import Path

import pytest

import node_index as index


def note(root, name, text):
    root.mkdir(parents=True, exist_ok=True)
    path = root / name
    path.write_text(text, encoding="utf-8")
    return path


def test_disk_cache_does_not_cross_roots(tmp_path):
    cache = tmp_path / "cache.json"
    a = note(tmp_path / "a", "Note.md", "# Alpha")
    b = note(tmp_path / "b", "Note.md", "# Bravo")
    os.utime(b, ns=(a.stat().st_atime_ns, a.stat().st_mtime_ns))
    index.build_index(root=a.parent, cache_path=cache)
    result = index.build_index(root=b.parent, cache_path=cache)
    assert result["nodes"]["Note.md"].headings == ["Bravo"]


@pytest.mark.parametrize("deleted", ["Source.md", "Target.md"])
def test_disk_graph_recomputed_after_deletion(tmp_path, deleted):
    root = tmp_path / "notes"
    cache = tmp_path / "cache.json"
    note(root, "Source.md", "[[Target]]")
    note(root, "Target.md", "# Target")
    first = index.build_index(root=root, cache_path=cache)
    assert first["nodes"]["Target.md"].incoming_links == ["Source.md"]
    (root / deleted).unlink()
    index._PROCESS_INDEX_CACHE.clear()  # Model a new interpreter reading the disk cache.
    result = index.build_index(root=root, cache_path=cache)
    if deleted == "Source.md":
        assert result["nodes"]["Target.md"].incoming_links == []
    else:
        link = result["nodes"]["Source.md"].outgoing_links[0]
        assert not link.resolved
        assert link.resolved_path is None


@pytest.mark.parametrize("scope", ["..", "escape"])
def test_scoped_directory_escape_rejected(tmp_path, monkeypatch, scope):
    root = tmp_path / "allowed"
    outside = tmp_path / "outside"
    note(root, "Safe.md", "# Safe")
    note(outside, "Outside.md", "# Outside")
    (root / "escape").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("NODE_SEARCH_ALLOWED_ROOTS", str(root))
    monkeypatch.delenv("NODE_SEARCH_ROOT", raising=False)
    with pytest.raises(index.NodeSearchError, match="outside allowed root"):
        index.build_index(scope, cache_path=tmp_path / "cache.json")


def test_profiles_use_scoped_policy_and_cache(tmp_path, monkeypatch):
    pytest.importorskip("agent.secret_scope", reason="Hermes profile integration requires Hermes")
    from agent.secret_scope import reset_secret_scope, set_secret_scope
    from hermes_constants import reset_hermes_home_override, set_hermes_home_override

    monkeypatch.setenv("NODE_SEARCH_ROOT", str(tmp_path / "launch-root"))
    for profile in ("a", "b", "a"):
        home = tmp_path / profile
        root = home / "notes"
        note(root, "Note.md", f"# Profile {profile}")
        home_token = set_hermes_home_override(str(home))
        secret_token = set_secret_scope({"NODE_SEARCH_ALLOWED_ROOTS": str(root)}, profile_home=str(home))
        try:
            result = index.node_search(scope=".", query=f"Profile {profile}")
            assert result["root"] == str(root)
            assert result["count"] == 1
            assert index.default_cache().is_relative_to(home)
            assert index.default_cache().exists()
            with pytest.raises(index.NodeSearchError, match="outside configured allowed roots"):
                index.node_search(scope=str(tmp_path / ("b" if profile == "a" else "a")), query="Profile")
        finally:
            reset_secret_scope(secret_token)
            reset_hermes_home_override(home_token)


def test_disk_cache_reuses_unchanged_graph_and_isolates_subscope(tmp_path):
    root = tmp_path / "notes"
    cache = tmp_path / "cache.json"
    note(root, "Source.md", "[[Target]]")
    note(root / "sub", "Target.md", "# Target")
    first = index.build_index(root=root, cache_path=cache)
    assert first["nodes"]["sub/Target.md"].incoming_links == ["Source.md"]
    index._PROCESS_INDEX_CACHE.clear()
    warm = index.build_index(root=root, cache_path=cache)
    assert warm["stats"]["graph_reused"]
    assert warm["nodes"]["sub/Target.md"].incoming_links == ["Source.md"]
    narrow = index.build_index("sub", root=root, cache_path=cache)
    assert narrow["nodes"]["sub/Target.md"].incoming_links == []


def test_import_does_not_read_scoped_policy(monkeypatch):
    import builtins

    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name == "agent.secret_scope":
            raise AssertionError("profile policy must be read at call time, not import time")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    source = Path(index.__file__).read_text(encoding="utf-8")
    exec(compile(source, index.__file__, "exec"), index.__dict__.copy())
