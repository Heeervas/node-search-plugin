# Benchmark de `node_search`

> Resultados generados con dataset sintético fijo; no representan un vault privado/live.
> Cada caso se ejecutó 7 vez/veces. La primera ejecución fuerza `refresh` para medir parseo+cache; las siguientes miden cache caliente.

| Caso | Objetivo | Resultados | Mediana ms | Rango ms | Top paths |
|---|---|---:|---:|---:|---|
| topic_context | Recuperar contexto de un tema/proyecto y vecinos inmediatos. | 8 | 2.99 | 2.96–8.39 | 20_projects/Market Radar.md<br>00_index/Map of Content.md<br>20_projects/AI Roadmap.md<br>20_projects/Archive Plan.md<br>30_sources/Gartner Report.md |
| metadata_active_ai | Filtrar notas por YAML/frontmatter y tags. | 1 | 2.86 | 2.79–7.64 | 20_projects/AI Roadmap.md |
| link_neighborhood | Encontrar notas que enlazan a una entidad conocida. | 3 | 2.88 | 2.84–7.63 | 00_index/Map of Content.md<br>20_projects/Market Radar.md<br>30_sources/Deep Learning Paper.md |
| graph_orphans | Auditar nodos sin backlinks, excluyendo ruido por defecto. | 6 | 2.88 | 2.85–7.88 | 00_index/Map of Content.md<br>20_projects/Archive Plan.md<br>50_inbox/Orphan Idea.md<br>60_collisions/one/Target.md<br>60_collisions/Source.md |
| graph_unresolved | Auditar wikilinks no resueltos/dangling. | 2 | 3.07 | 2.87–7.61 | 20_projects/Market Radar.md<br>50_inbox/Orphan Idea.md |
| graph_ambiguous | Auditar enlaces ambiguos por colisión de basename. | 1 | 3.16 | 2.85–8.80 | 60_collisions/Source.md |
| regex_indexed_fields | Probar regex solo en campos indexados, no en cuerpo completo. | 2 | 2.91 | 2.87–7.97 | 20_projects/Market Radar.md<br>30_sources/Massive Source.md |

## Consultas benchmark

Estas formas cubren los usos esperados para README/open source: contexto temático, filtros de metadatos, vecindario de enlaces, salud del grafo y regex en campos indexados.

### `topic_context`

Recuperar contexto de un tema/proyecto y vecinos inmediatos.

```json
{
  "mode": "topic_context",
  "query": "market radar",
  "where": [
    "path",
    "basename",
    "frontmatter",
    "links",
    "headings"
  ],
  "include": [
    "frontmatter",
    "incoming_links",
    "outgoing_links",
    "why_read"
  ],
  "depth": 1,
  "expand": "both",
  "limit": 10
}
```

### `metadata_active_ai`

Filtrar notas por YAML/frontmatter y tags.

```json
{
  "mode": "metadata",
  "frontmatter": {
    "status": "active"
  },
  "tags": [
    "ai"
  ],
  "include": [
    "frontmatter",
    "why_read"
  ],
  "limit": 10
}
```

### `link_neighborhood`

Encontrar notas que enlazan a una entidad conocida.

```json
{
  "mode": "link_neighborhood",
  "has_links_to": [
    "Ada Lovelace"
  ],
  "include": [
    "outgoing_links",
    "incoming_links",
    "why_read"
  ],
  "limit": 10
}
```

### `graph_orphans`

Auditar nodos sin backlinks, excluyendo ruido por defecto.

```json
{
  "mode": "graph_health",
  "link_state": [
    "orphan"
  ],
  "include": [
    "incoming_links",
    "why_read"
  ],
  "limit": 20
}
```

### `graph_unresolved`

Auditar wikilinks no resueltos/dangling.

```json
{
  "mode": "graph_health",
  "link_state": [
    "unresolved"
  ],
  "include": [
    "outgoing_links",
    "why_read"
  ],
  "limit": 20
}
```

### `graph_ambiguous`

Auditar enlaces ambiguos por colisión de basename.

```json
{
  "mode": "graph_health",
  "link_state": [
    "ambiguous"
  ],
  "include": [
    "outgoing_links",
    "why_read"
  ],
  "limit": 20
}
```

### `regex_indexed_fields`

Probar regex solo en campos indexados, no en cuerpo completo.

```json
{
  "query": "market[-_ ]radar|massive",
  "query_regex": true,
  "where": [
    "path",
    "basename",
    "frontmatter"
  ],
  "include": [
    "frontmatter"
  ],
  "limit": 10
}
```
