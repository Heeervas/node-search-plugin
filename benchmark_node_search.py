#!/usr/bin/env python3
"""Benchmark fixtures and README-friendly rendering for node_search.

This script uses a small synthetic Obsidian-like dataset generated in a
temporary directory. Results are real measurements of local node_search code,
not measurements of a private/live vault.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

# Allow running directly from this plugin directory without installation.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from node_index import node_search  # noqa: E402


FIXTURES: Dict[str, str] = {
    "00_index/Map of Content.md": """---
title: Knowledge Map
tags: [moc]
status: evergreen
---
# Knowledge Map
Links: [[20_projects/Market Radar]], [[20_projects/AI Roadmap]], [[40_people/Ada Lovelace]].
""",
    "20_projects/Market Radar.md": """---
title: Market Radar
tags: [project, intelligence]
status: active
owner: alberto
---
# Market Radar
Tracks [[30_sources/Gartner Report]] and [[30_sources/Massive Source]].
Mentions [[40_people/Ada Lovelace|Ada]] and [[Missing Vendor]].
""",
    "20_projects/AI Roadmap.md": """---
title: AI Roadmap
tags: [project, ai]
status: active
owner: alberto
---
# AI Roadmap
Depends on [[20_projects/Market Radar]] and [[30_sources/Deep Learning Paper]].
""",
    "20_projects/Archive Plan.md": """---
title: Archive Plan
tags: [project]
status: archived
---
# Archive Plan
Old work. Links to [[20_projects/Market Radar]].
""",
    "30_sources/Gartner Report.md": """---
title: Gartner Report
tags: [source, market]
year: 2026
---
# Gartner Report
Referenced by market analysis.
""",
    "30_sources/Massive Source.md": """---
title: Massive Source
tags: [source, intelligence]
year: 2025
---
# Massive Source
Related to [[30_sources/Gartner Report]].
""",
    "30_sources/Deep Learning Paper.md": """---
title: Deep Learning Paper
tags: [source, ai]
year: 2024
---
# Deep Learning Paper
See [[40_people/Ada Lovelace]].
""",
    "40_people/Ada Lovelace.md": """---
title: Ada Lovelace
tags: [person]
---
# Ada Lovelace
Linked from projects and sources.
""",
    "50_inbox/Orphan Idea.md": """---
title: Orphan Idea
tags: [inbox]
---
# Orphan Idea
No backlinks yet, but links to [[Unresolved Concept]].
""",
    "60_collisions/one/Target.md": """---
title: Target One
---
# Target One
""",
    "60_collisions/two/Target.md": """---
title: Target Two
---
# Target Two
""",
    "60_collisions/Source.md": """---
title: Ambiguous Source
---
# Ambiguous Source
This deliberately links to [[Target]].
""",
    ".trash/Deleted.md": """---
title: Deleted runtime noise
---
# Deleted
Should be excluded by default.
""",
}


@dataclass(frozen=True)
class QueryCase:
    id: str
    purpose: str
    args: Dict[str, Any]


QUERY_CASES: List[QueryCase] = [
    QueryCase(
        "topic_context",
        "Recuperar contexto de un tema/proyecto y vecinos inmediatos.",
        {
            "scope": None,
            "mode": "topic_context",
            "query": "market radar",
            "where": ["path", "basename", "frontmatter", "links", "headings"],
            "include": ["frontmatter", "incoming_links", "outgoing_links", "why_read"],
            "depth": 1,
            "expand": "both",
            "limit": 10,
        },
    ),
    QueryCase(
        "metadata_active_ai",
        "Filtrar notas por YAML/frontmatter y tags.",
        {
            "scope": None,
            "mode": "metadata",
            "frontmatter": {"status": "active"},
            "tags": ["ai"],
            "include": ["frontmatter", "why_read"],
            "limit": 10,
        },
    ),
    QueryCase(
        "link_neighborhood",
        "Encontrar notas que enlazan a una entidad conocida.",
        {
            "scope": None,
            "mode": "link_neighborhood",
            "has_links_to": ["Ada Lovelace"],
            "include": ["outgoing_links", "incoming_links", "why_read"],
            "limit": 10,
        },
    ),
    QueryCase(
        "graph_orphans",
        "Auditar nodos sin backlinks, excluyendo ruido por defecto.",
        {
            "scope": None,
            "mode": "graph_health",
            "link_state": ["orphan"],
            "include": ["incoming_links", "why_read"],
            "limit": 20,
        },
    ),
    QueryCase(
        "graph_unresolved",
        "Auditar wikilinks no resueltos/dangling.",
        {
            "scope": None,
            "mode": "graph_health",
            "link_state": ["unresolved"],
            "include": ["outgoing_links", "why_read"],
            "limit": 20,
        },
    ),
    QueryCase(
        "graph_ambiguous",
        "Auditar enlaces ambiguos por colisión de basename.",
        {
            "scope": None,
            "mode": "graph_health",
            "link_state": ["ambiguous"],
            "include": ["outgoing_links", "why_read"],
            "limit": 20,
        },
    ),
    QueryCase(
        "regex_indexed_fields",
        "Probar regex solo en campos indexados, no en cuerpo completo.",
        {
            "scope": None,
            "query": "market[-_ ]radar|massive",
            "query_regex": True,
            "where": ["path", "basename", "frontmatter"],
            "include": ["frontmatter"],
            "limit": 10,
        },
    ),
]


def create_fixture(root: Path) -> None:
    for rel, text in FIXTURES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def run_case(case: QueryCase, root: Path, cache_path: Path, repeats: int, refresh_first: bool) -> Dict[str, Any]:
    timings_ms: List[float] = []
    last_result: Dict[str, Any] = {}
    for i in range(repeats):
        args = dict(case.args)
        args["root"] = root
        args["cache_path"] = cache_path
        args["refresh"] = bool(refresh_first and i == 0)
        t0 = time.perf_counter()
        last_result = node_search(**args)
        timings_ms.append((time.perf_counter() - t0) * 1000)
    paths = [item["path"] for item in last_result.get("results", [])]
    stats = last_result.get("stats", {})
    return {
        "id": case.id,
        "purpose": case.purpose,
        "count": last_result.get("count", 0),
        "truncated": last_result.get("truncated", False),
        "median_ms": statistics.median(timings_ms),
        "min_ms": min(timings_ms),
        "max_ms": max(timings_ms),
        "top_paths": paths[:5],
        "vault_files_indexed": stats.get("total", "?"),
        "args": {k: v for k, v in case.args.items() if k != "scope"},
    }


def md_escape(value: Any) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render_markdown(rows: List[Dict[str, Any]], repeats: int) -> str:
    lines = [
        "# Benchmark de `node_search`",
        "",
        "> Resultados generados con dataset sintético fijo; no representan un vault privado/live.",
        f"> Cada caso se ejecutó {repeats} vez/veces. La primera ejecución fuerza `refresh` para medir parseo+cache; las siguientes miden cache caliente.",
        "",
        "| Caso | Objetivo | Resultados | Mediana ms | Rango ms | Top paths |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        top_paths = "<br>".join(md_escape(p) for p in row["top_paths"]) or "—"
        lines.append(
            "| {id} | {purpose} | {count} | {median:.2f} | {minv:.2f}–{maxv:.2f} | {paths} |".format(
                id=md_escape(row["id"]),
                purpose=md_escape(row["purpose"]),
                count=row["count"],
                median=row["median_ms"],
                minv=row["min_ms"],
                maxv=row["max_ms"],
                paths=top_paths,
            )
        )
    lines.extend(
        [
            "",
            "## Consultas benchmark",
            "",
            "Estas formas cubren los usos esperados para README/open source: contexto temático, filtros de metadatos, vecindario de enlaces, salud del grafo y regex en campos indexados.",
            "",
        ]
    )
    for row in rows:
        lines.append(f"### `{row['id']}`")
        lines.append("")
        lines.append(row["purpose"])
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(row["args"], ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5, help="repeticiones por caso")
    parser.add_argument("--json-out", type=Path, default=Path("benchmark_results.synthetic.json"))
    parser.add_argument("--md-out", type=Path, default=Path("benchmark_results.synthetic.md"))
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="node-search-bench-") as tmp:
        root = Path(tmp) / "brain"
        cache = Path(tmp) / "cache.json"
        create_fixture(root)
        rows = [run_case(case, root, cache, max(1, args.repeats), refresh_first=True) for case in QUERY_CASES]

    payload = {
        "label": "synthetic-fixed-dataset",
        "warning": "Resultados reales de node_search sobre dataset sintético fijo; no son mediciones de un vault live/privado.",
        "fixture_file_count": len(FIXTURES),
        "repeats": max(1, args.repeats),
        "rows": rows,
    }
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    args.md_out.write_text(render_markdown(rows, max(1, args.repeats)), encoding="utf-8")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.md_out}")
    print(render_markdown(rows, max(1, args.repeats)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
