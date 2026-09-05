# Adaptive Task Orchestrator write-DAG fixture

This fixture creates a self-contained Git repository for validating a real write-producing orchestration graph without treating the project root as a repository. Each run is immutable by name: materialization refuses to overwrite an existing run or baseline receipt.

Materialization is published atomically for cooperating local creators. A call builds and verifies a unique sibling staging directory while holding an exclusive per-run lock, promotes the staging directory only after its invariants pass, and then publishes the receipt. Caught failures remove invocation-owned staging and lock artifacts; a caught receipt-publication failure also rolls back only the final run promoted by that invocation. Pre-existing runs and receipts are never deleted. Process-crash recovery and stale-lock reclamation remain out of scope.

`runs_root` must resolve outside `template_root`; equal or descendant destinations are rejected before directory creation or copying, preventing recursive self-copy. The standard-library tooling suite discovers 63 tests on local Python 3.10 and 3.11: 60 passed and 3 real-symlink tests skipped on each runtime. The configured CI matrix adds `ubuntu-latest` and `windows-latest` for both runtimes; those GitHub Actions cells remain unobserved until an authorized push.

The template begins with a legacy `User.name` contract. A v0.2 validation run adds `displayName` while preserving compatibility, regenerates the shared field artifact once, and updates the server and client consumers in separate write scopes.

## Commands

```powershell
py -3 -B -m unittest discover -s fixtures/adaptive-task-orchestrator-write-dag/tests -v
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/materialize.py --run-id <unique-run-id>
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py --context-root docs/context/adaptive-task-orchestrator-v0.2
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py --context-root docs/context/adaptive-task-orchestrator-v0.3
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/verify_integrity.py --context-root docs/context/adaptive-task-orchestrator-v0.2
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/verify_integrity.py --context-root docs/context/adaptive-task-orchestrator-v0.3

py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/event_log.py record --output <worker-owned.jsonl> --task-id <task-id> --task-revision 1 --span-id <span-id> --event started
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/event_log.py record --output <worker-owned.jsonl> --task-id <task-id> --task-revision 1 --span-id <span-id> --event finished
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/event_log.py summarize --require-overlap --output <summary.json> <worker-a.jsonl> <worker-b.jsonl>
```

`validate_evidence.py` validates selected TaskContract, immutable-revision, route, and receipt records and emits stable machine-readable findings. `verify_integrity.py` separately treats each self-excluding manifest as the trust input, checks its canonical grammar, exact regular-file inventory, and SHA-256 bytes, and emits deterministic LF-terminated JSON Lines bytes. It exits `0` for no findings, `1` for findings, and `2` for command-line usage errors. Both validators are read-only; neither proves signatures, provenance, trusted time, or authenticity, and integrity verification assumes a quiescent package rather than a concurrent-adversary sandbox. The local Windows runs could not execute three separately reported real `os.symlink` tests because the host lacked permission; a historical intermediate NTFS-junction probe passed, while Linux and GitHub Actions execution remain pending.

To collect fresh integrity mutation observations, run `python -B tests/collect_integrity_evidence.py` from this fixture directory. This opt-in test runner creates automatically cleaned temporary packages; it is not a production read-only verifier. It emits JSON on stdout and test logs on stderr, including complete expected/actual findings, two-run output hashes, native CLI checks where applicable, and explicit per-test skips. See [ADR-0010](../../docs/decisions/0010-correct-v04-count-and-canonical-output-evidence.md) for corrections to earlier candidate claims.

`validate_evidence.py` intentionally does not validate arbitrary domain JSON, OpenAPI semantics, runtime model registries, or signatures/authenticity. `event_log.py` requires a separate stream per task revision; its local timestamps can establish interval overlap on one host, not scheduler performance or cross-host clock correctness.

Run directories contain nested `.git` metadata by design. Git commands must target
the exact run directory and must never target the repository root.
