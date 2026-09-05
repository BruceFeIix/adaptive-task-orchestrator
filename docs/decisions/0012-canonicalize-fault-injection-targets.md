# ADR-0012: Canonicalize fault-injection targets without changing tool behavior

## Status

Accepted bounded test-harness correction, 2026-09-06. Four-cell CI revalidation
is required before claiming the platform gate is closed.

## Context

The first PR #1 CI run, 33995561302, passed both Linux cells but failed both
Windows cells with the same five assertions/subtests across four methods.
The lock/receipt and manifest/inventory fault injectors compared lexical paths;
the implementations resolve their roots before filesystem operations. Equivalent
path spellings can therefore miss an injected error. The logs did not capture
the Windows temp-root spelling, so a specific short-name alias is not attested.

A local Python 3.11 reproduction wrapped TemporaryDirectory to return an
existing `alias/..` path. It reproduced all five failures before this correction.
See [the original CI observation](../validation/v0.5-ci-initial.json).

## Decision

Keep noncanonical `alias/..` roots explicitly in the four affected tests and
resolve expected injection targets before installing I/O mocks. Keep the same
exception, cleanup, same-ID retry, exact diagnostic, repeatability and read-only
assertions. Do not normalize inside a patched I/O call, which would add recursive
or unrelated operations at the fault boundary.

Do not change materialize.py, verify_integrity.py, runtime routing or the workflow
to satisfy these tests. Do not skip or weaken failing cases. The test count stays
110; the existing methods now exercise the path-alias regression on every host.

## Verification and consequences

- Before correction: four targeted methods produced the same five local failures.
- After correction, Python 3.11 targeted suites: materialize 9/9; integrity 16
  passed and 3 real-symlink permission skips.
- Full local suite: Python 3.10.0 ran 110 in 33.707s; Python 3.11.9 ran 110 in
  30.087s. Both passed 107, skipped 3, and exited 0. These local skips are not passes.
- Independent read-only review `ci_path_alias_review`, requested Astra/high,
  accepted the two-file test diff with no Critical or Required findings. It
  inspected canonicalization, injection reachability, cleanup and snapshot
  assertions; it did not run suites or review subsequent documentation. The
  native task-name response does not attest effective model/effort identity.
- The original CI ran all three real-symlink tests successfully in all four cells;
  only the Linux cells completed the subsequent evidence/route/integrity gates.
- Sealed v0.2-v0.5 packages and their manifests remain unchanged. Later CI results
  belong under docs/validation, not inside an already sealed package.
- This correction adds no dependency, tool capability, permission or release
  claim. Merge, tags and release remain outside the user's authorization.
