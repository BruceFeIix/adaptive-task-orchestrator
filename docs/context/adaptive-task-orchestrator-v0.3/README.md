# Adaptive Task Orchestrator v0.3 — hardening iteration

This package records the post-v0.2 hardening iteration: atomic fixture publication and cleanup, reusable TaskContract/Route/Receipt validation, and worker-owned timestamped event streams with a real two-agent overlap probe.

The completed package includes the accepted revision-3 independent review, the final validation receipt, and a self-excluding `integrity.sha256`. v0.1 and v0.2 remain immutable inputs and are not part of this package's write scope.

## Read order

1. `docs/specs/adaptive-task-orchestrator-v0.3-hardening.md`
2. `docs/decisions/0005-atomically-publish-materialized-runs.md`
3. `docs/decisions/0006-validate-evidence-and-record-worker-owned-events.md`
4. `docs/decisions/0007-separate-root-verification-from-evidence-synthesis.md`
5. `contracts/`, `routes/`, and `receipts/`
6. `evidence/`
7. `integrity.sha256`

## Claim boundary

This iteration remains local, standard-library-only, and single-host. Timestamped intervals can prove overlap for the instrumented probe wave, but they do not establish scheduler throughput, cross-host clock correctness, or production readiness.

The final accepted implementation is verified on the local Python 3.10.0 and 3.11.9 runtimes. It closes caught lock-initialization cleanup/retry, rejects recursive materialization topology, validates complete selected evidence shapes and receipt consistency, and preserves byte-identical overlap output across both runtimes. Process-crash/stale-lock recovery, signatures/authenticity, third-party OpenAPI semantics, and a second domain topology remain deferred.
