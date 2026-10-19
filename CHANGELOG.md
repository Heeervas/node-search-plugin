# Changelog

## 0.3.1

- Declare bounded PyYAML runtime dependency and pin development tools; remove ineffective Python-3.13-only empty lock.
- Defer profile policy lookups until calls rather than module import.
- Bind disk cache reuse to root/scope and rebuild links/backlinks after deletions.
- Add synthetic cache/profile/confinement regressions and accurate cache/privacy disclosures.

## Unreleased

- Add compact raw output as the default result schema (`node_search.compact.v1`): `frontmatter_summary`, link counts, capped evidence, and response cap metadata.
- Add explicit `output_mode: "full"` / legacy include escape hatches for raw frontmatter and link arrays.
- Add plugin YAML output defaults plus per-call overrides for frontmatter presets/fields, link detail, evidence detail, and result caps.
- Add graph-health summary metadata for graph-health/link-state calls.
- Adopt public agent-managed repository metadata.
