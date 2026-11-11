import io
import json
import os
import subprocess
import sys
from pathlib import Path

import mcp_server


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_vault(tmp_path: Path) -> Path:
    root = tmp_path / "brain"
    write(root / "vault" / "Alpha.md", "---\ntitle: Alpha\ntags: [project]\n---\n# Intro\nSee [[Beta]].")
    write(root / "vault" / "Beta.md", "---\ntitle: Beta\n---\nBack to [[Alpha]].")
    return root


def rpc(server, method, params=None, msg_id=1):
    message = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        message["params"] = params
    return server.handle(message)


def test_initialize_list_and_schema_match_plugin():
    schema_fn, handler = mcp_server.load_plugin()
    server = mcp_server.Server(schema_fn, handler)
    init = rpc(server, "initialize", {"protocolVersion": "2025-06-18"})["result"]
    assert init["protocolVersion"] == "2025-06-18"
    assert init["capabilities"] == {"tools": {"listChanged": False}}
    unknown = rpc(server, "initialize", {"protocolVersion": "1999-01-01"})["result"]
    assert unknown["protocolVersion"] == mcp_server.SUPPORTED_PROTOCOLS[0]
    tools = rpc(server, "tools/list")["result"]["tools"]
    assert [t["name"] for t in tools] == ["node_search"]
    assert tools[0]["inputSchema"] == schema_fn()["parameters"]
    assert rpc(server, "ping")["result"] == {}


def test_call_returns_results_and_flags_errors(tmp_path, monkeypatch):
    root = make_vault(tmp_path)
    monkeypatch.setenv("NODE_SEARCH_ALLOWED_ROOTS", str(root))
    monkeypatch.setenv("NODE_SEARCH_CACHE", str(tmp_path / "cache.json"))
    monkeypatch.delenv("NODE_SEARCH_ROOT", raising=False)
    server = mcp_server.Server(*mcp_server.load_plugin())

    ok = rpc(server, "tools/call", {"name": "node_search", "arguments": {"scope": "vault", "query": "alpha", "where": ["basename"]}})["result"]
    payload = json.loads(ok["content"][0]["text"])
    assert ok["isError"] is False and payload["success"] is True
    assert [r["path"] for r in payload["results"]] == ["vault/Alpha.md"]

    outside = rpc(server, "tools/call", {"name": "node_search", "arguments": {"scope": "/etc"}})["result"]
    assert outside["isError"] is True and json.loads(outside["content"][0]["text"])["success"] is False


def test_protocol_errors_and_notifications():
    server = mcp_server.Server(*mcp_server.load_plugin())
    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    assert rpc(server, "resources/list")["error"]["code"] == mcp_server.METHOD_NOT_FOUND
    assert rpc(server, "tools/call", {"name": "other"})["error"]["code"] == mcp_server.INVALID_PARAMS
    assert rpc(server, "tools/call", {"name": "node_search", "arguments": []})["error"]["code"] == mcp_server.INVALID_PARAMS
    assert server.handle(["not", "an", "object"])["error"]["code"] == mcp_server.INVALID_REQUEST

    out = io.StringIO()
    mcp_server.serve(server, io.StringIO("{broken\n\n" + json.dumps({"jsonrpc": "2.0", "id": 7, "method": "ping"}) + "\n"), out)
    replies = [json.loads(line) for line in out.getvalue().splitlines()]
    assert replies[0]["error"]["code"] == mcp_server.PARSE_ERROR
    assert replies[1] == {"jsonrpc": "2.0", "id": 7, "result": {}}


def test_stdio_entry_point(tmp_path):
    root = make_vault(tmp_path)
    env = {k: v for k, v in os.environ.items() if not k.startswith("NODE_SEARCH_")}
    env.update(NODE_SEARCH_ALLOWED_ROOTS=str(root), NODE_SEARCH_CACHE=str(tmp_path / "cache.json"), HERMES_HOME=str(tmp_path / "home"))
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "node_search", "arguments": {"scope": "vault", "mode": "graph_health", "link_state": ["has_incoming"]}}},
    ]
    proc = subprocess.run([sys.executable, str(Path(mcp_server.__file__))], input="\n".join(json.dumps(m) for m in messages) + "\n",
                          capture_output=True, text=True, env=env, timeout=60, check=True)
    replies = [json.loads(line) for line in proc.stdout.splitlines()]
    assert [r["id"] for r in replies] == [1, 2]
    payload = json.loads(replies[1]["result"]["content"][0]["text"])
    assert payload["success"] is True
    assert sorted(r["path"] for r in payload["results"]) == ["vault/Alpha.md", "vault/Beta.md"]
