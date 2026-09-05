# ADR-0010: Correct v0.4 count handling and canonical-output evidence

## Status

Accepted for the user-approved v0.4 correction plan on 2026-09-06. Final independent
review and actual GitHub Actions execution remain separate acceptance gates.

## Context

The independent review of `c7a710b` returned REVISE. R1 identified an unbounded
decimal-to-int conversion that raises on Python 3.11 but not 3.10. R2 identified
zero-count entries misclassified as header errors. R3 found that code/path-only
oracles did not establish complete canonical finding equality. R4 identified
pass counts that included a skipped method.

The strengthened binary-output oracle additionally reproduced native Windows
CRLF output from `print()`. Earlier text-mode subprocess checks normalized this
difference before comparison. This is a newly observed consequence of R3, not a
previously verified cross-platform byte guarantee.

## Decision

- Keep canonical decimal tokens as strings and compare with `str(len(entries))`.
- Blank lines and extra comment lines after the six headers are header violations
  regardless of the count. Other entry lines are parsed normally, including after
  count zero; only grammatically parsed entries participate in count comparison.
  The formerly inconsistent blank-entry classification is corrected before release.
- Keep exact expected detail literals in the test oracle; dynamic details derive
  from test inputs, never actual findings. Compare full ordered findings twice.
- Assert raw native CLI stdout bytes, empty stderr, and exit status twice for
  supported filesystem cases. Emit ASCII-escaped JSON with an explicit LF through
  binary stdout. In-process injected I/O errors are tested at the function boundary
  and are not described as native CLI tests.
- Split manifest-file, listed-file, and directory symlinks into independent tests.
- Produce new observations directly from the test run, including expected/actual
  details, output hashes, before/after inventory identities, and explicit skips.

## Historical correction and precedence

Existing v0.4 receipts and evidence recorded at or before `c7a710b` remain unchanged
as historical candidate records. Their `58/58` or `58 tests passed, 1 skip` language
means 58 discovered, 57 passed, 1 skipped; targeted 14 means 13 passed, 1 skipped.
Their code/path-only mutation results do not prove complete detail or byte parity.
Their earlier ACCEPT_WITH_CAVEATS conclusions are not final v0.4 acceptance after
the independent review's REVISE decision.

New correction records and observations supersede these claims for the corrected
candidate only. They do not retroactively upgrade historical checks. Accepted
v0.2/v0.3 packages, contracts, snapshots, and manifests remain immutable.

## Boundaries

Local success does not establish Linux or GitHub-hosted results. Real symlink
assertions skipped due to missing permission remain unexecuted. Integrity is
relative to a trusted manifest under a quiescent-package assumption; it proves
neither authenticity nor concurrent hostile-filesystem safety.
