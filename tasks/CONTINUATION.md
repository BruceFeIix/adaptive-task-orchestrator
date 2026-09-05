# Astra continuation checkpoint

## Authority and stop policy

The user approved the v0.4 correctness/evidence closure and v0.5 runtime-aware
Astra routing plan, with bounded fixed-task comparisons and a quota reserve.
Important design, implementation and review stay on Astra; generic Sol defaults
do not override that instruction. Requested identity is not effective identity.

Check account usage before/after bounded batches. Start no long worker below 5%
remaining; stop implementation at or before the observed 2% reserve. Missing
windows are unknown; usage is account-wide. Never automatically downgrade or
consume reset credits. Public push, PR, tag/release, global installation,
external model CLIs and permission expansion need their applicable authorization.

The user has now explicitly authorized pushing feature/v0.5-runtime-routing and
creating a PR to main for CI verification, including bounded CI repairs. Do not
merge, tag or release. This removes the previous push/PR authorization boundary.

## Current state

- Branch: feature/v0.5-runtime-routing. Inspect git status and git log on resume.
- v0.5 sealed local candidate: 82ccf02f825bf7ff83e30d6fe9717dab0f4d5eb8.
- v0.5 manifest: 34 entries, self-excluding, case-sensitive ordinal paths.
- v0.5 manifest SHA-256: AF635FD87B6CF0AD03230116B67C2AC890E821621B050752F8D56DB5A1A857C2.
- v0.4 sealed local candidate: 0ea8bfd, 33 entries; manifest SHA-256:
  ECE91E9E802C0E171FA5F9F165CA746F5F8290313032934936FCD8613492CC4A.
- v0.2/v0.3/v0.4/v0.5 accepted/sealed packages are immutable. Later observations
  belong outside them, for example docs/validation/.
- Repository and parent workspace Skill copies both have 9 files. All exact paths
  and SHA-256 pairs match. No global install; historical v0.1 snapshot unchanged.
- Latest quota observation: 9% remaining, 91% used in the reported weekly window
  during the CI repair batch. No reset consumed, no automatic downgrade.
- Feature branch was pushed without force or tags. Draft PR #1 is open to main:
  https://github.com/BruceFeIix/adaptive-task-orchestrator/pull/1.
- Initial PR head: e21a8ab5848d2f671c269c99607b2da2103eb8c9. Remote main was observed
  at 52ec8c9fbc5b018b8f669d4176100899e8802deb before PR creation; recheck when needed.
- CI run 33995561302: both Linux cells passed all 110 tests without skips and all
  later gates. Both Windows cells failed five fault-injection assertions/subtests
  across four methods. All four cells executed the three real-symlink tests.
- A deterministic alias/.. reproduction identified lexical-versus-canonical mock
  target mismatch. ADR-0012 records the test-only correction; full local suites
  pass 107 with 3 permission skips on both Python versions. Corrected CI pending.

## Completion audit

| Requirement | Evidence and current status |
|---|---|
| v0.4 R1-R4 correctness repairs | Done locally; frozen correction review ACCEPT_WITH_CAVEATS, zero Critical/Required |
| Versioned registry and host/effort rules | Done; live 9-file Skill, v0.5 spec and ADR-0011 |
| Offline semantic checker and meaningful negative tests | Done; V5-I1 review, Cartesian/adversarial probes and six controlled mutations |
| Independent Skill behavior test | Done; V5-P1 receipt, six cases reproduced twice on Python 3.10/3.11; two optional wording clarifications applied |
| Bounded fixed-task comparison | Done as a pilot; frozen three-task inputs/oracles, requested Astra and Terra first-pass 3/3 each, no repairs |
| Generic model calibration | Defaults remain explicitly provisional; this pilot does not justify a model ranking or cost/latency claim |
| Integrated local suite | Done; Python 3.10.0 and 3.11.9 each discovered 110, passed 107, skipped 3 real-symlink cases |
| Historical regression gates | Done locally; 12 v0.2/v0.3/v0.4 structural/integrity checks across both runtimes, no historical diff |
| Two local Skill copies | Done; 9/9 exact inventory and byte-hash matches, rechecked after sealing |
| Bilingual docs, CI definitions, evidence and manifest | Done locally; 34-entry seal and four post-seal checks, zero diagnostics |
| Actual Windows/Linux four-cell GitHub Actions | First run observed; Linux passed, Windows fault-injection repair requires CI revalidation |
| Real symlink assertions | All three passed in all four first-run CI cells; local host still lacks the required privilege |
| Effective model/effort attestation | Unavailable from observed native task-name-only responses; do not fabricate it |
| Public release | Not authorized/performed; local acceptance is not release completion |

Current receipt: docs/context/adaptive-task-orchestrator-v0.5/evidence/final-validation-receipt.json.
Post-seal evidence: docs/validation/v0.5-postseal-local.json.
First actual CI observation: docs/validation/v0.5-ci-initial.json.
Read the package README for the evidence order and exact scope of each review.

## Next actionable work

1. The bounded ADR-0012 test correction passed independent requested-Astra review
   with no Critical/Required findings. Push it to the existing feature branch and
   inspect the new PR #1 CI run. Do not create a duplicate PR.
2. Inspect each cell's test counts, real-symlink execution, structural/integrity
   and route gates. Do not merge or release merely because CI later passes.
3. If CI finds a real issue, implement a bounded fix with relevant RED/GREEN tests.
   Preserve sealed packages; record corrections via new ADR/errata/evidence and
   rerun only affected checks plus the final integration gate.
4. Save later platform results outside sealed packages. Ask for a separate merge
   or release decision when the complete relevant gates genuinely pass.
5. When quota approaches the reserve, save progress and stop. Do not spend quota
   on unchanged audits or broaden the task merely to reach the threshold.

## Remaining boundaries

The native checker proves declared consistency, not authentic identity or full
attempt/event/effect closure. Skill quick_validate.py could not run because PyYAML
was absent; manual unchanged-metadata/link validation is disclosed as a fallback.
WSL listing returned access denied; no Linux execution or permission change was
inferred. The tiny requested-configuration pilot is not a general benchmark.
Full lifecycle/crash recovery, signatures, external runtimes, second-domain
validation and inventory optimization remain separately scoped later work.

## Fast resume

Read this checkpoint, applicable AGENTS.md, actual git state and fresh account
quota. Follow the first incomplete authorized item rather than stale chat text.
Do not repeat accepted local reviews without changed artifacts or a new failure.

Push/PR authorization is recorded above. Continue the existing PR's verification;
do not repeat accepted local reviews or request the same authorization again.
Platform success, effective-model attestation and public release are distinct
claims. CI success alone does not close the latter two boundaries.
