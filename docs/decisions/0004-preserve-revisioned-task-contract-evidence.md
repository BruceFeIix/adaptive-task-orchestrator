# ADR-0004: Preserve revisioned TaskContracts before dispatch

- Status: Accepted
- Date: 2026-08-25
- Scope: repo-local `adaptive-task-orchestrator` evidence policy

## Context

The v0.2 DAG correctly preserved stale routes and receipts, but several early tasks reused a mutable, unversioned contract filename. Later scope repairs overwrote the prior contract body. The independent T8 revision 3 review found that a future reviewer could no longer compare the exact historical `read_scope`, `write_scope`, permissions, acceptance checks, and evidence requirements against the corresponding stale receipt.

Receipts describing an earlier contract are useful secondary evidence, but they cannot recreate omitted permission boundaries. Reconstructing those boundaries from memory would make the audit less trustworthy than explicitly admitting the evidence gap.

## Decision

Before every future dispatch, save the exact serialized TaskContract under an immutable `task_id + task_revision` identity. An optional mutable current pointer may coexist for convenience, but it cannot replace or overwrite the revisioned artifact.

For v0.2 revisions whose original contract body is no longer available, record that fact in a historical-fidelity matrix. Preserve their route, receipt, and stale disposition, but do not invent scopes or permissions. Narrow final claims accordingly.

## Consequences

- Current and future task revisions can be validated by exact three-way identity across contract, route, and receipt.
- Evidence directories contain more small JSON files.
- Early v0.2 scope-repair demonstrations remain valid as lifecycle evidence, but their original contract bodies are explicitly partial-history caveats rather than fully replayable authorization records.
- The immutable v0.1 snapshot and manifests remain unchanged; only the live TaskContract reference receives this additive rule.
