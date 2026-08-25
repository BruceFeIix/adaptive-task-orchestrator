# ADR-0003: Close transitive-read and dirty-state evidence gaps

- Status: Accepted
- Date: 2026-08-25
- Scope: repo-local `adaptive-task-orchestrator` TaskContract policy

## Context

The v0.2 write-producing DAG reproduced two policy-adjacent failure modes while preserving fail-closed execution:

1. T2 revisions 1 and 2 and T3 revisions 1 and 3 omitted resources that required acceptance commands or reviews loaded transitively. The root rejected or invalidated those receipts and repaired the literal scopes. In particular, T3 revision 1 ran a Python test whose imports were absent from `read_scope`, and T3 revision 3 was asked to verify generator compatibility without direct permission to read `tools/generate.py`.
2. T2 revision 4 correctly changed only the OpenAPI contract, but its fixture-global status check also saw `generated/user_fields.py`, an accepted residual from the earlier T4 blocked attempt. Global dirty state described the workspace but could not independently attribute the writer.

The existing policy already required explicit scopes, rejection of undeclared access, and a baseline for dirty resources. It did not explicitly state that acceptance commands confer no implicit transitive read authority, nor that fixture-global status is insufficient as sole authorship evidence. The repeated scope revisions and independent T3 caveat show that making these implications explicit reduces reconstruction cost and prevents permissive interpretations.

## Decision

Add a narrow `Scope and Baseline Closure` section to the live TaskContract reference:

- every project resource loaded transitively by an acceptance command must be declared, or the command must be isolated from undeclared project resources;
- undeclared transitive access requires a revised contract and stale prior evidence;
- shared dirty workspaces require owned-artifact pre-write identities plus write-operation, post-identity, scoped-diff, and accepted ownership evidence;
- global status is an inventory, not sole proof of writer scope compliance.

No routing thresholds, permissions, worker statuses, global installation behavior, or orchestration runtime are changed.

## Consequences

- Contract authors must account for test imports, configuration, fixtures, plugins, generated metadata, and manifests before dispatch.
- Receipt review remains fail closed instead of treating an authorized command as blanket file authorization.
- Writer receipts in dirty workspaces become slightly more verbose but are attributable without requiring a globally clean tree.
- Existing v0.1 snapshots and historical manifests remain unchanged. The live-policy delta and its evidence belong only to the v0.2 context.

## Evidence

- `receipts/T2-schema-writer-r1.json` and `receipts/T2-schema-writer-r2.json`: stale scope revisions.
- `receipts/T3-schema-review-r1.json`: transitive Python imports omitted from scope.
- `receipts/T3-schema-review-r3.json`: direct generator source omitted from a compatibility review.
- `receipts/T2-schema-writer-r4.json`: accepted artifact with a shared-dirty ownership caveat.
- `receipts/T4-codegen-owner-r1.json`: independent ownership evidence for the residual generated artifact.
- `receipts/T4-codegen-owner-r2.json`, `receipts/T5-server-consumer-r1.json`, and `receipts/T6-client-consumer-r1.json`: node-local pre/post hashes used successfully after the finding.

All receipt paths above are relative to `docs/context/adaptive-task-orchestrator-v0.2/`.
