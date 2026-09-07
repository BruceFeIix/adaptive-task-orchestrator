# Changelog

All notable changes to this project are documented in this file.

The project follows [Semantic Versioning](https://semver.org/) for published
releases. During the experimental `0.x` series, minor versions may refine policy
interfaces; migration notes will identify user-visible changes. Earlier entries
identified as validation milestones predate the standalone public repository and
are not Git release tags.

## [Unreleased]

### Added

- A bounded three-task routing pilot and independently reviewed Skill behavior,
  with explicit requested-only identity and provisional-default caveats. The local
  v0.5 package includes source identities and a self-excluding integrity manifest.
- A versioned Astra-capable registry and runtime-specific policy, plus an opt-in
  standard-library route consistency checker. Exact user pins, capability floors,
  fallback chains, effective evidence, review relationships and concurrency have
  deterministic checks; this is not an executor or authenticity mechanism.
- Routing and registry tests, native CLI golden bytes and six controlled in-memory
  oracle mutations. The current local suite discovers 110 methods: 107 passed and
  three legacy real-symlink permission tests skipped on each Python 3.10/3.11 run.
- A dependency-free `verify_integrity.py` CLI for deterministic, read-only exact
  inventory and SHA-256 verification relative to a trusted self-excluding manifest.
- Mutation coverage for canonical manifest grammar, unsafe paths, incomplete
  inventory, filesystem read errors, reparse points, deterministic findings, and
  CLI status/output behavior; the sealed v0.4 baseline contains 63 tests.

### Fixed

- Canonicalize fault-injection targets while retaining aliased input paths in
  regression tests. The initial Windows CI mismatch and the independently reviewed
  test-only correction are documented in ADR-0012; cleanup and fail-closed
  assertions remain intact.
- Compare unbounded decimal manifest counts without Python-version-dependent
  integer conversion; distinguish valid zero-count mismatches from entry errors.
- Emit LF-terminated CLI bytes on Windows as well as Linux. Regression tests now
  assert complete literal finding details and exact native CLI bytes twice.
- Count skipped tests separately: v0.4 Windows baseline runs discover 63 tests, with 60
  passed and 3 separately reported real-symlink skips. Earlier candidate evidence
  is corrected by ADR-0010 without rewriting historical records.

### Changed

- Configured CI as the exact `ubuntu-latest`/`windows-latest` by Python 3.10/3.11
  matrix, retaining `contents: read`, a ten-minute bound, and no dependency install.
- Replaced direct GNU `sha256sum` use with the portable Python verifier while
  retaining separate v0.2/v0.3 structural validation.
- Synchronized English, Simplified Chinese, and fixture documentation for the new
  command, test count, supported matrix, trust premise, and deferred limitations.

### Security

- Reject unsafe manifest paths, symlinks, Windows reparse points, non-regular
  objects, unlisted files, missing files, read errors, and digest mismatches without
  repairing or rewriting the selected package.

### Known limitations

- SHA-256 consistency is integrity relative to a trusted manifest, not a signature,
  provenance record, trusted timestamp, or authenticity guarantee.
- The verifier assumes a quiescent package and is not a concurrent-adversary
  filesystem sandbox.
- Strict transitive evidence closure, process-crash recovery, third-party OpenAPI
  semantics, and a second end-to-end domain remain deferred.
- The four Windows/Linux Python 3.10/3.11 CI cells subsequently passed 110/110
  tests each, zero skips, including all three real `os.symlink` cases and all nine
  later validation gates. See the [platform receipt](docs/validation/v0.5-ci-platform.json).
  Local permission skips remain historical skips; other platforms are unverified.

## [0.3.0] - 2026-08-25

### Added

- Standalone public repository packaging.
- English and Simplified Chinese project documentation.
- Apache-2.0 licensing and contributor, security, and community guidance.
- GitHub Actions validation across Python 3.10 and 3.11.
- Atomic fixture staging, locking, promotion, and caught-failure cleanup.
- Fail-closed validation for TaskContract, immutable revision, route, and receipt evidence.
- Worker-owned JSONL event streams and single-host overlap summaries.
- A real instrumented two-agent overlap probe.

### Changed

- Separated root verification side effects from root-owned evidence synthesis.
- Hardened Python 3.10 and 3.11 compatibility.

### Security

- Rejected recursive materialization topologies and ambiguous evidence shapes.

## v0.2 validation milestone - 2026-08-25

### Added

- First bounded local write-producing multi-agent DAG validation.
- Revisioned TaskContracts, route records, WorkerReceipts, fault gates, and independent final review.
- Ownership-aware dirty-workspace evidence and transitive-read closure.

## v0.1 policy baseline - 2026-08-24

### Added

- Initial repo-local Codex Skill.
- Task decomposition, capability routing, review, escalation, software-development, and reverse-engineering policies.

### Known limitations

- No real write-producing multi-agent DAG was completed at v0.1.

[Unreleased]: https://github.com/BruceFeIix/adaptive-task-orchestrator/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/BruceFeIix/adaptive-task-orchestrator/releases/tag/v0.3.0
