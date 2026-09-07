# v0.5 runtime-routing local candidate evidence

This package records local validation of a Codex-native policy update and its
opt-in standard-library checker. It is not a production scheduler, an effective
model identity certificate, or a completed cross-platform release. Historical
drafts remain evidence, not active Skill instructions.

## Read order

1. [Specification](../../specs/adaptive-task-orchestrator-v0.5-runtime-routing.md)
   and [ADR-0011](../../decisions/0011-validate-runtime-specific-model-routes.md)
   define the registry, host snapshot and declared-record consistency boundary.
2. [Design repair review](receipts/V5-D1-design-review-r2.json) supersedes the
   earlier rejected design for current acceptance purposes without rewriting it.
3. [Checker review](receipts/V5-I1-checker-review-r1.json) independently checks the
   frozen implementation and adversarial cases. [Postreview tests](evidence/postreview-checker-tests.json)
   retain the optional byte-oracle followup, mutations and validation limitation.
4. [Skill behavior review](receipts/V5-P1-policy-forward-test-r1.json) and
   [full hypothetical inputs](evidence/policy-forward-test-inputs.json) retain
   three cards and six reproducible positive/negative checks. Root reproduced
   each case twice on both local Python runtimes.
5. [Fixed-task pilot](evidence/fixed-task-pilot-results.json) records one requested
   Astra configuration and one requested Terra configuration, three tasks each,
   first-pass 3/3 each. Inputs/oracles were frozen before dispatch. No defaults
   changed and no model-ranking, cost, latency or effective-identity claim follows.
6. [Integrated local tests](evidence/final-integrated-local-tests.json) record
   110 discovered, 107 passed and three real-symlink permission skips on each of
   Windows Python 3.10.0 and 3.11.9. Earlier 80/98-test increments are not this count.
7. [Local Skill synchronization](evidence/workspace-skill-sync.json) records the
   exact inventories and nine equal SHA-256 pairs after updating the parent
   workspace copy. This is point-in-time local evidence, not a global install.
8. [Final local receipt](evidence/final-validation-receipt.json) defines the final
   local claim. The [manifest](integrity.sha256) is generated last and excludes
   itself; record later platform observations outside this sealed directory.

## Important boundaries

- A planned route may be valid without execution evidence. A high-risk accepted
  or completed route without matching effective model/effort evidence is not.
- A task-name-only native spawn response proves neither effective configuration
  nor model diversity. Independent context is not statistical independence.
- The checker does not fetch evidence references or authenticate supplied records.
  Zero findings do not mean all tasks ran, succeeded, or formed a complete run.
- Generic capability ranks/profile defaults remain provisional project policy.
- The earlier candidate runtime-reference copy is a frozen review input; the
  repository-local Skill owns current instructions and later wording clarifications.
- Skill quick_validate.py was unavailable because PyYAML was absent. Its manual
  metadata/link checks are disclosed as a fallback, not a validator pass.
- Actual four-cell GitHub Actions, Linux and real symlink execution remain pending.
  Local WSL listing was denied; no Linux result was inferred or permissions changed.

## Revalidation

From the repository root, use Python 3.10 or 3.11:

```text
python -B -m unittest discover -s fixtures/adaptive-task-orchestrator-write-dag/tests
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py --context-root docs/context/adaptive-task-orchestrator-v0.5
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_runtime_routes.py --registry .agents/skills/adaptive-task-orchestrator/references/model-registry.json --bundle docs/context/adaptive-task-orchestrator-v0.5/candidates/planned-astra-bundle.json
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/verify_integrity.py --context-root docs/context/adaptive-task-orchestrator-v0.5
```

Retain later revalidation logs outside this package. A trusted manifest detects
byte/inventory changes in a quiescent package; it is not a signature, trusted time,
or protection against hostile concurrent filesystem replacement. Preserve v0.1
fingerprint errata and all accepted v0.2/v0.3/v0.4 evidence unchanged.
