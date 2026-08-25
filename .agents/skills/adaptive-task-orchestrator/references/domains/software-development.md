# Software Development Domain Policy

Read this reference for implementation, debugging, refactoring, migration, code review, or test work. Apply repository-local instructions and user constraints before this general policy.

## Establish the Working State

Before planning writers, have the root or one read-only scout establish:

- repository instructions and applicable skills;
- current branch or worktree state and existing user changes;
- build, test, type-check, lint, and formatting entrypoints;
- public interfaces, generated files, schemas, migrations, and shared configuration;
- files or resources that cannot safely receive concurrent writes.

Treat uncommitted work as user-owned. Never use destructive Git operations to simplify integration. Do not ask a worker to modify files until its write scope and verification command are known.

## Decompose by Outcome and Ownership

Prefer vertical, independently testable slices over layers that leave the repository unusable. Good nodes produce one of:

- a verified reproduction and root-cause report;
- an interface or schema decision consumed by downstream tasks;
- one bounded implementation with targeted tests;
- a deterministic test, build, or static-analysis receipt;
- a specification, quality, security, or integration review.

Do not mechanically create one worker per file. Group files that implement one behavior, and split when behaviors, risk levels, or write ownership differ.

Exploration, documentation lookup, log analysis, test reproduction, and repository mapping are usually read-only and can run in parallel. Implementation is serial by default. Concurrent writers require disjoint write scopes plus isolated worktrees or output directories and an explicit merge owner.

Shared contracts are dependency roots. Finalize and verify an API schema, database migration contract, generated-code source, lockfile policy, or compatibility rule before dispatching dependent consumers. Do not allow multiple workers to reinterpret the same unsettled contract independently.

## Route by Work, Not Job Title

| Work | Default capability | Raise when |
|---|---|---|
| file inventory, search, logs, test-output classification | `fast_reader` | results require cross-module interpretation |
| documentation and large-file reading | `fast_reader` or `general_worker` | sources conflict or behavior must be inferred |
| clear mechanical edit with strong tests | `fast_reader` or `general_worker` | public behavior or compatibility changes |
| ordinary bug fix or bounded feature | `general_worker` | root cause crosses modules or the specification is ambiguous |
| architecture, concurrency, auth, migration, public API | `deep_reasoner` | impact is high and verification is weak |
| security, critical compatibility, final disputed conclusion | `frontier_reviewer` | always use independent evidence review |

Do not route all coding to the strongest model. Do not route a short auth, concurrency, or migration change to a fast model merely because the diff is small.

## Implementation Contract

An implementation node should state:

- intended behavior and preserved behavior;
- owned files and forbidden files;
- relevant interface or upstream artifact;
- targeted test or other acceptance oracle;
- expected compatibility and error behavior;
- whether adding or changing tests is in scope;
- commands the worker must run before returning.

Workers must not weaken, skip, delete, or hard-code around tests to manufacture success. A failing check remains a failure unless the task explicitly changes that expected behavior and the root accepts the new contract.

## Review Gates

Use separate concerns rather than one vague “looks good” review:

1. **Specification review:** Does the change implement the requested behavior, preserve stated constraints, and avoid out-of-scope work?
2. **Quality review:** Are the design, failure handling, maintainability, security, and tests appropriate for the risk?
3. **Integration review:** After merging accepted slices, do full relevant tests/builds pass and do interfaces remain coherent?

Low-risk mechanical changes with strong deterministic checks may combine root and integration review. High-risk changes should use a fresh reviewer who did not author the patch, and reviewer capability must be no lower than the author. A high-impact change with strong contract tests normally uses one independent reviewer plus root integration; use a frontier reviewer only for weak-oracle material claims, security/cryptography, unresolved conflict, or an explicit maximum-quality request. One reviewer may cover specification and quality for the same artifact.

## Evidence and Completion

An accepted coding receipt includes:

- exact changed paths or patch artifact;
- concise root cause or implementation rationale;
- targeted checks with exit status and meaningful output;
- broader regression checks appropriate to the change;
- remaining warnings, untested paths, and compatibility assumptions;
- confirmation that no user changes or out-of-scope files were overwritten.

Root inspects the integrated diff and runs final checks after all writing tasks join. A child saying “tests pass” is evidence to verify, not automatic acceptance.

Replan when discovery reveals shared state, an invalid interface assumption, a larger blast radius, or a new user constraint. Preserve still-valid artifacts rather than restarting the whole graph.
