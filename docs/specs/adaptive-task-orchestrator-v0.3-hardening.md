# Spec: Adaptive Task Orchestrator v0.3 hardening

## Objective

Close the five bounded advisories accepted in v0.2 where local standard-library implementation can provide a strong oracle. This iteration adds recoverable atomic fixture publication, a machine-executable evidence validator, and timestamped disjoint event streams that can prove whether two eligible worker intervals actually overlap.

Success means these capabilities are implemented through RED/GREEN tests, exercised against real project evidence, and accepted by a fresh independent reviewer. It does not turn the Skill into a persistent scheduler or install an external runtime.

## Assumptions

1. The project root remains a non-Git workspace; fixture runs remain nested Git repositories.
2. The completed v0.1 and v0.2 context packages are immutable inputs to v0.3 verification.
3. Python 3 and Git are locally available. No package installation or network access is authorized.
4. Third-party OpenAPI validation and a second domain topology remain later work because they require a dependency or a larger new fixture.
5. Evidence JSON is untrusted boundary input and must fail closed with deterministic diagnostics.

## Tech Stack

- Python 3 standard library only.
- `unittest` for small and medium tests.
- JSON and JSON Lines for evidence and event streams.
- Git CLI only inside temporary or named fixture run directories.
- Markdown ADRs and versioned JSON evidence under `docs/context/adaptive-task-orchestrator-v0.3/`.

## Commands

```powershell
# Full fixture tooling suite.
py -3 -B -m unittest discover -s fixtures/adaptive-task-orchestrator-write-dag/tests -v

# Validate an evidence package.
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py `
  --context-root docs/context/adaptive-task-orchestrator-v0.3

# Record one worker event in its worker-owned stream.
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/event_log.py record `
  --output <worker.jsonl> --task-id <id> --task-revision 1 `
  --span-id <id-r1> --event started

# Validate and summarize multiple streams.
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/event_log.py summarize `
  --require-overlap --output <summary.json> <worker-a.jsonl> <worker-b.jsonl>
```

## Project Structure

```text
fixtures/adaptive-task-orchestrator-write-dag/
    tools/materialize.py          atomic staging, lock, promotion, cleanup
    tools/validate_evidence.py    TaskContract/Route/Receipt validator CLI
    tools/event_log.py            worker-owned JSONL events and overlap summary
    tests/test_materialize.py
    tests/test_validate_evidence.py
    tests/test_event_log.py

docs/decisions/0005-*.md          atomic publication decision
docs/decisions/0006-*.md          evidence-validation and event-stream decision
docs/context/adaptive-task-orchestrator-v0.3/
    contracts/revisions/
    routes/
    receipts/
    evidence/events/
    README.md
    integrity.sha256
```

The named v0.2 run and all v0.1/v0.2 evidence remain read-only.

## Code Style

- Use small `pathlib.Path` functions and explicit dataclasses where a serialized interface benefits.
- Return deterministic, path-qualified diagnostic codes rather than prose-only failures.
- Validate at CLI/file boundaries; internal helpers may rely on validated values.
- Write stable UTF-8 JSON/JSONL with a final newline.
- Use exclusive creation for locks and worker event streams; never overwrite an accepted artifact.
- Keep each event stream owned by exactly one task revision.

Example diagnostic shape:

```json
{
  "code": "CONTRACT_MISSING_FIELD",
  "path": "contracts/T1.json",
  "detail": "classification"
}
```

## Testing Strategy

### Atomic materializer

- RED test injects Git failure after `copytree` and proves no final run, receipt, lock, or staging directory remains.
- RED test proves a pre-existing final run or receipt is never overwritten.
- GREEN tests prove successful runs publish only after the baseline, dirty edit, and receipt are complete.

### Evidence validator

- Unit fixtures cover valid TaskContract, child RouteDecision, root execution record, preflight record, and WorkerReceipt shapes.
- Negative fixtures cover missing fields, invalid enums, unresolved dependencies, current/revision hash mismatch, illegal route state, and receipt revision mismatch.
- Integration validation runs against the completed v0.2 package and the current v0.3 package.

### Event evidence

- Unit tests cover stable timestamps, append-only same-owner streams, duplicate/invalid transitions, missing finishes, and overlap/non-overlap classification.
- Two real bounded agents write separate event streams during one concurrent wave.
- Root merges streams and requires a positive overlap result without claiming performance or scheduler throughput.

## Boundaries

### Always

- Preserve user-owned files and all v0.1/v0.2 evidence bytes.
- Save an immutable TaskContract copy before every dispatch.
- Use disjoint writer scopes and one root merge owner.
- Attribute root verification side effects separately from root-owned evidence synthesis, and declare every shared synthesis output before writing it.
- Run a targeted RED test before implementation and a full suite after integration.
- Treat evidence files as untrusted input and reject ambiguous shapes.

### Ask first

- Adding a third-party dependency or OpenAPI validator.
- Changing the live Skill policy beyond the already accepted ADR-0003/0004 amendments.
- Adding a persistent service, external runtime, or cross-machine fixture.

### Never

- Edit v0.1 snapshots, historical reports, v0.1 manifests, or the completed v0.2 context package.
- Run destructive Git operations against the project root or named v0.2 run.
- Let two workers append to the same event file.
- Silently accept an unknown record type, enum, dependency, transition, or revision mismatch.
- Claim temporal overlap when the closed intervals do not intersect.

## Interfaces

### Materializer publication

The public `materialize_run(template_root, runs_root, run_id)` signature and receipt fields remain backward compatible. A successful return guarantees that the final run and receipt exist. Any caught exception guarantees that no new final run, receipt, staging directory, or lock remains. If receipt publication fails after promotion, the function may remove only the final run proven to have been promoted by that invocation while it still owns the exclusive lock. Process-crash recovery is a separate, explicitly deferred boundary.

### Validator CLI

Exit `0` means every selected artifact passes. Exit `1` means validation findings were emitted as stable JSON. Exit `2` is reserved for CLI usage errors. Record kinds distinguish executable TaskContracts, preflight fixture records, child routes, and root execution records.

### Event stream

Each JSONL record contains `schema_version`, `task_id`, `task_revision`, `span_id`, `event`, `timestamp_utc`, and `timestamp_ns`. A valid span has exactly one `started` event followed by exactly one `finished` event for the same owner. Summary output names each interval and every overlapping pair.

## Success Criteria

- All new tests demonstrate RED before implementation and pass after GREEN.
- The full fixture tooling suite passes with Python bytecode writes disabled.
- Injected failures both before promotion and during post-promotion receipt publication leave no durable artifact, and a same-ID retry succeeds.
- Successful materialization preserves the v0.2 public receipt interface and exact dirty-state behavior.
- The validator rejects each specified malformed fixture with a stable code.
- The validator accepts the completed v0.2 package under its declared historical boundaries and accepts v0.3 current evidence.
- Two real agents produce disjoint valid event streams whose intervals overlap; the persisted summary proves the overlap.
- v0.1 remains 25/25 and 7/7; v0.2 `integrity.sha256` remains 100/100.
- A fresh independent reviewer reports no unresolved Critical or Required finding.
- v0.3 publishes a final receipt and self-excluding case-sensitive Ordinal SHA-256 manifest.

## Non-Goals

- Third-party OpenAPI semantic validation.
- Persistent queues, services, databases, or scheduler processes.
- Performance benchmarking or guarantees about dispatch latency.
- Cross-machine execution or a second reverse-engineering/domain fixture.
- Reconstruction of the eleven unavailable early v0.2 TaskContract bodies.

## Open Questions

None block this approved iteration. Third-party validation and broader topology coverage remain explicit candidates for v0.4.
