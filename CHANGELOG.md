# Changelog

All notable changes to this project are documented in this file.

The project follows [Semantic Versioning](https://semver.org/) for published releases. During the experimental `0.x` series, minor versions may refine policy interfaces; migration notes will identify user-visible changes.

## [Unreleased]

### Added

- Standalone public repository packaging.
- English and Simplified Chinese project documentation.
- Apache-2.0 licensing and contributor, security, and community guidance.
- GitHub Actions validation across Python 3.10 and 3.11.

## [0.3.0] - 2026-08-25

### Added

- Atomic fixture staging, locking, promotion, and caught-failure cleanup.
- Fail-closed validation for TaskContract, immutable revision, route, and receipt evidence.
- Worker-owned JSONL event streams and single-host overlap summaries.
- A real instrumented two-agent overlap probe.

### Changed

- Separated root verification side effects from root-owned evidence synthesis.
- Hardened Python 3.10 and 3.11 compatibility.

### Security

- Rejected recursive materialization topologies and ambiguous evidence shapes.

## [0.2.0] - 2026-08-25

### Added

- First bounded local write-producing multi-agent DAG validation.
- Revisioned TaskContracts, route records, WorkerReceipts, fault gates, and independent final review.
- Ownership-aware dirty-workspace evidence and transitive-read closure.

## [0.1.0] - 2026-08-24

### Added

- Initial repo-local Codex Skill.
- Task decomposition, capability routing, review, escalation, software-development, and reverse-engineering policies.

### Known limitations

- No real write-producing multi-agent DAG was completed at v0.1.

[Unreleased]: https://github.com/BruceFeIix/adaptive-task-orchestrator/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/BruceFeIix/adaptive-task-orchestrator/releases/tag/v0.3.0
[0.2.0]: https://github.com/BruceFeIix/adaptive-task-orchestrator/releases/tag/v0.2.0
[0.1.0]: https://github.com/BruceFeIix/adaptive-task-orchestrator/releases/tag/v0.1.0
