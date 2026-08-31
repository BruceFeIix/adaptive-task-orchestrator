# v0.4 portable evidence integrity tasks

Status: approved by the user on 2026-08-31; implementation is in progress.

- [x] Establish repository instructions, clean baseline, remote parity, and existing
      validation commands.
  - Acceptance: `main` matched `origin/main`; 44/44 tests passed; v0.2 and v0.3
    structural validators passed; integrity remained 100/100 and 65/65.
  - Verify: baseline receipts retained in the active task.
  - Files: none.

- [x] Compare candidate v0.4 directions with three independent read-only audits.
  - Acceptance: portable integrity, strict evidence closure, crash recovery, and a
    second domain were evaluated against current claims and boundaries.
  - Verify: root reconciled the conflicting recommendations by oracle strength,
    compatibility, user value, and version size.
  - Files: none.

- [x] User approves the v0.4 spec, ADR-0009, and implementation plan.
  - Acceptance: Assumptions 1-8, integrity-not-authenticity boundary, separate CLI,
    quiescent-package model, four-cell OS/runtime matrix, and deferred work are
    accepted.
  - Verify: proposed documents are changed to approved/accepted status.
  - Files: `docs/specs/adaptive-task-orchestrator-v0.4-portable-integrity.md`,
    `docs/decisions/0009-verify-evidence-manifests-portably.md`, `tasks/plan.md`,
    `tasks/todo.md`.

- [x] Freeze the five v0.4 execution contracts before RED tests or dispatch.
  - Acceptance: `V4-T1@1` through `V4-T5@1` each define one bounded outcome, exact
    scopes, acceptance checks, evidence requirements, and assurance requirement.
  - Verify: exactly five revision files parse as JSON; a later semantic change creates
    a new revision rather than rewriting revision 1.
  - Files: the five named files under
    `docs/context/adaptive-task-orchestrator-v0.4/contracts/revisions/` listed in the
    implementation plan.

- [x] Preserve the never-dispatched invalid dependency forms and create V4-T2 through
      V4-T5 revision 2 contracts with exact `task_id@revision` dependencies.
  - Acceptance: revision 1 bytes remain unchanged; no later route selects them; each
    revision 2 changes only revision/dependency identity semantics.
  - Verify: four JSON files parse, temporary current-contract projection passes
    dependency closure, and route/receipt search finds no selection of the rejected
    revisions.
  - Files: exactly the four Task 1c revision paths in `tasks/plan.md`.

- [x] RED: add manifest grammar, path-safety, inventory, digest, ordering, and
      repeatability tests.
  - Acceptance: tests cover the exact mutation matrix and fail for missing behavior.
  - Verify: targeted test command fails with the recorded expected signature.
  - Files: `fixtures/adaptive-task-orchestrator-write-dag/tests/test_verify_integrity.py`.
  - Caveat: the first historical invocation found a test syntax error; after the
    bounded repair and before production code, Python 3.10/3.11 each discovered 14
    tests and failed only with the expected missing-module signature.

- [x] GREEN: implement the read-only portable integrity verifier.
  - Acceptance: all targeted mutations produce exact stable findings; valid packages
    produce none; no write or out-of-root read occurs.
  - Verify: targeted and full suites pass; v0.2/v0.3 verify through the new CLI.
  - Files: `fixtures/adaptive-task-orchestrator-write-dag/tools/verify_integrity.py`.

- [ ] Integrate the verifier into CI.
  - Acceptance: Python replaces GNU `sha256sum` for both immutable packages without
    adding dependencies or permissions; all tests and validators run on
    `ubuntu-latest` and `windows-latest` with Python 3.10 and 3.11.
  - Verify: root checks the exact matrix, `permissions: contents: read`, portable run
    commands, absence of install/network steps, and local Windows equivalents;
    GitHub Actions is the final four-cell oracle after an authorized branch push.
  - Files: `.github/workflows/ci.yml`.

- [ ] Synchronize English, Chinese, fixture, and changelog documentation.
  - Acceptance: command, test count, capability, and caveat statements agree.
  - Verify: root resolves every changed relative Markdown link from its source
    directory with PowerShell `Test-Path -LiteralPath`, then inspects the plan's exact
    `rg` bilingual fact table for version, command, test count, matrix, trust premise,
    and deferred limitations.
  - Files: `README.md`, `README.zh-CN.md`, `CHANGELOG.md`,
    `fixtures/adaptive-task-orchestrator-write-dag/README.md`.

- [x] Record `V4-T1@1`/`V4-T2@2` RED/GREEN implementation evidence (Task 6a).
  - Acceptance: two routes, two receipts, and one RED/GREEN summary contain exact
    commands, statuses, identities, and read-only results.
  - Verify: all five JSON files parse and v0.4 structural identity validation passes.
  - Files: exactly the five Task 6a paths in `tasks/plan.md`.

- [ ] Record `V4-T3@2` mutation and compatibility evidence (Task 6b).
  - Acceptance: each mutation and each OS/runtime cell records expected and actual
    deterministic outcomes, including v0.2/v0.3 immutable compatibility.
  - Verify: all four JSON files parse and v0.4 structural identity validation passes.
  - Files: exactly the four Task 6b paths in `tasks/plan.md`.

- [ ] Record `V4-T4@2` public-integration evidence (Task 6c).
  - Acceptance: CI permissions/matrix/commands and bilingual claims/caveats are
    compared field by field.
  - Verify: all four JSON files parse and v0.4 structural identity validation passes.
  - Files: exactly the four Task 6c paths in `tasks/plan.md`.

- [ ] Run fresh independent five-axis and adversarial review.
  - Acceptance: no unresolved Critical or Required finding after at most two repair
    loops.
  - Verify: reviewer decision and repair evidence are recorded.
  - Files: exactly the `V4-T5@2` route, receipt, and independent-review summary listed
    in Task 7; its contract is already frozen by Task 1b.

- [ ] Close the v0.4 package and final validation receipt.
  - Acceptance: the self-excluding manifest covers every final file exactly once;
    final claims remain narrower than authenticity or runtime enforcement; all
    package files including the receipt are final before the manifest is generated,
    and no package byte changes after read-only verification.
  - Verify: execute the exact JSON/JSONL, v0.2/v0.3/v0.4 structural and integrity,
    changed-link, bilingual-fact, bounded secret-pattern, and diff checks in Tasks 5
    and 8; store final verifier output outside the immutable package or in CI.
  - Files: v0.4 README, final receipt, manifest, context index, ADR index.

- [ ] Prepare the version for release.
  - Acceptance: feature branch is clean, changelog is release-ready, and the version
    bump remains additive and backward compatible.
  - Verify: root reports exact commit and release checklist; public push/tag/release
    require the user's release decision.
  - Files: no additional files unless review identifies a required correction.
