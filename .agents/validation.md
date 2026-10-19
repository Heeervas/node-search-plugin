# Validation contract

Acceptance owner: repository owner/coordinator. Scope: Node Search catalogue preparation only; no pushes, publication or live vault scans. Preserve tool name/schema and query/output semantics. Synthetic Markdown only.

## Behaviour and packaging

Run from the repository. Clear launch-profile policy for standalone tests (tests set their own roots); use the existing Hermes development interpreter for the real secret-scope integration test.

```sh
env -u NODE_SEARCH_ROOT -u NODE_SEARCH_ALLOWED_ROOTS -u NODE_SEARCH_CACHE python -m pytest . -q --basetemp=/opt/data/profiles/builder/cache/scratch/node-search-pytest
python -m py_compile __init__.py node_index.py benchmark_node_search.py test_catalogue_regressions.py
ruff check .
git diff --check
```

Install pinned tooling from requirements-dev.txt in an isolated writable environment before claiming pinned-tool checks. Verify the declared PyYAML lower bound separately from the core-constrained version. CI retains the Python 3.10–3.12 standalone matrix; local Python 3.14 evidence does not prove that matrix.

Current upstream admission: execute unmodified `hermes_cli.plugin_validate.validate_plugin_dir` from an isolated upstream checkout, including capability subprocess, scanner, no-core-override and private-import checks. Record upstream SHA. Full dependency admission additionally requires `hermes plugins validate <candidate> --install-deps` in an isolated writable environment, never the running Hermes core. Static admission is not dependency-install evidence.

## Deterministic quality

Canonical external dependency: builder-assurance skill version 1.1.0, resolved under `/opt/data/profiles/builder/skills/software-development/builder-assurance`. Policy schema is vendored locally; another machine must supply that version or explicitly report the missing dependency.

```sh
python /opt/data/profiles/builder/skills/software-development/builder-assurance/scripts/validate_quality_policy.py .agents/quality.yaml
python /opt/data/profiles/builder/skills/software-development/builder-assurance/scripts/quality_report.py --repo . --base 448d827ef4bdc32efe031c20bf3c315ffc91b351 --scope all --level top --config .agents/quality.yaml --format json > outputs/quality.json
```

Original immutable baseline: 448d827ef4bdc32efe031c20bf3c315ffc91b351. TOP covers profile boundaries and cache integrity. Independent review is required for isolation/cache changes and this new policy. No approved exceptions. Outstanding installation, lint or review gates prevent acceptance even when quality metrics pass.
