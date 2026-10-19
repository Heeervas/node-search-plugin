# Local verification — review fixes

Baseline: 448d827ef4bdc32efe031c20bf3c315ffc91b351. Tested implementation commit: c37ea55de68e2f5a51af6291f193fcb06b5ca8f1. Plugin 0.3.1. Acceptance remains BLOCKED by supported-runtime, PyYAML-floor and fresh dependency-admission gates, not by deterministic quality or independent code review. See outputs/preparation.md for resumed gate evidence.

## Review findings

Independent review: /opt/data/profile_delegate/runs/pd_20261019_104603_bn195t/result.json. R1 fixed by setting NODE_SEARCH_CACHE in the handler test and adding scratch HERMES_HOME to the canonical suite command. Basetemp alone does not redirect plugin state. Actual A/B/A integration remains intact. R2 fixed by merging adjacent identical graph-rebuild guards: graph resolution and persistence now share one block; root/base/node-set checks remain. R3 fixed by removing transcript trailing whitespace, without changing substantive pre-fix evidence.

## Executed evidence

- Canonical suite with scratch HERMES_HOME and basetemp suffix `-r1-r2`: 38 passed in 1.67s. Python 3.14.7, pytest 9.1.1, PyYAML 6.0.3, packaging 26.0. No skipped profile integration test. Synthetic Markdown only.
- Compile command in .agents/validation.md passed.
- `git diff --cached --check 448d827ef4bdc32efe031c20bf3c315ffc91b351` passed before implementation commit; `git diff --check 448d827ef4bdc32efe031c20bf3c315ffc91b351 HEAD` passed afterward.
- Quality policy validates. Regenerated TOP report: QUALITY_PASS, no exceptions or adapter gaps. Module logical lines 1149 → 1149; build_index complexity 17 → 17. Unchanged strong debt remains reported. outputs/quality.json includes its genuine c37ea55-plus-all snapshot identity; it is not relabeled as a later documentation commit.
- Unmodified upstream validate_plugin_dir rerun from sparse checkout 2e83e2a935ee04f606aab58e498d34ca58d84c07: exit 0, all checks pass, safe scanner, no warnings, matching isolated registration and no-core-override, host-ready. outputs/admission-upstream.json. Relevant upstream hermes_cli/agent/tools/pm/gateway/hermes_constants.py have no local diff. This is not --install-deps evidence. Reviewer independently checked later upstream commits did not change relevant admission sources.
- Baseline red transcript retains four intended failures. Existing suite covers cross-root cache identity, deletion, disk/memory reuse, narrowed scope, traversal/symlinks and compact/full search behaviour.

Source SHA-256 identities for binding unchanged code across subsequent evidence/documentation commits:

```text
3cf3f900643e591be3f1a2c7d252ca84aac7c2971fda54d113c0d17cb9f2cd3a  node_index.py
7788e0184dc375193bc43a41b9de59e0b9a04ef09fc2f55023f0b95ef97a6a45  __init__.py
f8108aa551527e92a5f883024f136508b2ab1eaed4ea2fb5dfd3d5a87e3835dc  plugin.yaml
bfc8965c2a91c80a5ecdb9646e791119863bdaa8818b508a5869005519e1a2b4  test_node_search.py
25fb3b9c8dc38726a9081a258ef57a5a47341c348f0e9fb60b99e0dc60497812  test_catalogue_regressions.py
```

## Required incomplete gates

Earlier denied command (not retried): `uv pip install --python /opt/data/profiles/builder/cache/scratch/node-search-check-env/bin/python 'pytest==8.4.2' 'ruff==0.14.1' 'PyYAML==6.0' 'packaging==25.0'`. OSV/deps.dev/ecosyste.ms threat-intelligence lookups timed out; unattended safety policy denied execution. `command -v ruff` now exits 1. Pinned dev-tool installation, `ruff check .`, Python 3.10–3.12 execution, PyYAML 6.0 floor execution and fresh isolated `hermes plugins validate <candidate> --install-deps` under core constraints remain incomplete. No retry or safety-policy workaround was attempted.

Independent re-review pd_20261019_110105_zas2bl accepted R1/R2/R3 at 4109156b0e6bb305c4b3cb0a73fd29dc99d681fe; no further code changes are required. The incomplete-gates paragraph above records the earlier attempt, not current lint readiness; outputs/preparation.md supersedes it. No nested review/delegation. No push, publication, profile policy/config change, paid calls or private scan. Reviewer-created synthetic cache outside scratch was not touched. Later changes limited to evidence/STATE do not change these tested code bytes; proposed catalogue pin is generated after the candidate documentation commit.
