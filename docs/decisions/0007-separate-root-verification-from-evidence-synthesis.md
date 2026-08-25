# ADR-0007: Separate root verification from evidence synthesis provenance

## Status

Accepted

## Date

2026-08-25

## Context

The v0.3 revision-1 root-integration TaskContract described a read-only verification node whose only permitted runtime writes were automatically cleaned test temporary directories. Its receipt also listed a fixture README update and root-owned overlap/integration evidence files under `artifacts_or_changes`. Those project writes were performed by the root synthesis step before or after the verification commands, not by a delegated read-only worker, but the receipt did not distinguish the provenance clearly.

Independent review recorded this as Advisory A1. The ambiguity does not change the file identities, test results, or permission boundary, but future consumers should not have to infer which logical step produced a listed artifact.

## Decision

- Preserve the accepted revision-1 contract and receipt unchanged as historical evidence.
- Record this additive provenance erratum rather than rewriting the receipt.
- Model the next root-integration revision as a root-owned write task whose declared outputs include its route disposition, integration summary, and receipt.
- Separate verification side effects from root synthesis outputs in the receipt. Automatically cleaned test temporary directories are verification side effects; Markdown, JSON evidence, routes, receipts, task ledgers, and manifests are root synthesis outputs only when explicitly declared.
- Keep implementation workers unable to write shared synthesis files.

## Consequences

- T5 revision 1 remains auditable but must be read with this ADR.
- T5 revision 2 will make its evidence publication scope explicit and will not attribute root synthesis files to an otherwise read-only worker.
- The root retains serial ownership of shared README, context, task-ledger, final-receipt, and integrity-manifest writes.
- This clarification does not broaden dependency, network, Git, or external-runtime permissions.

## Alternatives Considered

### Rewrite the revision-1 receipt

Rejected because an accepted receipt is historical evidence and should not be silently normalized after independent review.

### Omit synthesis artifacts from future receipts

Rejected because that would hide real project writes rather than clarify their owner and phase.
