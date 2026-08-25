# Spec: Adaptive Task Orchestrator v0.2 write-producing DAG validation

## Objective

Build and execute an isolated, recoverable software-development fixture that proves whether the repo-local `adaptive-task-orchestrator` can safely run a real write-producing multi-agent DAG. The validation must cover a shared compatibility contract, one generated-output owner, two independent downstream consumers, a pre-existing user dirty edit, deterministic tests, runtime route evidence, failure handling, and independent review.

Success means the project can make a bounded evidence-backed claim about actual execution reliability. It does not mean the Skill is a deterministic scheduler, globally installed plugin, or production service.

## Assumptions

1. The project root remains a non-Git workspace.
2. The fixture may create its own nested Git repository strictly inside a named run directory.
3. Python 3 and Git are available locally; no network downloads are required.
4. The compatibility exercise migrates a user field from `name` toward `displayName` while preserving the legacy field.
5. The approved scope includes writing fixture files and dispatching bounded child agents, but excludes global Skill installation and external orchestration runtimes.

## Tech Stack

- Python 3 standard library for materialization, generation, consumers, and tests.
- JSON-form OpenAPI 3.1 document to avoid a YAML parser dependency.
- Git CLI only inside the generated fixture run directory.
- Codex native subagents for schema authoring, review, code generation, and isolated consumer implementation.
- Markdown and JSON evidence files under a new v0.2 context directory.

No third-party Python packages, package managers, network services, databases, or external agent frameworks are permitted.

## Commands

```powershell
# Test the fixture materializer and structural policy checks.
py -3 -m unittest discover -s fixtures/adaptive-task-orchestrator-write-dag/tests -v

# Create the named, non-overwriting fixture run.
py -3 fixtures/adaptive-task-orchestrator-write-dag/tools/materialize.py --run-id 20260824-v0.2.0

# Run the generated fixture's contract and integration tests.
py -3 -m unittest discover -s fixtures/adaptive-task-orchestrator-write-dag/runs/20260824-v0.2.0/tests -v

# Inspect the fixture-local dirty state without changing it.
git -C fixtures/adaptive-task-orchestrator-write-dag/runs/20260824-v0.2.0 status --short
```

## Project Structure

```text
docs/decisions/0002-*.md
    Additive fingerprint errata; does not alter v0.1.

docs/specs/adaptive-task-orchestrator-v0.2-write-dag.md
    Approved requirements and acceptance boundary.

tasks/plan.md
tasks/todo.md
    Dependency-aware implementation plan and live checklist.

fixtures/adaptive-task-orchestrator-write-dag/
    README.md
    template/
        contract/openapi.json
        generated/user_fields.py
        consumers/server/user_adapter.py
        consumers/client/user_adapter.py
        tests/test_baseline.py
        user-notes.md
    tools/materialize.py
    tests/test_materialize.py
    runs/<run-id>/
        Fixture-local Git repository and real DAG outputs.

docs/context/adaptive-task-orchestrator-v0.2/
    README.md
    contracts/
    routes/
    receipts/
    evidence/
    integrity.sha256
```

The exact evidence inventory may grow only when an acceptance check requires it. The v0.1 context directory is forbidden to writers.

## Code Style

- Use explicit `pathlib.Path` paths and small standard-library functions.
- Fail closed: existing run directories are never overwritten.
- Use JSON with stable key ordering and a final newline for generated artifacts.
- Tests use `unittest`, descriptive behavior names, and state assertions.
- Commands report concise deterministic output and non-zero exit codes on failure.

Example:

```python
def require_new_run(run_root: Path) -> None:
    if run_root.exists():
        raise FileExistsError(f"refusing to overwrite existing run: {run_root}")
```

## Testing Strategy

### Small tests

- Validate run identifiers and path containment.
- Verify materialization refuses overwrite.
- Verify expected template inventory.
- Verify fingerprint canonicalization when used by evidence tooling.

### Medium integration tests

- Materialize a fixture in a temporary directory.
- Initialize its local Git baseline.
- Apply the pre-existing user edit after the baseline commit.
- Verify `git status --short` reports only the intended dirty edit before DAG work.
- Verify the generated artifact matches the shared contract.
- Verify both consumers accept legacy and current payloads.

### End-to-end DAG validation

- Run real bounded writers against one named fixture run.
- Preserve route decisions, worker receipts, diffs, checks, and review findings.
- Run the complete fixture test suite and final dirty-state audit from the root.

### Fault injection

- Reject overlapping writer scopes before dispatch.
- Return `NEEDS_CONTEXT` for a deliberately omitted required input, then revise the contract before retrying.
- Mark an obsolete receipt stale when its task revision changes.
- Exercise one bounded author-review repair cycle with a deterministic regression test.
- Record an unavailable or unattested route as requested rather than observed.

## Boundaries

### Always

- Preserve all existing user files and v0.1 artifacts.
- Record a baseline identity before any child writer starts.
- Give each writer an explicit, non-overlapping write scope.
- Keep shared schema and generated output under one owner each.
- Run targeted checks after each increment and root integration checks after join.
- Treat child claims as evidence to verify, not automatic acceptance.

### Conditional

- Modify the live Skill only after a reproduced acceptance failure and a written review finding demonstrate that prose policy is insufficient or wrong.
- Add a deterministic plan validator or persistent trace only if observed failure or reconstruction cost justifies it.
- Use a stronger reviewer only when the routing hard floor or unresolved evidence requires it.

### Never

- Modify `docs/context/adaptive-task-orchestrator-v0.1/snapshot/`.
- Rewrite verbatim historical reports or existing v0.1 hash manifests.
- Run destructive Git operations against `F:\Projects\CodexProjects`.
- Install the Skill globally, add an external orchestration runtime, or broaden permissions.
- Allow concurrent writers to share a path, generated directory, Git index, or mutable service state.
- Claim end-to-end validation when any required receipt or deterministic check is missing.

## DAG and Ownership

```text
T0 baseline inventory (root, read)
  -> T1 compatibility contract + RED tests (root, write)
  -> T2 shared OpenAPI writer (deep_reasoner, write)
  -> T3 independent schema reviewer (deep_reasoner, read)
  -> T4 generated output owner (general_worker, write)
  -> [T5 server consumer, T6 client consumer] (general_worker, disjoint writes)
  -> T7 integration and dirty-state audit (root, read)
  -> T8 independent final review (fresh reviewer, read)
```

Root is the sole merge and evidence owner. T5 and T6 may run concurrently only because they own separate consumer directories and receive the same accepted upstream contract and generated artifact.

## Success Criteria

- The v0.1 archive remains 25/25 and snapshot remains 7/7.
- The fingerprint errata reproduces both known bundle values without editing history.
- Materializer tests demonstrate non-overwrite and exact dirty-state creation.
- A real child writes the shared contract and a different child independently reviews it.
- A single child owns generated output.
- Two child writers modify separate consumer directories without overlap.
- All fixture contract and integration tests pass after the DAG.
- The pre-existing `user-notes.md` dirty edit remains byte-for-byte unchanged.
- Every dispatched task has a contract, route decision, bounded receipt, and acceptance evidence.
- Fault gates demonstrate conflict prevention, `NEEDS_CONTEXT`, stale revision handling, and one repair cycle.
- A fresh reviewer reports no unresolved Critical or Required findings.
- A v0.2 evidence directory and SHA-256 integrity manifest allow a future task to reproduce the conclusion.

## Non-Goals

- Global installation or marketplace packaging.
- A persistent queue, database, web UI, service API, or external scheduler.
- Cross-machine orchestration.
- Reverse-engineering fixture execution in this iteration.
- Universal numeric routing thresholds.
- Performance benchmarking beyond recording basic elapsed time and agent count.

## Open Questions

No blocking product decisions remain for this approved iteration. Findings may trigger a bounded live-Skill correction; otherwise the live v0.1 Skill remains unchanged and v0.2 consists of validation evidence plus fixture infrastructure.
