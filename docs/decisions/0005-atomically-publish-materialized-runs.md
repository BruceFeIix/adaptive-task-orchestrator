# ADR-0005: Atomically publish materialized fixture runs

## Status

Accepted

## Date

2026-08-25

## Context

The v0.2 materializer copied directly to the final run path before Git initialization, commit, dirty-state creation, and receipt serialization completed. A failure in that interval left a partial final directory, while the non-overwrite guard correctly but permanently rejected a same-ID retry.

## Decision

Build each run in a unique sibling staging directory protected by an exclusive per-run lock. Complete Git initialization, baseline commit, dirty edit, and receipt preparation in staging. Promote the staging directory to the final run path only after every invariant passes, then publish the baseline receipt with exclusive creation.

On a caught failure before promotion, remove only the exact owned staging directory and lock. On a caught receipt-publication failure after promotion, roll back only the final directory that the current invocation can prove it just promoted while retaining the exclusive lock. Never delete or replace a run or receipt that existed before the invocation acquired its lock. A process crash is outside this caught-exception guarantee and can still strand an owned artifact.

The public Python function and receipt fields remain unchanged.

## Alternatives Considered

### Continue publishing directly to the final path

Rejected because a mid-operation failure leaves an unretryable partial run.

### Delete the final path after failure

Rejected because ownership becomes ambiguous if another actor created or modified that path during the failed operation.

### Add a database or external transaction coordinator

Rejected as disproportionate and outside the local standard-library scope.

## Consequences

- Same-ID retry is safe after an owned failed attempt.
- Successful runs become visible only in a complete state.
- Per-run lock and staging names are internal implementation details and are cleaned on normal success and caught failure.
- A caught post-promotion receipt failure rolls back the invocation-owned final directory so a same-ID retry remains possible.
- A process crash can still strand a lock, staging directory, or promoted run; automatic crash recovery and stale-lock reclamation are intentionally deferred because safe ownership proof needs a separate design.
