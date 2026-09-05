# Astra continuation checkpoint

## Authority and stop policy

On 2026-09-06 the user approved the staged plan: finish v0.4 correctness and
evidence closure, then implement v0.5 runtime-aware Astra routing and verification.
Important design, implementation, and review stay with the current Astra root or
an explicitly requested `gpt-6-astra` reviewer. This user instruction overrides
the existing Sol default while the registry upgrade is in progress. A requested
model is not evidence of the effective model identity.

Read account usage before and after bounded work batches. Start no long-running
worker below 5% remaining. Stop implementation at or before the observed 2%
reserve, save this checkpoint, and report status. Missing windows are unknown,
not unused capacity. Usage is account-wide and can change between observations.
Do not consume reset credits automatically. No automatic model downgrade.

## Current baseline

- Active branch: `feature/v0.5-runtime-routing`.
- Sealed v0.4 branch: `feature/v0.4-portable-integrity`, commit `0ea8bfd`.
- Starting commit: `c7a710b`; worktree was clean.
- First usage observation: 23% remaining in the only reported weekly window.
- P0 local candidate is sealed; actual platform gates remain pending. P1 design
  repair review accepted with caveats and no remaining Required findings. The
  first P2 checker increment passes 17 targeted tests and the 80-method full suite
  on both local runtimes (77 passed, 3 legacy symlink skips). Expanded tests,
  implementation review, registry, native smoke, live policy and P3-P4 remain.
- The previous independent review returned REVISE with R1-R4 below.
- Existing v0.4 receipts describe pre-repair candidates, not final acceptance.
- v0.2/v0.3 accepted evidence and all historical contracts remain immutable.
- Public push, tag, release, and external model CLI execution are not authorized.

## P0: v0.4 corrections

- [x] R1: compare canonical decimal count tokens without unbounded `int()`.
- [x] R2: classify zero count plus valid/invalid entries by the actual grammar.
- [x] R3: compare complete findings, literal details, and canonical output bytes.
- [x] R4: distinguish discovered/passed/skipped/failed counts in current claims.
- [x] Split real symlink scenarios so each execution or skip is observable.
- [x] Record RED/GREEN and corrected mutation evidence in new records.
- [x] Independently review the changed artifact with Astra.
- [x] Close the local candidate package; generate its manifest last.
- [ ] Keep actual four-cell CI and real-platform gaps explicitly pending until run.

## P1-P4: v0.5 approved direction

1. Freeze a new specification and ADR: versioned candidate registry, host/tool
   capability snapshot, availability versus effective-route evidence, model/effort
   compatibility, fork rules, concurrency counting, and monotonic fallback.
2. Add a standard-library route semantics checker with explicit profile/version;
   preserve legacy evidence validation behavior. It does not execute agents.
3. Test rule failures offline, then perform bounded native subagent smoke checks.
   Record only observed metrics; no fabricated identity or cost claims.
4. Synchronize bilingual documentation, CI, versioned evidence, and the two local
   Skill copies through an explicit hash-checked update. No global installation.

Full strict-complete-run closure, crash recovery, external runtimes, signatures,
second-domain validation, and quadratic inventory optimization remain later work.

## Resume procedure

Latest local checks: each Python 3.10/3.11 full suite discovered 63, passed 60,
skipped 3; each targeted suite discovered 19, passed 16, skipped 3. There are 59
directly collected two-run observations per runtime; complete findings and native
CLI output hashes match across the two runtimes. Eight legacy validator commands
passed. ADR-0010 corrects the earlier candidate overclaims. Review remains pending.
The sealed v0.4 package has 33 manifest entries. Both Python runtimes pass its
structural and integrity checks. Manifest SHA-256:
`ECE91E9E802C0E171FA5F9F165CA746F5F8290313032934936FCD8613492CC4A`.
Correction reviewer accepted with caveats, zero Critical/Required. Do not edit the
v0.4 package now; record all later checks and CI outside it.
Latest observed quota: 18% remaining. No reset used.

## Latest v0.5 increment

The root-only module `validate_runtime_routes.py` now implements schema, candidate
intersection, floors, overrides/history/context, pinned pairs, monotonic fallbacks,
effective evidence bindings, review relationships/cycles, concurrency and record
coverage. It is opt-in and does not execute agents. First validation and source
hashes are in `docs/context/adaptive-task-orchestrator-v0.5/evidence/first-checker-increment.json`.
This is an implementation candidate, not independently accepted. The next action
is expanded malformed-input/negative/golden-byte tests, then a frozen Astra review.
Do not claim the currently unchanged live Skill or README already describes v0.5.

Read this file and applicable AGENTS.md; inspect `git status`, current HEAD, and
the latest quota. Preserve any newly dirty user files. Resume from the first
unchecked item using the actual files and retained checks, not the checkbox alone.
With adequate quota, the user can say: "Resume the approved v0.4/v0.5 plan from
tasks/CONTINUATION.md; keep critical work on Astra and retain a 2% quota reserve."
An active goal is not complete merely because quota requires stopping.
