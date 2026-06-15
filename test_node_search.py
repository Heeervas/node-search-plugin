from pathlib import Path

import pytest

from node_index import NodeSearchError, build_index, node_search


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_frontmatter_links_backlinks_and_aliases(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "A.md", """---
title: Alpha
tags: [project, ai]
status: active
---
# Intro
Links to [[B|Bee]] and ![[Missing]].""")
    write(root / "B.md", """---
title: Beta
---
Back to [[A#Intro]].""")

    result = node_search(scope=None, query="alpha", tags=["ai"], root=root, cache_path=cache, include=["frontmatter", "outgoing_links", "incoming_links", "headings"])

    assert result["success"] is True
    assert result["count"] == 1
    a = result["results"][0]
    assert a["path"] == "A.md"
    assert a["frontmatter"]["status"] == "active"
    assert "Intro" in a["headings"]
    assert any(link["resolved_path"] == "B.md" for link in a["outgoing_links"])
    assert any(link["target"] == "Missing" and not link["resolved"] for link in a["outgoing_links"])
    assert a["incoming_links"] == ["B.md"]


def test_malformed_frontmatter_is_structured_error(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "bad.md", """---
foo: [
---
Body""")

    result = node_search(query="bad", root=root, cache_path=cache, include=["frontmatter"])

    assert result["count"] == 1
    item = result["results"][0]
    assert item["frontmatter_ok"] is False
    assert item["frontmatter_error"]


def test_ambiguous_basename_link_is_explicit(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "one" / "Target.md", "# One")
    write(root / "two" / "Target.md", "# Two")
    write(root / "Source.md", "[[Target]]")

    result = node_search(query="Source", root=root, cache_path=cache, include=["outgoing_links"])
    links = result["results"][0]["outgoing_links"]

    assert links[0]["resolved"] is False
    assert links[0]["ambiguous"] is True
    assert sorted(links[0]["candidates"]) == ["one/Target.md", "two/Target.md"]


def test_path_traversal_rejected(tmp_path):
    root = tmp_path / "brain"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(NodeSearchError):
        build_index(str(outside), root=root, cache_path=tmp_path / "cache.json")


def test_symlink_escape_is_ignored(tmp_path):
    root = tmp_path / "brain"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    write(outside / "secret.md", "[[Nope]]")
    (root / "link.md").symlink_to(outside / "secret.md")

    result = node_search(path_filter="link", root=root, cache_path=tmp_path / "cache.json")

    assert result["stats"]["total"] == 0


def test_depth_expands_graph(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "A.md", """---
title: Seed
---
[[B]]""")
    write(root / "B.md", "[[C]]")
    write(root / "C.md", "leaf")

    result = node_search(query="Seed", depth=1, expand="outgoing", root=root, cache_path=cache, include=[])
    paths = {item["path"] for item in result["results"]}

    assert paths == {"A.md", "B.md"}


def test_path_filter_filters_results_without_changing_scan_contract(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "projects" / "A.md", """---
title: Seed
---
[[B]]""")
    write(root / "archive" / "B.md", "target")

    result = node_search(path_filter="projects", query="Seed", depth=1, expand="outgoing", root=root, cache_path=cache, include=[])
    paths = {item["path"] for item in result["results"]}

    assert paths == {"projects/A.md", "archive/B.md"}
    assert result["stats"]["total"] == 2


def test_empty_call_rejected_instead_of_dumping_vault(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "A.md", "# A")

    with pytest.raises(NodeSearchError, match="orphan/no-backlink notes"):
        node_search(root=root, cache_path=cache)


def test_query_regex_defaults_on_and_explicit_false_is_honored(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "Wild Project.md", "# Wild Project")
    write(root / "Wild X Project.md", "# Wild X Project")
    write(root / "Other.md", "# Other")

    default_regex = node_search(query="Wild Project", where=["path", "basename"], root=root, cache_path=cache, include=[])
    assert {item["path"] for item in default_regex["results"]} == {"Wild Project.md"}

    literal = node_search(query="Wild Project", query_regex=False, where=["path", "basename"], root=root, cache_path=cache, include=[])
    assert {item["path"] for item in literal["results"]} == {"Wild Project.md"}


def test_query_regex_matches_indexed_fields(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "market_radar.md", """---
title: Market Radar
---
# Alpha""")
    write(root / "massive_source.md", """---
title: Massive source
---
# Beta""")
    write(root / "other.md", """---
title: Banana
---
# Gamma""")

    result = node_search(query="market[-_ ]radar|massive", query_regex=True, where=["path", "basename", "frontmatter"], root=root, cache_path=cache, include=[])
    paths = {item["path"] for item in result["results"]}

    assert paths == {"market_radar.md", "massive_source.md"}


def test_invalid_query_regex_returns_user_error(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "A.md", "# A")

    with pytest.raises(NodeSearchError, match="Invalid query_regex"):
        node_search(query="[", query_regex=True, root=root, cache_path=cache)


def test_link_state_orphan_and_unresolved_filters(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "Orphan.md", "[[Missing]]")
    write(root / "Linked.md", "[[Target]]")
    write(root / "Target.md", "target")

    orphans = node_search(link_state=["orphan"], root=root, cache_path=cache, include=["incoming_links"])
    orphan_paths = {item["path"] for item in orphans["results"]}
    assert "Orphan.md" in orphan_paths
    assert "Linked.md" in orphan_paths
    assert "Target.md" not in orphan_paths

    unresolved = node_search(link_state=["unresolved"], root=root, cache_path=cache, include=["outgoing_links"])
    assert [item["path"] for item in unresolved["results"]] == ["Orphan.md"]
    assert unresolved["results"][0]["matched"] == ["link_state.unresolved"]


def test_link_state_ambiguous_and_invalid_state(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "one" / "Target.md", "# One")
    write(root / "two" / "Target.md", "# Two")
    write(root / "Source.md", "[[Target]]")

    ambiguous = node_search(link_state=["ambiguous"], root=root, cache_path=cache, include=["outgoing_links"])
    assert [item["path"] for item in ambiguous["results"]] == ["Source.md"]
    assert ambiguous["results"][0]["matched"] == ["link_state.ambiguous"]

    with pytest.raises(NodeSearchError, match="Invalid link_state"):
        node_search(link_state=["lolno"], root=root, cache_path=cache)


def test_default_excludes_runtime_noise_and_can_be_disabled(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "live" / "A.md", "# A")
    write(root / ".trash" / "Trash.md", "# Trash")
    write(root / ".pytest_cache" / "Cache.md", "# Cache")

    defaulted = node_search(mode="graph_health", link_state=["orphan"], root=root, cache_path=cache, include=[])
    assert {item["path"] for item in defaulted["results"]} == {"live/A.md"}

    explicit = node_search(mode="graph_health", link_state=["orphan"], exclude_defaults=False, root=root, cache_path=cache, include=[])
    assert {item["path"] for item in explicit["results"]} == {".pytest_cache/Cache.md", ".trash/Trash.md", "live/A.md"}


def test_exclude_path_filter_applies_to_seeds_and_expansion(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "projects" / "A.md", """---
title: Seed
---
[[archive/B]]""")
    write(root / "archive" / "B.md", "target")

    result = node_search(query="Seed", depth=1, expand="outgoing", exclude_path_filter=["archive/"], root=root, cache_path=cache, include=[])
    assert {item["path"] for item in result["results"]} == {"projects/A.md"}


def test_mode_and_why_read_are_intent_hints_without_priority_bias(tmp_path):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "B.md", "# B")
    write(root / "A.md", """---
title: Alpha
tags: [x]
---
# Heading
[[B]]""")

    result = node_search(mode="topic_context", query="Alpha", root=root, cache_path=cache, include=["why_read", "headings"])
    assert result["mode"] == "topic_context"
    assert result["results"][0]["path"] == "A.md"
    assert "mode.topic_context" in result["results"][0]["matched"]
    assert any("mode=topic_context" == reason for reason in result["results"][0]["why_read"])

    with pytest.raises(NodeSearchError, match="mode must be one of"):
        node_search(mode="priority", root=root, cache_path=cache)


def test_cached_index_preserves_resolved_graph_without_re_resolving(tmp_path, monkeypatch):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "A.md", "[[B]] and [[Missing]]")
    write(root / "B.md", "[[A]]")

    first = node_search(query="A", root=root, cache_path=cache, include=["outgoing_links", "incoming_links"], refresh=True)
    assert first["results"][0]["incoming_links"] == ["B.md"]
    assert any(link["resolved_path"] == "B.md" for link in first["results"][0]["outgoing_links"])

    def explode(_nodes):
        raise AssertionError("warm cache should reuse resolved graph without _resolve_links")

    monkeypatch.setattr("node_index._resolve_links", explode)
    second = node_search(query="A", root=root, cache_path=cache, include=["outgoing_links", "incoming_links"])

    assert second["stats"]["parsed"] == 0
    assert second["stats"].get("graph_reused") is True
    assert second["results"][0]["incoming_links"] == ["B.md"]
    assert any(link["resolved_path"] == "B.md" for link in second["results"][0]["outgoing_links"])


def test_in_process_cache_reuses_nodes_and_invalidates_on_file_change(tmp_path, monkeypatch):
    root = tmp_path / "brain"
    cache = tmp_path / "cache.json"
    write(root / "A.md", """---
title: Alpha
---
[[B]]""")
    write(root / "B.md", "# B")

    first = node_search(query="Alpha", root=root, cache_path=cache, include=[], refresh=True)
    assert first["stats"]["parsed"] == 2

    second = node_search(query="Alpha", root=root, cache_path=cache, include=[])
    assert second["stats"]["parsed"] == 0
    assert second["stats"].get("memory_reused") is True

    def explode_load(_cache_path):
        raise AssertionError("changed file should force JSON reload after invalidating in-process cache")

    monkeypatch.setattr("node_index._load_cache", explode_load)
    second = node_search(query="Alpha", root=root, cache_path=cache, include=[])
    assert second["stats"]["parsed"] == 0
    assert second["stats"].get("memory_reused") is True

    write(root / "B.md", "# B updated")
    third = node_search(query="Alpha", root=root, cache_path=cache, include=[], refresh=True)
    assert third["stats"]["parsed"] == 2


def test_configured_allowed_roots_reject_absolute_escape(tmp_path, monkeypatch):
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    write(allowed / "A.md", "# A")
    write(outside / "Secret.md", "# Secret")
    monkeypatch.setenv("NODE_SEARCH_ALLOWED_ROOTS", str(allowed))

    with pytest.raises(NodeSearchError, match="outside configured allowed roots"):
        node_search(scope=str(outside), query="Secret", cache_path=tmp_path / "cache.json")


def test_absolute_scope_inside_configured_allowed_root_selects_root(tmp_path, monkeypatch):
    allowed = tmp_path / "allowed"
    sub = allowed / "vault"
    write(sub / "A.md", "# A")
    monkeypatch.setenv("NODE_SEARCH_ALLOWED_ROOTS", str(allowed))

    result = node_search(scope=str(sub), query="A", cache_path=tmp_path / "cache.json")

    assert result["success"] is True
    assert result["root"] == str(allowed.resolve())
    assert result["base"] == "vault"
    assert result["results"][0]["path"] == "vault/A.md"
