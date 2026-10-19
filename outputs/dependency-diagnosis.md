# Dependency admission and runtime diagnosis

Supersedes the dependency-admission and matrix blockers in preparation.md. Started from clean 89383fed67e1b55087e7693236a7cc45249c5ad2. Candidate source/manifest/tests and policy unchanged; all five verification.md hashes still match. Upstream remains unmodified 6e9b3e3b8852f12bf965f888213470574b72803e. Only evidence/state/validation docs change here. Whole release remains blocked only by PyYAML 6.0 floor execution.

## Precise failure source

`hermes_cli/plugins_cmd_catalog.py:790` calls `pm.sync_venv(plugins=Candidates([Path(path)]))` without `explicit=True`. In `pm/install.py:849–850`, a non-current stamp plus non-explicit request and disabled lazy installs is refused. The explicit CLI `pm install venv` does a core-only sync (`pm/cli.py:583`), with no candidate member. Therefore its success cannot satisfy the different candidate dependency stamp. This was not a resolver conflict, interpreter mismatch or broken installation.

Read-only input comparison showed:

- Core-only recorded and recomputed stamp: `892906d474e2707793ee3df97f71b453d2b185bf36f63977b20956bf1344db97`.
- Candidate members: only `/opt/data/plugins/node-search`.
- Candidate stamp: `69009fcded3b86d82c37513522c6d21d932af9a26e7fca432e6037e055368134`.
- Running interpreter initially was the existing Hermes interpreter, but validator and PM imports resolved inside the isolated upstream checkout; selected environments/facts were under scratch. No running-core environment was changed.

Upstream also catches dependency preparation errors and falls back to static validation without changing exit status. That is a concrete fail-open admission-reporting defect: `--install-deps` may exit 0 despite dependency failure. No upstream source was patched. A separate upstream fix could mark this explicit user-requested install as explicit and propagate preparation failure; this task does not authorize that patch or publication.

## Successful supported correction

The existing explicit PM sync API supports candidate inputs and keeps policy intact. The canonical reusable command is now in .agents/validation.md. Actual command, executed from `/opt/data/profiles/builder/cache/scratch/node-search-upstream-current`, was:

```sh
env HOME=/opt/data/profiles/builder/cache/scratch/node-search-install-user HERMES_HOME=/opt/data/profiles/builder/cache/scratch/node-search-install-home PYTHONDONTWRITEBYTECODE=1 python -c 'from pathlib import Path; import pm; from pm.plugin_inputs import Candidates; pm.sync_venv(explicit=True, plugins=Candidates([Path("/opt/data/plugins/node-search")]))'
```

The normal tool/safety path allowed this scoped explicit installation. Result: resolving and installing Python dependencies both succeeded, exit 0. No raw pip/uv mutation of Hermes dependency environments, policy/config edits or lazy-install enabling occurred. New scratch generation: `623f497de69f4e9182114cfc512df428`. Receipt `pm_20261019T153243Z-sync-395367-157f25ec7b8f46f0abdb2f229385efea.json` records outcome ok, no refusal, venv_rebuild ok true.

Then the original CLI reproduction, with the same scratch HOME/HERMES_HOME and cleared NODE_SEARCH_ROOT/ALLOWED_ROOTS/CACHE, succeeded:

`python -m hermes_cli.main plugins validate /opt/data/plugins/node-search --install-deps --json`

Results: exit 0; empty stderr; ok true; all checks pass; isolated capability probe succeeds; security scanner safe; no warnings; host-ready. A second captured run preserved the JSON and empty stderr in scratch. PM receipt records outcome ok, no refusal, already in sync. This is actual prepared-candidate admission, not fallback.

Selected probe interpreter:
`/opt/data/profiles/builder/cache/scratch/node-search-install-home/installs/6e8b559570104299/environments/623f497de69f4e9182114cfc512df428/venv/bin/python`.
Direct isolated interpreter inspection reports Python 3.14.7 and PyYAML 6.0.3. Its selected stamp equals the candidate stamp above. Comparing name/version maps in the original core uv.lock and selected candidate resolved lock: 326 core packages, 327 candidate packages, zero changed/missing core versions; PyYAML remains 6.0.3. The extra package is the candidate workspace member. Core constraints and pins were preserved.

Private-local evidence (not copied wholesale into public reports):
- Scratch `node-search-dependency-admission.json` and `node-search-dependency-admission.stderr`.
- Scratch install-home `logs/update_receipts/` successful explicit-build and validation receipts.
- Scratch install-home `installs/6e8b559570104299/facts.json` and selected generation workspace/uv.lock.

## Existing-runtime discovery and matrix

No denied interpreter acquisition was retried. Bounded read-only inspection of the active standard uv cache found 17 interpreter metadata records. One referenced Python 3.12 in the standard default uv managed-install directory `/opt/data/.local/share/uv/python`, rather than the active profile's nonexistent managed-install directory. Inspecting only that standard directory and `uv python list --only-installed --offline` with `UV_PYTHON_INSTALL_DIR` set to it revealed existing Python 3.10.20, 3.11.15 and 3.12.13. No download, private scan or runtime mutation occurred. Cached archives contained only Python 3.14 executables; PyYAML cached distributions inspected were all 6.0.3.

Separate scratch venvs `node-search-py310-env`, `node-search-py311-env`, `node-search-py312-env` were created from those exact existing interpreters. Each `uv pip install --python <env>/bin/python -r requirements-dev.txt` passed normal safety checks and installed pinned pytest 8.4.2, Ruff 0.14.1 and PyYAML 6.0.3. Canonical standalone tests with scratch HERMES_HOME/basetemp, compilation with scratch pycache, and Ruff --no-cache all passed:

| Runtime | Suite | Compile | Ruff |
|---|---|---|---|
| Python 3.10.20 | 37 passed, 1 skipped, 0.49s | PASS | PASS |
| Python 3.11.15 | 37 passed, 1 skipped, 0.45s | PASS | PASS |
| Python 3.12.13 | 37 passed, 1 skipped, 0.49s | PASS | PASS |

The single expected skip is Hermes secret-scope integration absent in standalone environments. The independently accepted 38/no-skip actual profile integration remains the integration evidence. No code changes invalidate it.

The command guard rejected an attempted dynamic shell loop for the matrix as unanalyzable before execution. The same visible checks were then submitted as explicit literal commands and approved normally; no hidden executable loop was used. An inline combined lock-comparison/subprocess diagnostic was rejected; separate read-only comparison and literal interpreter commands were approved and produced the results above. No guard was disabled or ignored.

## Only remaining operator action

PyYAML 6.0 installation was not retried and is not available in the inspected standard cache. The denied acquisition still needs complete threat-intelligence service access or interactive approval through the normal guard. No new runtime needs to be supplied. In an attended approved session, use the existing isolated Python 3.11 environment:

```sh
uv pip install --python /opt/data/profiles/builder/cache/scratch/node-search-py311-env/bin/python 'PyYAML==6.0'
```

If permitted and successful, verify version 6.0 then execute the canonical standalone suite with that interpreter and a separate scratch test home/basetemp. This changes only the disposable 3.11 check environment, not core or the plugin declaration. If the normal guard denies it again, restore OSV/deps.dev/ecosyste.ms access or resolve the decision interactively; do not use another installer, change package tokens or weaken acceptance. This worker did not execute that previously denied command again.

After floor acceptance, coordinator refreshes the final catalogue pin, pushes the exact candidate and opens an update to the existing catalogue entry. Existing proposal still pins code-equivalent 16e0e46f3a19edbf3473bbeb572bce5af9beda87; documentation-only continuation is not yet reflected in that pin. No publication or PR action is performed here.
