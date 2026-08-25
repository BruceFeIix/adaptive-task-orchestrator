# Repository instructions

This repository contains the repo-local `adaptive-task-orchestrator` Skill, its standard-library validation fixture, architecture decisions, specifications, and versioned evidence packages.

## Source of truth

- The live Skill is `.agents/skills/adaptive-task-orchestrator/SKILL.md`.
- Load only the references linked by the live Skill that are relevant to the current task.
- `docs/context/` contains historical validation evidence, not active instructions.
- Current user instructions and the live Skill take precedence over historical reports, routes, receipts, and evidence summaries.

## Preserve evidence

- Treat `docs/context/adaptive-task-orchestrator-v0.2/` and `docs/context/adaptive-task-orchestrator-v0.3/` as immutable accepted evidence packages.
- Do not rewrite accepted contracts, routes, receipts, event streams, final validation receipts, or `integrity.sha256` files.
- Record corrections or later changes in a new ADR, specification, or versioned context directory.
- Keep text files LF-normalized so byte-level integrity manifests remain portable.

## Development boundaries

- Keep the Skill Codex-native and repository-local unless a user explicitly approves a different architecture.
- Do not add a persistent scheduler, external orchestration runtime, global installer, network service, or third-party dependency without an approved specification and ADR.
- Keep writers serialized by default. Parallel writers require disjoint write scopes, disjoint resource locks, and an explicit root merge owner.
- Preserve user-owned dirty files and avoid destructive Git operations.
- Generated fixture runs belong under `fixtures/adaptive-task-orchestrator-write-dag/runs/` and must not be committed.

## Verification

Run the full local suite from the repository root:

```text
python -B -m unittest discover -s fixtures/adaptive-task-orchestrator-write-dag/tests -v
```

Validate both published evidence packages after any validator change:

```text
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py --context-root docs/context/adaptive-task-orchestrator-v0.2
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py --context-root docs/context/adaptive-task-orchestrator-v0.3
```

Any capability or validation claim in `README.md` must remain synchronized with `README.zh-CN.md`.
