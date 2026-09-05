# ADR-0011: Validate runtime-specific model routes

## Status

Accepted design under the user-approved v0.5 direction, 2026-09-06.
Independent design repair review V5-D1@2, checker review V5-I1@1 and Skill
forward-test V5-P1@1 accepted with caveats. The v0.5 local candidate retains final
integration evidence and unresolved platform/attestation gaps. This is not a
cross-platform release or effective-model claim.

## Decision

Keep capability aliases and TaskContract/RouteDecision separation. Put exact model
IDs, project capability assignments, effort/surface support and defaults in one
versioned repository-local registry. Intersect it with a per-run host/tool snapshot.
Use an additive offline `runtime-routes-v1` checker for semantic consistency.

Distinguish a tool declaring a candidate, accepting a dispatch, and reporting the
actual effective model/effort. Source records need matching run, snapshot, worker,
and registry identities. A JSON validator can check those references but cannot
authenticate arbitrary input or force the host to disclose fields it lacks.

Normalize concurrent child capacity from the host's counting convention. Validate
fork/override/context combinations and monotonic fallbacks. Root-only degradation
remains limited to low-risk, directly checked work. Keep review freshness and
model-family diversity separate.

## Why this scope

The existing Skill policy is extensible but its Python evidence checker does not
validate exact model/effort combinations. Replacing every Sol string with Astra
would collapse useful cost/quality roles and rewrite historical provenance. A new
API client or scheduler would duplicate Codex execution and expand permissions.
The offline checker supplies a bounded deterministic oracle without either change.

## Consequences

Legacy validation and historical packages remain unchanged. New v0.5 high-risk
completed records require effective-route evidence that some hosts may not expose;
such records fail the acceptance gate honestly. Planned routes remain checkable.
The registry is project policy with a documented source and evaluation status, not
a guarantee of model performance or account availability. No automatic network
refresh or global configuration mutation is introduced.

See the [v0.5 specification](../specs/adaptive-task-orchestrator-v0.5-runtime-routing.md).
