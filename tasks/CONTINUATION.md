# Astra continuation checkpoint

## Authority and stop policy

The user approved completing v0.4 correctness/evidence closure and v0.5
runtime-aware Astra routing, then continuing bounded work toward that scope.
Important design, implementation and review stay with the current Astra root or
an explicitly requested gpt-6-astra reviewer; generic Sol defaults do not override
that instruction. Requested identity is not runtime-attested effective identity.

Check account usage before/after bounded batches. Start no long worker below 5%
remaining; stop implementation at or before the observed 2% reserve and save a
checkpoint. Missing usage windows are unknown, and usage is account-wide.
Never automatically downgrade, consume reset credits, push, tag, release, install
globally, invoke an external model CLI, or broaden execution permissions.

## Current authoritative state

- Branch: feature/v0.5-runtime-routing. Run git status and git log before resuming.
- Latest policy/evidence increment: 03ae7e5; workspace Skill sync verified 9/9.
- v0.4 local candidate sealed at 0ea8bfd, with 33 manifest entries.
- v0.4 manifest SHA-256: ECE91E9E802C0E171FA5F9F165CA746F5F8290313032934936FCD8613492CC4A.
- v0.2/v0.3/v0.4 accepted or sealed packages remain immutable.
- Latest observed quota: 14% remaining in the only reported weekly window.
- Six existing README/CHANGELOG/index/CI edits are root-authored pending closure;
  preserve any additional dirty paths rather than assuming ownership.

## Completed and evidenced

- v0.4 R1-R4 corrections and independent correction review accepted with caveats.
  Its frozen full-suite baseline is 63 discovered, 60 passed, 3 skipped per Python.
- v0.5 design repair review V5-D1@2 and checker review V5-I1@1 accepted with
  caveats, zero remaining Critical/Required. Registry and runtime Skill implemented.
- Checker tests include malformed input, complete CLI bytes, pins, effective
  evidence, review cycles, concurrency, immutable inputs and controlled mutations.
  Retained postreview evidence has 42 targeted + 5 registry tests per Python;
  prior root full-suite run had 110 discovered, 107 passed, 3 legacy symlink skips.
  Do not treat an earlier 80/98-test increment as the final integrated count.
- Policy forward-test V5-P1@1 accepted with caveats, zero Critical/Required.
  Full hypothetical inputs and a clearly labeled root-transcribed receipt are
  retained. Root reproduced all six positive/negative cases twice each on
  Python 3.10.0 and 3.11.9 with exact findings and unchanged inputs.
- Two optional policy ambiguities were clarified without changing checker or
  registry behavior. Independent-task creation is not a child-capacity workaround.
- Latest read-only Python 3.11 checks: v0.2/v0.3/v0.4 structure + integrity
  (six commands) and the v0.5 planned route CLI all exited zero with no findings.

## Remaining work in dependency order

1. Local Skill synchronization is complete: exact inventories and all nine SHA-256
   pairs match. Evidence: v0.5/evidence/workspace-skill-sync.json. Recheck after any
   later source edits; do not assume this point-in-time result remains current.
2. Complete bounded fixed-task comparisons before changing provisional generic
   defaults. Keep requested-only observations distinct from effective model proof;
   no broad quality/cost/latency claim or subscription-cost inference.
3. Finish bilingual docs, indexes, CI commands and current integration evidence.
   Add v0.5 context README/final local receipt; generate its manifest LAST.
   Validate the integrated package on both local Python runtimes.
4. Keep actual GitHub Actions four-cell execution, Linux and real symlink checks
   explicitly pending until observed. Do not publish just to trigger CI.
5. Apply the full completion audit against the specification, not only green
   validators. If quota is low, save progress without marking the goal complete.

## Known boundaries

The checker checks declared records, not authenticity or complete-run success.
The native spawn response only established accepted request/task identity, not the
effective model/effort. High-risk accepted/completed assurance cannot be fabricated.
Skill quick_validate.py could not run because PyYAML is absent; unchanged metadata
and resolved links were checked manually, not called a validator pass.
Local WSL listing returned access denied; no Linux execution claim.
Generic capability ranks/defaults remain provisional. Full attempt/event/effect
closure, crash recovery, signatures, external runtimes and second-domain validation
are deferred, not silently folded into the current version.

## Fast resume

Read this file, applicable AGENTS.md, git status/current HEAD and current quota.
Inspect the receipts and actual artifacts for the first incomplete item. Reuse
valid prior checks; repeat tests only for changed artifacts or unresolved concerns.

Suggested user instruction: "Resume the approved v0.4/v0.5 plan from
tasks/CONTINUATION.md; keep critical work on Astra and retain a 2% quota reserve."
The goal remains active until the complete authorized outcome is genuinely proved.
