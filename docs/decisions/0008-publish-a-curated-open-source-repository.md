# ADR-0008: Publish a curated standalone open-source repository

## Status

Accepted

## Date

2026-08-25

## Context

The implementation originated in a larger non-Git workspace that also preserved private task transcripts, local paths, operational identifiers, temporary planning files, generated fixture runs, Python caches, and immutable historical evidence.

Publishing the whole workspace would expose irrelevant local provenance and nested Git state. Publishing only the seven Skill files would omit the executable fixture, tests, design rationale, and accepted v0.2/v0.3 evidence needed to understand the project's validation boundary.

The public repository also needs a license and portable line-ending policy before its first commit. Byte-level evidence manifests require deterministic LF text across platforms.

## Decision

Publish `BruceFeIix/adaptive-task-orchestrator` as a curated standalone repository under the Apache License 2.0.

Include:

- the live repository-local Skill and references;
- the standard-library write-DAG template, tools, and tests;
- ADR-0001 through ADR-0007 and the v0.2/v0.3 specifications;
- the complete accepted v0.2 and v0.3 context packages;
- bilingual project documentation and community governance files;
- an LF-enforcing `.gitattributes` file and a Python 3.10/3.11 CI gate.

Exclude:

- the original v0.1 transcript and verbatim private archive;
- workspace-local task plans and handoff instructions;
- materialized fixture runs and nested `.git` metadata;
- absolute-path baseline receipts derived from local runs;
- Python caches, credentials, environment files, locks, and logs.

The public repository records why v0.1 was omitted and preserves the material fingerprint erratum without altering the private immutable baseline. Historical v0.2/v0.3 package bytes remain unchanged.

## Alternatives considered

### Publish the complete original workspace

Rejected because it would mix active source with private transcripts, local paths, temporary planning state, caches, generated runs, and nested Git metadata.

### Publish only the live Skill

Rejected because users and reviewers would lack executable validation tools, tests, architecture decisions, specifications, and evidence for the stated boundaries.

### Rewrite historical evidence for portability

Rejected because modifying accepted evidence would destroy provenance and invalidate published hashes. New explanatory documentation is used instead.

### MIT License

Considered as a simpler permissive license. Apache-2.0 was selected because its explicit patent grant is a better long-term fit for an orchestration policy and tooling project that may gain additional implementations.

## Consequences

- The public repository is useful without exposing unnecessary task-internal provenance.
- Public users can run the 44-test suite and validate the v0.2/v0.3 evidence packages.
- Public users cannot independently recompute the omitted private v0.1 archive checks; README and ADR language must not imply otherwise.
- Generated runs remain local and ignored. Reproducible source and evidence remain version controlled.
- Future accepted evidence belongs in a new versioned context directory rather than edits to v0.2 or v0.3.
- Contributions are licensed under Apache-2.0 without a separate CLA unless a later ADR changes that policy.
