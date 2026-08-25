# Contributing

Thanks for helping improve Adaptive Task Orchestrator. The project values bounded changes, explicit evidence, honest capability claims, and reviewable history.

## Development setup

Requirements:

- Python 3.10 or newer;
- Git;
- no third-party Python packages for the current fixture suite.

Clone the repository and run:

```bash
python -B -m unittest discover \
  -s fixtures/adaptive-task-orchestrator-write-dag/tests -v
```

Then validate both published evidence packages:

```bash
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py \
  --context-root docs/context/adaptive-task-orchestrator-v0.2

python -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py \
  --context-root docs/context/adaptive-task-orchestrator-v0.3
```

## Before changing behavior

The live implementation is under `.agents/skills/adaptive-task-orchestrator/`. Read `SKILL.md` and only the relevant linked policy references before editing it.

For a significant policy, evidence interface, validation claim, public interface, dependency, or architecture change:

1. write or update a specification;
2. add a new ADR rather than rewriting historical rationale;
3. define bounded acceptance checks;
4. add or update tests before accepting the implementation;
5. update both language versions of the README when factual claims change.

## Evidence and fixture rules

- Do not modify accepted files under `docs/context/adaptive-task-orchestrator-v0.2/` or `docs/context/adaptive-task-orchestrator-v0.3/`.
- Never silently rewrite historical contracts, routes, receipts, reports, or integrity manifests.
- Create a new versioned evidence package for new validation work.
- Keep text output LF-normalized and deterministic.
- Never commit generated fixture runs, nested `.git` directories, bytecode, local credentials, or user-owned workspace content.
- Acceptance commands do not grant implicit permission to read everything they import. Declare or isolate transitive reads.
- Parallel writers require non-overlapping write scopes and resource locks. Root integration remains single-owner work.

## Pull requests

Keep changes focused and commits atomic. A pull request should explain:

- the problem and intended behavior;
- files and interfaces in scope;
- preserved behavior and explicit non-goals;
- checks that were run and their results;
- limitations, compatibility assumptions, and remaining uncertainty.

All required checks must pass. Do not weaken, skip, or hard-code around a failing test to manufacture success.

## Documentation synchronization

`README.md` and `README.zh-CN.md` use the same section structure and factual boundary. Commands, paths, field names, status values, versions, and hashes must remain identical. A capability, compatibility, validation, performance, or security claim changed in one language must change in the other in the same pull request.

## Licensing of contributions

By submitting a contribution, you agree that it is licensed under the repository's [Apache License 2.0](LICENSE). Only submit work you have the right to license. Third-party material must retain its required attribution and use a compatible license.
