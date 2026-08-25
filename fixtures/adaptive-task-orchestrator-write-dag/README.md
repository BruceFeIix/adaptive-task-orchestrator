# Adaptive Task Orchestrator write-DAG fixture

This fixture creates a self-contained Git repository for validating a real write-producing orchestration graph without treating the project root as a repository. Each run is immutable by name: materialization refuses to overwrite an existing run or baseline receipt.

Materialization is published atomically for cooperating local creators. A call builds and verifies a unique sibling staging directory while holding an exclusive per-run lock, promotes the staging directory only after its invariants pass, and then publishes the receipt. Caught failures remove invocation-owned staging and lock artifacts; a caught receipt-publication failure also rolls back only the final run promoted by that invocation. Pre-existing runs and receipts are never deleted. Process-crash recovery and stale-lock reclamation remain out of scope.

`runs_root` must resolve outside `template_root`; equal or descendant destinations are rejected before directory creation or copying, preventing recursive self-copy. The tooling is verified with the local Python 3.10 and 3.11 runtimes and uses only the standard library.

The template begins with a legacy `User.name` contract. A v0.2 validation run adds `displayName` while preserving compatibility, regenerates the shared field artifact once, and updates the server and client consumers in separate write scopes.

## Commands

```powershell
py -3 -B -m unittest discover -s fixtures/adaptive-task-orchestrator-write-dag/tests -v
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/materialize.py --run-id <unique-run-id>
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py --context-root docs/context/adaptive-task-orchestrator-v0.3

py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/event_log.py record --output <worker-owned.jsonl> --task-id <task-id> --task-revision 1 --span-id <span-id> --event started
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/event_log.py record --output <worker-owned.jsonl> --task-id <task-id> --task-revision 1 --span-id <span-id> --event finished
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/event_log.py summarize --require-overlap --output <summary.json> <worker-a.jsonl> <worker-b.jsonl>
```

`validate_evidence.py` validates selected TaskContract, immutable-revision, route, and receipt records and emits stable machine-readable findings. It intentionally does not validate arbitrary domain JSON, OpenAPI semantics, runtime model registries, or signatures/authenticity. `event_log.py` requires a separate stream per task revision; its local timestamps can establish interval overlap on one host, not scheduler performance or cross-host clock correctness.

Run directories contain nested `.git` metadata by design. Git commands must target
the exact run directory and must never target the repository root.
