# ADR-0009: Verify evidence manifests portably

## Status

Accepted

## Date

2026-08-31

## Context

The accepted v0.2 and v0.3 evidence packages use self-excluding SHA-256 manifests.
Their selected TaskContract, route, revision, and receipt records are checked by a
Python standard-library validator, but package integrity is checked in CI with GNU
`sha256sum`. That command is available on the Linux CI runner but is not a portable
project interface for Windows users.

The external command verifies listed file digests, but it does not enforce the
project's full package policy: safe relative paths, exact complete inventory,
self-exclusion, unique entries, portable case behavior, or case-sensitive ordinal
ordering. The repository therefore lacks one reusable fail-closed oracle for the
integrity claim already made by its evidence packages.

## Decision

Add a separate standard-library CLI named `verify_integrity.py` under the approved
v0.4 specification.

The verifier will:

- treat `integrity.sha256` and every serialized path as untrusted input;
- validate the published six-line header and printable-ASCII entry grammar;
- reject unsafe, ambiguous, duplicate, case-colliding, non-ordinal, or self-including
  paths before reading a target;
- use ASCII-byte case-sensitive ordering and an explicit ASCII-lowercase collision
  key rather than host filesystem ordering or Unicode normalization;
- compare the manifest with the package's exact regular-file inventory;
- inventory without following links, and reject symlinks and unsupported filesystem
  objects;
- calculate SHA-256 from file bytes and emit stable path-qualified findings;
- remain read-only and deterministic;
- require a quiescent package for one call instead of claiming protection against
  hostile concurrent filesystem replacement;
- run without third-party dependencies in the four-cell matrix of Windows and Linux
  with Python 3.10 and 3.11;
- leave `validate_evidence.py` and all accepted v0.2/v0.3 bytes unchanged.

CI will call this Python CLI for v0.2, v0.3, and the eventual v0.4 package instead of
calling GNU `sha256sum` directly.

This decision treats the manifest as a trust input. It establishes internal byte
consistency relative to that manifest; it does not establish authorship,
provenance, trusted time, or cryptographic authenticity.

## Alternatives Considered

### Keep GNU `sha256sum --check` as the only verifier

Rejected because it leaves Windows users without the same project-native command
and does not enforce complete-inventory or path-policy invariants.

### Add manifest checks directly to `validate_evidence.py`

Rejected for v0.4 because record semantics and package byte integrity are separate
concerns. A dedicated CLI preserves the current validator's public behavior and
keeps temporary record-only fixtures valid.

### Introduce a strict complete-run evidence profile now

Deferred because attempt identity, scope URI semantics, effect containment, event
binding, and claim-to-evidence references require a larger versioned schema and a
separate product decision. Portable manifest verification is a prerequisite with a
stronger and smaller oracle.

### Add signatures or a transparency service

Deferred because useful authenticity requires a signer identity, key lifecycle,
revocation policy, trusted time, and possibly external infrastructure. A hash file
alone cannot supply those properties.

### Use a third-party manifest or signing library

Rejected for this iteration because the required parsing, path containment,
inventory, and SHA-256 behavior is small and deterministic in the Python standard
library. A new dependency would increase supply-chain and compatibility cost without
improving the bounded integrity claim.

### Validate a second domain before integrity closure

Deferred. A static reverse-engineering fixture could broaden evidence, but every new
versioned package would still depend on portable integrity verification. The
foundation should be completed before adding a weaker-oracle domain topology.

## Consequences

- Windows and Linux users gain one repository-native package-integrity command.
- CI and local verification use the same implementation and stable diagnostics.
- Mutated, incomplete, ambiguous, or path-unsafe packages fail closed.
- Symlink refusal and containment are guaranteed for the quiescent-package model;
  the CLI is not a portable filesystem sandbox against concurrent replacement.
- Existing evidence remains immutable and backward compatible.
- The test suite and public documentation grow, but no runtime dependency is added.
- The project still cannot prove evidence authenticity or that recorded execution
  claims correspond to external reality.
- Strict complete-run closure, crash recovery, and a second domain remain future
  decisions rather than hidden scope in v0.4.
