# v0.4 portable-integrity local candidate evidence

This package records a corrected local candidate, not a completed cross-platform
release. The user approved portable integrity verification and later R1-R4 repairs.
Current claims follow the corrections and final local receipt below. Older records
are retained as historical candidates, including their rejected overclaims.

## Read order and precedence

1. [ADR-0010](../../decisions/0010-correct-v04-count-and-canonical-output-evidence.md)
   explains the count, LF-output, oracle and skipped-test corrections.
2. [Correction summary](evidence/corrections/summary.json) records RED/GREEN and
   supersedes current claims in the earlier candidate evidence.
3. [Python 3.10 observations](evidence/corrections/python-3.10-observations.json) and
   [Python 3.11 observations](evidence/corrections/python-3.11-observations.json)
   contain 59 directly collected records each: full expected/actual findings,
   two-run byte hashes and pre/post identities. There are 55 native CLI cases and
   four function-only injected-I/O cases per runtime.
4. [Independent review history](evidence/independent-review-summary.json) links the
   original REVISE and corrected ACCEPT_WITH_CAVEATS decisions.
5. [Correction review receipt](receipts/V4-R1-correction-review-r1.json) independently
   reproduces the observations at correction commit `a45922e`.
6. [Final local validation](evidence/final-validation-receipt.json) defines the
   package's current local acceptance boundary. The self-excluding
   [manifest](integrity.sha256) is generated only after all package files are final.

## Current boundary

- Root ran 63 discovered tests on Windows Python 3.10/3.11: 60 passed, 3 skipped
  on each. Independent review reran the 19-test integrity subset: 16 passed,
  3 skipped; it discovered but did not independently run the whole suite.
- The three real symlink assertions were not executed locally (WinError 1314).
- All four actual GitHub Actions cells and Linux execution remain pending.
- Eight local legacy package checks passed. v0.2/v0.3 files remain unchanged.
- Requested Astra routing does not prove the effective model identity.
- Integrity is consistency with a selected trusted manifest in a quiescent package.
  It does not establish authenticity, trusted time, event truth, or hostile
  concurrent-filesystem safety.

Earlier `58/58` statements mean 58 discovered, 57 passed and 1 skipped. Earlier
targeted `14 passed` statements mean 14 discovered, 13 passed and 1 skipped.
Code/path-only checks did not establish complete detail or raw-output parity.
These historical records are not retroactively rewritten or treated as current.

## Revalidation

From the repository root, run the tooling suite and the separate structural and
integrity CLIs for this directory. Retain later CI logs and publication receipts
outside the sealed package. No package byte is changed after its manifest.
Actual CI on the final candidate is still required before claiming cross-platform
release readiness; an exit-0 structural check alone does not close that gate.
