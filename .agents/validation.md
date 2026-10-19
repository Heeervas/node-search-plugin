# Validation contract

Acceptance owner: repository owner/coordinator. Scope: Node Search catalogue preparation only; no pushes, publication or live vault scans. Preserve tool name/schema and query/output semantics. Synthetic Markdown only.

## Behaviour and packaging

Run from the repository. Clear launch-profile policy for standalone tests (tests set their own roots); use the existing Hermes development interpreter for the real secret-scope integration test.

```sh
: "${NODE_SEARCH_VALIDATION_TMP:?Set to an absolute disposable scratch directory}"
env -u NODE_SEARCH_ROOT -u NODE_SEARCH_ALLOWED_ROOTS -u NODE_SEARCH_CACHE HERMES_HOME="$NODE_SEARCH_VALIDATION_TMP/test-home" python -m pytest . -q --basetemp="$NODE_SEARCH_VALIDATION_TMP/pytest"
PYTHONPYCACHEPREFIX="$NODE_SEARCH_VALIDATION_TMP/pycache" python -m py_compile __init__.py node_index.py benchmark_node_search.py test_catalogue_regressions.py
ruff check .
git diff --check 448d827ef4bdc32efe031c20bf3c315ffc91b351 HEAD
```

`--basetemp` alone does not redirect plugin state: the scratch `HERMES_HOME` is required. The handler test also explicitly sets its cache to `tmp_path`; the real A/B/A profile integration test retains its own home overrides. Before committing, check the staged baseline-to-candidate diff as well.

Install pinned tooling from requirements-dev.txt in an isolated writable environment before claiming pinned-tool checks. Verify the declared PyYAML lower bound separately from the core-constrained version. CI retains the Python 3.10–3.12 standalone matrix; local Python 3.14 evidence does not prove that matrix.

Current upstream admission: execute unmodified `hermes_cli.plugin_validate.validate_plugin_dir` from an isolated upstream checkout, including capability subprocess, scanner, no-core-override and private-import checks. Record upstream SHA. Full dependency admission additionally requires `hermes plugins validate <candidate> --install-deps` in an isolated writable environment, never the running Hermes core. Static admission is not dependency-install evidence. Capture stderr as well as the JSON: current upstream may print `dependency preparation failed` and still exit 0 with `ok: true` from static fallback; that is an incomplete dependency gate, never a PASS. Prepare the isolated upstream environment with the documented explicit `hermes pm install venv` command if needed; do not enable lazy installs or change policy to force admission.

For local pinned-tool preparation, use these commands with absolute scratch/interpreter paths supplied by the operator; every installation must pass normal safety checks:

```sh
uv venv --python "$NODE_SEARCH_BOOTSTRAP_PYTHON" "$NODE_SEARCH_VALIDATION_TMP/dev-env"
uv pip install --python "$NODE_SEARCH_VALIDATION_TMP/dev-env/bin/python" -r requirements-dev.txt
"$NODE_SEARCH_VALIDATION_TMP/dev-env/bin/ruff" check . --no-cache
```

For each available Python 3.10/3.11/3.12 interpreter, use a separate scratch venv, install requirements-dev.txt through the same approved path, and execute the standalone test command above plus compile and Ruff. An expected Hermes-only integration skip in standalone environments must be supplemented by the existing no-skip Hermes integration evidence. For the separate floor check use a compatible Python (prefer 3.10/3.11), install `PyYAML==6.0` through normal safety checks, verify its version, and run the standalone suite. A denied acquisition is BLOCKED, not permission to change installers.

From a fresh unmodified upstream checkout and its isolated runtime, with scratch HOME/HERMES_HOME and cleared NODE_SEARCH_* variables, run:

```sh
python -m hermes_cli.main plugins validate "$NODE_SEARCH_CANDIDATE" --json
python -m hermes_cli.main plugins validate "$NODE_SEARCH_CANDIDATE" --install-deps --json
```

The second command requires actual successful candidate dependency preparation under the upstream lock/core constraints; stderr, probe interpreter and preparation receipt must support that claim.

At upstream 6e9b3e3b8852f12bf965f888213470574b72803e, cmd_validate calls sync_venv without explicit=True. A core-only `pm install venv` cannot satisfy the candidate-member stamp. In the isolated scratch checkout only, explicit candidate preparation through the existing PM API resolves this without policy changes:

```sh
python -c 'import os; from pathlib import Path; import pm; from pm.plugin_inputs import Candidates; pm.sync_venv(explicit=True, plugins=Candidates([Path(os.environ["NODE_SEARCH_CANDIDATE"])]))'
```

This remains an installation requiring the normal safety checker. Afterwards run --install-deps above, require empty dependency-error stderr and an ok PM receipt, verify the selected candidate environment/probe and compare core lock versions. Never apply this preparation to the running Hermes installation.

## Deterministic quality

Canonical external dependency: builder-assurance skill version 1.1.0. Set `BUILDER_ASSURANCE_SKILL` to its absolute skill directory; the schema is vendored locally. Another machine must supply that version or explicitly report the missing dependency.

```sh
: "${BUILDER_ASSURANCE_SKILL:?Set to builder-assurance 1.1.0 skill directory}"
python "$BUILDER_ASSURANCE_SKILL/scripts/validate_quality_policy.py" .agents/quality.yaml
python "$BUILDER_ASSURANCE_SKILL/scripts/quality_report.py" --repo . --base 448d827ef4bdc32efe031c20bf3c315ffc91b351 --scope all --level top --config .agents/quality.yaml --format json > outputs/quality.json
```

Original immutable baseline: 448d827ef4bdc32efe031c20bf3c315ffc91b351. TOP covers profile boundaries and cache integrity. Independent review is required for isolation/cache changes and this new policy. No approved exceptions. Outstanding installation, lint or review gates prevent acceptance even when quality metrics pass.
