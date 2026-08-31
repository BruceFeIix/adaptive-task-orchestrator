# Implementation Plan: v0.4 portable evidence integrity

## Status

Approved by the user on 2026-08-31. Implementation is in progress under the
accompanying specification and accepted ADR-0009.

## Overview

v0.4 adds one cross-platform, read-only Python CLI that validates the exact complete
file inventory and SHA-256 bytes of a versioned evidence package against its trusted
self-excluding manifest. Existing structural validation and all accepted v0.2/v0.3
artifacts remain unchanged.

## Architecture Decisions

- Use a separate `verify_integrity.py` tool instead of changing
  `validate_evidence.py` default behavior.
- Validate manifest syntax and path containment before opening listed files.
- Compare both directions: every manifest entry must resolve to one regular file,
  and every package regular file except the manifest must appear exactly once.
- Use the approved ASCII grammar, ASCII-byte ordinal ordering, and ASCII-lowercase
  collision key so Windows and Linux apply the same canonical rules.
- Require a quiescent package and reject observed symlinks without claiming the
  verifier is a concurrent-adversary sandbox.
- Treat the manifest as trusted input for integrity only; preserve the authenticity
  caveat.
- Keep implementation and tests dependency-free in the Windows/Linux by Python
  3.10/3.11 matrix.

## Dependency Graph

```text
Accepted spec + ADR
        │
        ▼
RED manifest/parser/path/inventory tests
        │
        ▼
Minimal verifier implementation
        │
        ▼
Targeted GREEN + full regression
        │
        ├───────────────┐
        ▼               ▼
CI integration     bilingual/public docs
        └───────┬───────┘
                ▼
v0.4 execution evidence package
                ▼
fresh independent review
                ▼
final receipt, manifest, release readiness
```

All source writers are serialized. Read-only verification and documentation review
may run in parallel after the implementation contract is accepted.

## Phase 1: Freeze the design

### Task 1: Approve the v0.4 contract

**Description:** Review the proposed spec, ADR, plan, and task list; resolve assumptions
before any behavior is implemented.

**Acceptance criteria:**

- [x] The objective and non-goals are explicitly accepted.
- [x] Assumptions 1-8 are explicitly accepted.
- [x] The separate CLI and integrity-not-authenticity boundary are accepted.
- [x] No unresolved product decision changes implementation scope.

**Verification:**

- [x] Spec status changes from `Proposed` to `Approved`.
- [x] ADR-0009 status changes from `Proposed` to `Accepted`.
- [x] `git diff --check` passes.

**Dependencies:** None.

**Files likely touched:**

- `docs/specs/adaptive-task-orchestrator-v0.4-portable-integrity.md`
- `docs/decisions/0009-verify-evidence-manifests-portably.md`
- `tasks/plan.md`
- `tasks/todo.md`

**Estimated scope:** Small.

### Task 1b: Freeze the v0.4 execution contracts

**Description:** Before RED tests or any delegated review, create the five immutable
root-owned TaskContracts that define test authoring, implementation, compatibility
verification, public integration, and independent review.

**Acceptance criteria:**

- [x] Each contract has one bounded outcome, exact scopes, acceptance checks,
      evidence requirements, and assurance requirement.
- [x] Contract identities are `V4-T1` through `V4-T5`, revision 1.
- [x] The files are written and inspected before the corresponding task starts.

**Verification:**

- [x] All five files parse as JSON.
- [x] Each revisioned file is the dispatch authority; v0.4 adds no mutable convenience
      pointer. Any later semantic change creates revision 2 rather than rewriting
      revision 1.

**Dependencies:** Task 1.

**Files likely touched:**

- `docs/context/adaptive-task-orchestrator-v0.4/contracts/revisions/V4-T1-red-tests-r1.contract.json`
- `docs/context/adaptive-task-orchestrator-v0.4/contracts/revisions/V4-T2-integrity-verifier-r1.contract.json`
- `docs/context/adaptive-task-orchestrator-v0.4/contracts/revisions/V4-T3-compatibility-verification-r1.contract.json`
- `docs/context/adaptive-task-orchestrator-v0.4/contracts/revisions/V4-T4-public-integration-r1.contract.json`
- `docs/context/adaptive-task-orchestrator-v0.4/contracts/revisions/V4-T5-independent-review-r1.contract.json`

**Estimated scope:** Medium, exactly five immutable files.

### Task 1c: Correct pre-dispatch dependency identities

**Description:** Preflight found that the revision 1 contracts for V4-T2 through
V4-T5 named dependency task IDs without immutable `@revision` identities. Preserve
those never-dispatched files, create revision 2 contracts with exact dependency
identities, and select only revision 2 for later routes.

**Acceptance criteria:**

- [x] V4-T1 remains revision 1 because it has no dependencies and was already
      dispatched against its accepted contract.
- [x] V4-T2 through V4-T5 revision 1 files remain byte-identical and are never routed.
- [x] Each revision 2 contract differs only in its own revision and exact dependency
      identities; every dependency names an existing accepted upstream revision.

**Verification:**

- [x] All four revision 2 files parse as JSON and pass strict contract validation.
- [x] A temporary current-contract projection proves dependency closure without
      modifying the versioned package.
- [x] No route or receipt selects V4-T2@1, V4-T3@1, V4-T4@1, or V4-T5@1.

**Dependencies:** Task 1b.

**Files likely touched:**

- `docs/context/adaptive-task-orchestrator-v0.4/contracts/revisions/V4-T2-integrity-verifier-r2.contract.json`
- `docs/context/adaptive-task-orchestrator-v0.4/contracts/revisions/V4-T3-compatibility-verification-r2.contract.json`
- `docs/context/adaptive-task-orchestrator-v0.4/contracts/revisions/V4-T4-public-integration-r2.contract.json`
- `docs/context/adaptive-task-orchestrator-v0.4/contracts/revisions/V4-T5-independent-review-r2.contract.json`

**Estimated scope:** Medium, exactly four immutable files.

## Phase 2: Build the deterministic oracle

### Task 2: Write the RED mutation tests

**Description:** Add focused tests that define valid manifest behavior and every
specified failure class before production code exists.

**Acceptance criteria:**

- [x] Positive and single-mutation cases match the specification.
- [ ] The first run fails because `verify_integrity` is absent or lacks the required
      behavior, not because the tests are malformed.
- [x] RED output and exit status are retained in the v0.4 task receipt.

**Accepted caveat:** The worker's first historical invocation exposed and repaired a
test f-string syntax error. Before any production code existed, the final module then
AST-parsed and produced the qualifying missing-module RED on Python 3.10 and 3.11.
The literal first-run criterion remains unchecked and is preserved in the receipt.

**Verification:**

- [x] Targeted test command fails with the expected missing-behavior signature.
- [x] Test file compiles and discovery finds all 14 test methods.

**Dependencies:** Task 1b.

**Files likely touched:**

- `fixtures/adaptive-task-orchestrator-write-dag/tests/test_verify_integrity.py`

**Estimated scope:** Medium.

### Task 3: Implement the minimal verifier

**Description:** Implement parsing, safe path handling, complete inventory, digest
comparison, deterministic findings, and the CLI needed to turn the RED suite GREEN.

**Acceptance criteria:**

- [x] Every specified valid package returns zero findings.
- [x] Every mutation returns the exact expected finding set.
- [x] The implementation performs no package writes and no out-of-root reads.

**Verification:**

- [x] Targeted v0.4 suite passes.
- [x] Full fixture suite passes.
- [x] v0.2 and v0.3 manifests report 100/100 and 65/65 through the new CLI.

**Dependencies:** Tasks 1c and 2.

**Files likely touched:**

- `fixtures/adaptive-task-orchestrator-write-dag/tools/verify_integrity.py`

**Estimated scope:** Medium.

### Checkpoint: Deterministic oracle

- [x] RED evidence is preserved.
- [x] GREEN targeted and full-suite evidence is preserved.
- [x] No accepted evidence package differs from `v0.3.0`.
- [x] Root inspects implementation simplicity and path-safety behavior.

## Phase 3: Integrate the public capability

### Task 4: Move CI to the portable verifier

**Description:** Replace platform-specific manifest commands with the project-native
CLI and expand CI to the approved Windows/Linux by Python 3.10/3.11 matrix while
retaining structural evidence checks.

**Acceptance criteria:**

- [ ] CI verifies v0.2 and v0.3 manifests through Python.
- [ ] Every test and validator runs in all four approved OS/runtime cells.
- [ ] The workflow retains read-only permissions and bounded runtime.
- [ ] No dependency-install step is added.

**Verification:**

- [ ] Root inspection confirms `permissions` is exactly `contents: read`, matrix OS
      values are exactly `ubuntu-latest` and `windows-latest`, Python values are
      exactly `3.10` and `3.11`, every `run` command is valid in both default runner
      shells, and no install/network step was introduced.
- [ ] `git diff --check -- .github/workflows/ci.yml` passes.
- [ ] Equivalent Windows commands pass locally; after the user authorizes a branch
      push, GitHub Actions is the Linux/Windows workflow oracle before release.

**Dependencies:** Task 3.

**Files likely touched:**

- `.github/workflows/ci.yml`

**Estimated scope:** Extra small.

### Task 5: Synchronize public documentation

**Description:** Document the new command and exact claim boundary in the fixture
guide, bilingual READMEs, and changelog.

**Acceptance criteria:**

- [ ] English and Chinese claims, commands, test counts, and caveats agree.
- [ ] Documentation says integrity/tamper detection, not authenticity/signature.
- [ ] Deferred crash recovery, strict closure, second domain, and third-party OpenAPI
      work remain visible.

**Verification:**

- [ ] For every changed relative Markdown link, root resolves the target from the
      source file's directory with PowerShell `Test-Path -LiteralPath`; no unresolved
      target remains. HTTP(S), `mailto:`, and same-document anchors are excluded.
- [ ] `rg -n "v0\\.4|verify_integrity|integrity|authenticity|test" README.md README.zh-CN.md`
      is inspected as a bilingual fact table. Version, command, test count, supported
      matrix, trusted-manifest premise, and deferred limitations must agree.

**Dependencies:** Task 3.

**Files likely touched:**

- `README.md`
- `README.zh-CN.md`
- `CHANGELOG.md`
- `fixtures/adaptive-task-orchestrator-write-dag/README.md`

**Estimated scope:** Medium.

### Checkpoint: Public integration

- [ ] The full fixture suite passes.
- [ ] `validate_evidence.py` passes separately for v0.2 and v0.3.
- [ ] `verify_integrity.py` passes separately for v0.2 and v0.3.
- [ ] CI and documentation invoke commands that exist.
- [ ] No public claim exceeds the deterministic oracle.

## Phase 4: Evidence and independent assurance

### Task 6a: Record RED/GREEN implementation evidence

**Description:** Record the accepted routes and receipts for RED test authoring and
the minimal verifier implementation, plus one deterministic RED/GREEN summary.

**Acceptance criteria:**

- [x] `V4-T1@1` records the expected RED command, failure signature, and unchanged
      repository identity before production code exists.
- [x] `V4-T2@2` records targeted GREEN, full regression, v0.2/v0.3 compatibility,
      and read-only checks.
- [x] Each route selects the already frozen matching TaskContract revision and each
      receipt reports only evidence produced by that task.

**Verification:**

- [x] The five files parse as JSON through the exact JSON command in Task 8.
- [x] `validate_evidence.py --context-root` for v0.4 reports no route, receipt, task,
      or revision identity finding after the files exist.

**Dependencies:** Task 3.

**Files likely touched:**

- `docs/context/adaptive-task-orchestrator-v0.4/routes/V4-T1-red-tests-r1.route.json`
- `docs/context/adaptive-task-orchestrator-v0.4/routes/V4-T2-integrity-verifier-r2.route.json`
- `docs/context/adaptive-task-orchestrator-v0.4/receipts/V4-T1-red-tests-r1.json`
- `docs/context/adaptive-task-orchestrator-v0.4/receipts/V4-T2-integrity-verifier-r2.json`
- `docs/context/adaptive-task-orchestrator-v0.4/evidence/red-green-summary.json`

**Estimated scope:** Medium, exactly five files.

### Task 6b: Record mutation and compatibility evidence

**Description:** Record the compatibility-verification route and receipt, the exact
single-mutation result matrix, and the four-cell supported-runtime matrix.

**Acceptance criteria:**

- [ ] Every mutation row records input identity, expected findings, actual findings,
      exit status, repeatability, and pre/post package identity.
- [ ] Every runtime row records OS, Python version, command, exit status, and exact
      canonical finding sequence or zero-finding result.
- [ ] Compatibility evidence identifies immutable v0.2 and v0.3 bytes and exact entry
      counts without rewriting either package.

**Verification:**

- [ ] The four files parse as JSON through the exact JSON command in Task 8.
- [ ] `validate_evidence.py --context-root` for v0.4 reports no route, receipt, task,
      or revision identity finding after the files exist.

**Dependencies:** Task 3 and completion of the four-cell CI run from Task 4.

**Files likely touched:**

- `docs/context/adaptive-task-orchestrator-v0.4/routes/V4-T3-compatibility-verification-r2.route.json`
- `docs/context/adaptive-task-orchestrator-v0.4/receipts/V4-T3-compatibility-verification-r2.json`
- `docs/context/adaptive-task-orchestrator-v0.4/evidence/mutation-matrix.json`
- `docs/context/adaptive-task-orchestrator-v0.4/evidence/runtime-compatibility-matrix.json`

**Estimated scope:** Medium, exactly four files.

### Task 6c: Record public-integration evidence

**Description:** Record the public-integration route and receipt, the CI/command
integration result, and a bilingual capability-and-caveat fact table.

**Acceptance criteria:**

- [ ] The integration summary records the workflow matrix, permissions, commands,
      dependency boundary, and all validation exit statuses.
- [ ] The bilingual facts compare version, command, test count, supported matrix,
      trusted-manifest premise, and deferred limitations field by field.
- [ ] Documentation claims tamper detection only relative to a trusted manifest and
      never claim signatures, provenance, trusted time, or authenticity.

**Verification:**

- [ ] The four files parse as JSON through the exact JSON command in Task 8.
- [ ] `validate_evidence.py --context-root` for v0.4 reports no route, receipt, task,
      or revision identity finding after the files exist.

**Dependencies:** Tasks 4 and 5.

**Files likely touched:**

- `docs/context/adaptive-task-orchestrator-v0.4/routes/V4-T4-public-integration-r2.route.json`
- `docs/context/adaptive-task-orchestrator-v0.4/receipts/V4-T4-public-integration-r2.json`
- `docs/context/adaptive-task-orchestrator-v0.4/evidence/public-integration-summary.json`
- `docs/context/adaptive-task-orchestrator-v0.4/evidence/bilingual-claims.json`

**Estimated scope:** Medium, exactly four files.

### Task 7: Run fresh independent review

**Description:** Give a fresh reviewer the approved spec, raw diff, tests, mutation
matrix, and evidence package. Require correctness, path-safety, architecture,
security, performance, compatibility, and claim-boundary findings.

**Acceptance criteria:**

- [ ] Reviewer did not author the implementation.
- [ ] Every Critical or Required finding is repaired or causes REPLAN/STOP.
- [ ] At most two bounded author-review repair loops are used.

**Verification:**

- [ ] Final review decision is `ACCEPT` or `ACCEPT_WITH_CAVEATS` with no unresolved
      Critical or Required finding.
- [ ] Root reruns changed-path tests after each repair.

**Dependencies:** Tasks 6a, 6b, and 6c.

**Files likely touched:**

- `docs/context/adaptive-task-orchestrator-v0.4/routes/V4-T5-independent-review-r2.route.json`
- `docs/context/adaptive-task-orchestrator-v0.4/receipts/V4-T5-independent-review-r2.json`
- `docs/context/adaptive-task-orchestrator-v0.4/evidence/independent-review-summary.json`

**Estimated scope:** Small, exactly three files; its contract was frozen by Task 1b.

### Task 8: Close the v0.4 evidence package

**Description:** Publish the context guide, final validation receipt, self-excluding
manifest, and indexes only after all files are final.

**Acceptance criteria:**

- [ ] Manifest includes every v0.4 regular file except itself exactly once.
- [ ] New verifier accepts v0.4 with zero findings.
- [ ] Final receipt lists verified and explicitly unverified claims.
- [ ] Finalization order is fixed: (1) finalize every package file including the
      receipt; (2) generate `integrity.sha256` last in case-sensitive ASCII-byte
      manifest order; (3) verify the package read-only; (4) make no further package
      edit; and (5) retain final verifier output outside the immutable package or in
      CI, never by writing it back into the package.

**Verification:**

- [ ] v0.2 remains 100/100, v0.3 remains 65/65, and v0.4 reports its exact count.
- [ ] The full suite passes; `validate_evidence.py` passes separately for v0.2,
      v0.3, and v0.4; `verify_integrity.py` passes separately for all three packages.
- [ ] JSON parsing uses this exact PowerShell check:

  ```powershell
  $contextRoot = 'docs/context/adaptive-task-orchestrator-v0.4'
  $jsonFiles = Get-ChildItem -LiteralPath $contextRoot -Recurse -File -Filter '*.json'
  foreach ($file in $jsonFiles) {
      Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json | Out-Null
  }
  $jsonlFiles = Get-ChildItem -LiteralPath $contextRoot -Recurse -File -Filter '*.jsonl'
  foreach ($file in $jsonlFiles) {
      foreach ($line in Get-Content -LiteralPath $file.FullName) {
          if ($line.Length -gt 0) { $line | ConvertFrom-Json | Out-Null }
      }
  }
  ```

- [ ] Cross-file identity closure uses this exact structural command:

  ```powershell
  py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py `
    --context-root docs/context/adaptive-task-orchestrator-v0.4
  ```

- [ ] Changed relative Markdown links and bilingual claims pass the exact Task 5
      checks.
- [ ] This bounded secret-pattern scan returns no match; `rg` exit 1 is the expected
      no-match result:

  ```powershell
  rg -n -e 'AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----' `
    --glob '!.git/**' .
  ```

- [ ] `git diff --check` passes after the manifest verification, without changing
      package bytes.

**Dependencies:** Task 7.

**Files likely touched:**

- `docs/context/adaptive-task-orchestrator-v0.4/README.md`
- `docs/context/adaptive-task-orchestrator-v0.4/evidence/final-validation-receipt.json`
- `docs/context/adaptive-task-orchestrator-v0.4/integrity.sha256`
- `docs/context/README.md`
- `docs/decisions/README.md`

**Estimated scope:** Medium.

### Checkpoint: Complete

- [ ] All success criteria in the approved spec are met.
- [ ] Feature branch is clean and reviewable.
- [ ] No release tag or public push occurs without explicit release authorization.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Unsafe manifest path reads outside the package | High | Parse and reject paths before any target open; mutation tests patch the read boundary. |
| Case behavior differs across Windows and Linux | High | Serialize `/`, use explicit ordinal ordering, reject case-fold collisions, test canonical strings rather than host directory order. |
| Exact-inventory checks flag validator output or caches | Medium | Production verifier writes nothing; invoke Python with `-B`; tests compare before/after inventory. |
| Manifest work is overstated as authenticity | High | Repeat integrity-not-authenticity language in spec, ADR, CLI docs, bilingual README, receipt, and review contract. |
| Existing package compatibility is broken | High | Separate CLI; treat v0.2/v0.3 as immutable positive integration fixtures. |
| Verifier grows into another monolith | Medium | Keep one focused module with pure helpers; independent review applies the ~1000-line file signal and removes premature abstractions. |
| Evidence packaging overwhelms implementation scope | Medium | Split evidence writers by immutable task-owned file groups; root alone owns indexes and final manifest. |

## Open Question

- Release publication remains a separate user decision. Implementation stops at a
  release-ready feature branch before any public push, tag, or GitHub Release.
