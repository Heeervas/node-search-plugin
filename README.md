# Node Search 🕸️

Version: `0.2.0`

Hermes Agent plugin exposing `node_search`: a bounded first-pass Markdown/Obsidian metadata and link-graph candidate selector.

Use it when an agent needs to decide **which Markdown notes to read next**: topic/project context, YAML/frontmatter filters, tags, backlinks, outgoing links, orphan/no-backlink notes, unresolved/dangling wikilinks, ambiguous links, and small graph expansion. It returns compact candidate evidence; the agent should then call `read_file` only on selected files.

It intentionally does **not** search full Markdown bodies in v1. Use normal file/content search for exact prose snippets, scripts, tables, transcripts, or non-Markdown files.

## Features

- Model-callable `node_search` tool.
- Configurable allowed Markdown roots.
- `.md` files only.
- YAML frontmatter, headings, Obsidian wikilinks, outgoing links, backlinks.
- Explicit malformed YAML, unresolved links, orphan/no-backlink nodes, and ambiguous basename resolution.
- Graph/link-health filters: `orphan`, `no_backlinks`, `unresolved`/`dangling`, `ambiguous`, `has_outgoing`, `has_incoming`.
- Intent modes: `auto`, `topic_context`, `graph_health`, `metadata`, `link_neighborhood`.
- Optional compact `why_read` evidence for triage before reading files.
- JSON cache derived from `$HERMES_HOME` or `NODE_SEARCH_CACHE`.
- Empty broad calls fail with repair examples instead of dumping a vault.

## Requirements

- Hermes Agent with plugin support.
- Python 3.10+.
- `PyYAML`.

## Installation

Default profile:

```bash
mkdir -p ~/.hermes/plugins
git clone https://github.com/eve-ai-dev/node-search-plugin.git ~/.hermes/plugins/node-search
hermes plugins enable node-search
```

Named profile:

```bash
mkdir -p ~/.hermes/profiles/<profile>/plugins
git clone https://github.com/eve-ai-dev/node-search-plugin.git ~/.hermes/profiles/<profile>/plugins/node-search
hermes -p <profile> plugins enable node-search
```

Restart the CLI/gateway after enabling because plugin discovery and tool schemas load at startup.

## Configuration

Set at least one allowed Markdown root for shared/public installs:

```bash
export NODE_SEARCH_ALLOWED_ROOTS="$HOME/notes,$HOME/work/wiki"
```

Compatibility variables:

| Variable | Default | Purpose |
|---|---:|---|
| `NODE_SEARCH_ALLOWED_ROOTS` | `$HERMES_HOME/brain` | Comma-separated roots that `scope` may scan inside. |
| `NODE_SEARCH_ROOT` | empty | Legacy single-root override; prepended to allowed roots when set. |
| `NODE_SEARCH_CACHE` | `$HERMES_HOME/.cache/hermes/node_search/index.json` | JSON index cache path. |

Security notes:

- `scope` may be relative to the selected root or absolute inside it.
- Symlink/path traversal escapes are rejected or ignored.
- The tool returns metadata/link candidates, not file bodies.
- Result count, graph depth, links per node, headings, and frontmatter size are capped.

## Example calls

Topic context:

```json
{
  "scope": "obsidian-vault",
  "mode": "topic_context",
  "query": "market radar",
  "query_regex": false,
  "where": ["path", "basename", "frontmatter", "links"],
  "include": ["frontmatter", "incoming_links", "outgoing_links", "why_read"],
  "depth": 1,
  "expand": "both",
  "limit": 10
}
```

Regex over indexed fields:

```json
{
  "scope": "obsidian-vault",
  "query": "market[-_ ]radar|massive",
  "query_regex": true,
  "where": ["path", "basename", "frontmatter"],
  "include": ["why_read"],
  "limit": 10
}
```

Graph health:

```json
{
  "scope": "obsidian-vault",
  "mode": "graph_health",
  "link_state": ["orphan"],
  "include": ["incoming_links", "why_read"],
  "exclude_path_filter": ["archive/", "request_dump"],
  "limit": 25
}
```

```json
{
  "scope": "obsidian-vault",
  "link_state": ["unresolved"],
  "include": ["outgoing_links", "why_read"],
  "limit": 25
}
```

Guardrail: calls must provide `scope` plus at least one narrowing parameter: `query`, `frontmatter`, `tags`, `has_links_to`, `linked_from`, `link_state`, `path_filter`, or a non-`auto` `mode`.

## Benchmark

The repository includes `benchmark_node_search.py`, a small reproducible benchmark using a fixed synthetic Obsidian-like dataset generated in a temporary directory. It does not require or expose a private/live vault.

```bash
python benchmark_node_search.py --repeats 7 \
  --json-out benchmark_results.synthetic.json \
  --md-out benchmark_results.synthetic.md
```

## Development

```bash
python -m pip install pytest ruff pyyaml
python -m py_compile __init__.py node_index.py benchmark_node_search.py
ruff check .
python -m pytest . -q
```

Before publishing, scan for secrets and private artifacts. Do not commit real vault exports, handoffs, plans, `.env`, session transcripts, or internal docs.
