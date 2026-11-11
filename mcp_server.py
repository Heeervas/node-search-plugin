"""node-search MCP server (stdio, newline-delimited JSON-RPC 2.0).

Exposes the unchanged `node_search` tool to any MCP client. The tool schema and
argument handling are loaded from the plugin entry module, so Hermes and MCP
share one contract. Configuration uses the standalone environment variables
NODE_SEARCH_ALLOWED_ROOTS / NODE_SEARCH_ROOT and NODE_SEARCH_CACHE.
No third-party MCP SDK is required; only PyYAML (via node_index) is needed.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TextIO, Tuple

SERVER_NAME = "node-search"
SERVER_VERSION = "0.3.1"
SUPPORTED_PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS = -32700, -32600, -32601, -32602


def load_plugin() -> Tuple[Callable[[], Dict[str, Any]], Callable[..., str]]:
    """Load the plugin entry module from this directory and return (schema, handler)."""
    path = Path(__file__).resolve().parent / "__init__.py"
    spec = importlib.util.spec_from_file_location("node_search_plugin", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("node-search plugin entry module not found")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._schema, module._handler


def tool_definition(schema: Dict[str, Any]) -> Dict[str, Any]:
    return {"name": schema["name"], "description": schema["description"], "inputSchema": schema["parameters"]}


def _error(msg_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _result(msg_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


class Server:
    def __init__(self, schema_fn: Callable[[], Dict[str, Any]], handler: Callable[..., str]):
        self.schema = schema_fn()
        self.handler = handler

    def handle(self, message: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            return _error(message.get("id") if isinstance(message, dict) else None, INVALID_REQUEST, "invalid request")
        if "id" not in message:
            return None  # Notifications (e.g. notifications/initialized) need no reply.
        msg_id, method = message["id"], message["method"]
        params = message.get("params") or {}
        if not isinstance(params, dict):
            return _error(msg_id, INVALID_PARAMS, "params must be an object")
        if method == "initialize":
            requested = params.get("protocolVersion")
            version = requested if requested in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0]
            return _result(msg_id, {"protocolVersion": version, "capabilities": {"tools": {"listChanged": False}},
                                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION}})
        if method == "ping":
            return _result(msg_id, {})
        if method == "tools/list":
            return _result(msg_id, {"tools": [tool_definition(self.schema)]})
        if method == "tools/call":
            return self._call(msg_id, params)
        return _error(msg_id, METHOD_NOT_FOUND, f"method not found: {method}")

    def _call(self, msg_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        if params.get("name") != self.schema["name"]:
            return _error(msg_id, INVALID_PARAMS, f"unknown tool: {params.get('name')}")
        arguments = params.get("arguments")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            return _error(msg_id, INVALID_PARAMS, "arguments must be an object")
        text = self.handler(arguments)
        try:
            success = bool(json.loads(text).get("success"))
        except (ValueError, AttributeError):
            success = False
        return _result(msg_id, {"content": [{"type": "text", "text": text}], "isError": not success})


def serve(server: Server, stdin: TextIO, stdout: TextIO) -> None:
    for line in stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except ValueError:
            reply: Optional[Dict[str, Any]] = _error(None, PARSE_ERROR, "parse error")
        else:
            reply = server.handle(message)
        if reply is not None:
            stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            stdout.flush()


def main() -> int:
    schema_fn, handler = load_plugin()
    serve(Server(schema_fn, handler), sys.stdin, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
