# Architecture decisions

Architecture Decision Records capture why the project is designed and validated the way it is. Accepted historical ADRs are not rewritten when the design evolves; a later ADR records the change.

| ADR | Decision |
|---|---|
| [0001](0001-codex-native-repo-local-orchestrator.md) | Keep orchestration Codex-native and repository-local |
| [0002](0002-record-v0.1-bundle-fingerprint-errata.md) | Record the v0.1 fingerprint erratum without rewriting history |
| [0003](0003-close-transitive-read-and-dirty-state-evidence-gaps.md) | Close transitive-read and dirty-state evidence gaps |
| [0004](0004-preserve-revisioned-task-contract-evidence.md) | Preserve immutable revisioned TaskContract evidence |
| [0005](0005-atomically-publish-materialized-runs.md) | Publish materialized fixture runs atomically |
| [0006](0006-validate-evidence-and-record-worker-owned-events.md) | Validate evidence and use worker-owned event streams |
| [0007](0007-separate-root-verification-from-evidence-synthesis.md) | Separate root verification effects from evidence synthesis |
| [0008](0008-publish-a-curated-open-source-repository.md) | Publish a curated standalone open-source repository |
| [0009](0009-verify-evidence-manifests-portably.md) | Verify complete evidence inventories and hashes portably |
| [0010](0010-correct-v04-count-and-canonical-output-evidence.md) | Correct v0.4 count handling, canonical output, and evidence claims |
| [0011](0011-validate-runtime-specific-model-routes.md) | Separate registry, host capability, planned routes and effective execution evidence |
| [0012](0012-canonicalize-fault-injection-targets.md) | Match fault injection to canonical I/O paths while preserving aliased-input regression coverage |
