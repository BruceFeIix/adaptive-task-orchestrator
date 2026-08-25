# Adaptive Task Orchestrator v0.2 — write-producing DAG validation

This directory records the first real local write-producing multi-agent DAG validation of the repo-local `adaptive-task-orchestrator`. Root integration is complete; final acceptance is determined by `receipts/T8-independent-final-review-r6.json` and `evidence/final-validation-receipt.json`. The package is incomplete until those files and `integrity.sha256` exist. T8 revisions 1 and 2 were cancelled while the materializer tests' ephemeral temp-write boundary was propagated; revision 3 returned `REVISE`; revision 4 was cancelled before dispatch with its incomplete T7 dependency; T9 repaired those findings; revision 5 was cancelled before acceptance when its preservation wording omitted ADR-0004; revision 6 is the current final review.

## What was exercised

The named run at `fixtures/adaptive-task-orchestrator-write-dag/runs/20260824-v0.2.0/` started from a nested Git baseline and one deliberate user-owned dirty edit. A schema writer migrated `name` toward canonical `displayName`, an independent reviewer gated the shared contract, a single codegen owner regenerated metadata, and two disjoint consumer writers ran concurrently before root integration.

The deterministic join passed:

- materializer and isolation tests: 5/5;
- named-run compatibility and regression tests: 13/13;
- original `user-notes.md` dirty bytes preserved at SHA-256 `4AAD6DFEF0AF92E1421866476F5A20BBA1C2D45CCFE4AA81DB2D1D5A8E4E0AD2`;
- exact nested Git state reconciled to seven accepted paths;
- no network access, dependency installation, global Skill installation, external runtime, or destructive Git operation.

Fault evidence covers overlapping-writer rejection before dispatch, `NEEDS_CONTEXT` plus revised-contract recovery, stale route/receipt invalidation, a `BLOCKED` codegen contradiction plus bounded repair, and a requested/unattested route that was never presented as observed.

## Read order

1. `docs/specs/adaptive-task-orchestrator-v0.2-write-dag.md` — approved scope and success criteria.
2. `docs/decisions/0002-record-v0.1-bundle-fingerprint-errata.md` — historical fingerprint caveat.
3. `docs/decisions/0003-close-transitive-read-and-dirty-state-evidence-gaps.md` — evidence-driven live-policy amendment.
4. `contracts/` and `routes/` — authoritative task revisions and requested/observed lifecycle.
5. `receipts/` — worker evidence plus root dispositions; use only the latest non-stale accepted revision for current claims.
6. `evidence/historical-contract-fidelity.json` — exact revisioned contracts and explicitly unavailable early bodies.
7. `evidence/T7-integration-summary.json` — deterministic root join summary.
8. `receipts/T8-independent-final-review-r6.json` and `evidence/final-validation-receipt.json` — final assurance and bounded conclusion.
9. `integrity.sha256` — hashes for the completed v0.2 package; it excludes itself.

## Reproduce the core checks

From `F:\Projects\CodexProjects`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
py -3 -m unittest discover -s fixtures/adaptive-task-orchestrator-write-dag/tests -v
```

From the named-run directory:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
py -3 -m unittest discover -s tests -v
git status --short
Get-FileHash -Algorithm SHA256 user-notes.md
```

Every JSON file under `contracts/`, `routes/`, `receipts/`, and `evidence/` must parse. The conflict and parallel-preflight evidence can be reproduced by intersecting the respective `write_scope` and `resource_locks` arrays.

## v0.1 preservation and fingerprint caveat

The v0.1 archive remains 25/25 and its immutable first-implementation snapshot remains 7/7. Do not edit the v0.1 snapshot, verbatim reports, or historical manifests.

The historical bundle fingerprint `8563586856A87E5309CE35459ACAFBC785C413833B3A8494ACA6EA50E1BDFE8D` corresponds to `OrdinalIgnoreCase`, which yields the manifest-listed order for this inventory. The true case-sensitive `Ordinal` fingerprint is `11B134AD4C9611F3845BCB1655AA208F361C020AD03D19C06E66E8FC6E295E42`. All seven per-file hashes are unaffected.

The live Skill now intentionally matches six of the seven immutable v0.1 snapshot files. Only `references/task-contract.md` differs. ADR-0003 closes transitive acceptance-command reads and requires ownership-aware evidence in a shared dirty workspace; ADR-0004 requires immutable revisioned contract evidence before dispatch. The immutable snapshot remains the v0.1 baseline.

Early v0.2 revisions whose exact contract bodies were overwritten are not silently reconstructed. Their routes and receipts remain lifecycle evidence, but exact historical scopes are declared unavailable in `evidence/historical-contract-fidelity.json`. Current and future revisions have immutable copies under `contracts/revisions/` before dispatch. Therefore the package supports exact replay for the listed preserved revisions and only bounded lifecycle claims for the unavailable ones.

## Limits

This evidence validates one bounded local nested-Git software-development fixture. It does not validate a persistent scheduler, cross-machine coordination, production workloads, an external orchestration runtime, every routing tier, or every domain policy. The exact root model and effort were inherited but not runtime-attested, so the T7 route records execution as observed while leaving the route itself `inherited-unattested`. No third-party OpenAPI validator was installed.
