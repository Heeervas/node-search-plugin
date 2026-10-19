# Local verification

Baseline 448d827ef4bdc32efe031c20bf3c315ffc91b351; plugin 0.3.1. Acceptance is BLOCKED, not catalogue-ready.

- Baseline regressions: four intended failures (cross-root cached heading, deleted source backlink, deleted target resolution, import-time scoped lookup); outputs/regressions-before.txt.
- Final command from .agents/validation.md: 38 passed in 0.31s on Python 3.14.7 with installed PyYAML 6.0.3. Compile and git diff --check passed.
- Tests use synthetic temporary Markdown only. They cover root traversal, symlink file/directory escapes, actual Hermes secret-scope/home switching A/B/A, disk and memory reuse, deletion, narrowed scope, compact/full results, queries and graph semantics.
- Current upstream unmodified validate_plugin_dir at 2e83e2a935ee04f606aab58e498d34ca58d84c07: exit 0, all checks pass, scanner safe, no warnings, no core overrides, real isolated register() capability probe matches declarations, host-ready. outputs/admission-upstream.json. Reused sparse checkout; did not change installed core. This is not --install-deps evidence.
- Tool schema/name unchanged; only entrypoint docstring version changed. Consumers of removed DEFAULT_ROOT/DEFAULT_CACHE were searched: none in repository. Runtime already used dynamic default functions.
- Attempted isolated pinned pytest/ruff/PyYAML/package installation denied by unattended safety policy because OSV/deps.dev/ecosyste.ms checks timed out. No approval bypass, retry through another installer, global change, or substitute fabricated installation evidence. Ruff absent. Python 3.10–3.12 and PyYAML 6.0 floor remain untested; full core-constrained dependency installation remains untested.
- TOP quality report is QUALITY_FAIL: preexisting strong module/build_index metrics worsen with integrity guards; no approved exception. Baseline policy valid and measurement path exercised. Independent review outstanding; no nested delegations due constrained shared memory and unavailable verified reviewer headroom. Parent must resolve quality and review, not treat behavioural green as acceptance.
- No push, tag, release, gateway restart, profile edits, paid call or private vault indexing.
