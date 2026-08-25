# ADR-0006: Validate evidence and record worker-owned event streams

## Status

Accepted

## Date

2026-08-25

## Context

v0.2 used deterministic root scripts to validate TaskContracts, routes, receipts, and revision identities, but the rules were not a reusable repository tool. It also proved that two consumers were eligible for parallel dispatch without persisting timestamps capable of establishing actual interval overlap.

## Decision

Add two dependency-free CLIs:

1. A fail-closed evidence validator with stable diagnostic codes for executable TaskContracts, preflight records, child routes, root execution records, receipts, dependency identities, and immutable revision equality.
2. An append-only JSONL event tool where each task revision owns one stream. Root combines the disjoint streams and computes interval overlap after the wave.

Unknown record kinds, enums, dependencies, transitions, or revision mismatches are errors. Parallel workers never append to one shared trace file.

## Alternatives Considered

### JSON Schema with a third-party implementation

Deferred because dependency installation is outside the approved scope. The explicit Python validator can later emit or consume a formal schema without changing the record interfaces.

### One shared concurrent JSONL file

Rejected because it introduces the exact shared write conflict that the orchestration policy avoids.

### Infer overlap from route and receipt ordering

Rejected because ordering proves neither start/end timestamps nor temporal intersection.

## Consequences

- Evidence checks become repeatable through one CLI rather than ad hoc shell scripts.
- Actual overlap can be proven for instrumented workers without a persistent scheduler.
- Event evidence remains a bounded observation, not a performance guarantee.
- Third-party OpenAPI semantics and cross-machine clock analysis remain future work.
