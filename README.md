# Adaptive Task Orchestrator

English | [简体中文](README.zh-CN.md)

[![CI](https://github.com/BruceFeIix/adaptive-task-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/BruceFeIix/adaptive-task-orchestrator/actions/workflows/ci.yml)

A repo-local Codex Skill for coordinating bounded subagent work with explicit task contracts, dependency-aware execution, scoped ownership, evidence gates, and root-led review.

> **Status: experimental.** The current implementation has evidence-backed local validation in one bounded, standard-library-only, single-host software-development fixture. It is not a production scheduler or a distributed agent runtime.

## Why this exists

Complex agent work becomes unreliable when decomposition, permissions, routing, write ownership, and review are left implicit. Adaptive Task Orchestrator turns those concerns into explicit artifacts and gates while keeping the current Codex conversation as the root authority.

The Skill helps the root agent:

- decide whether delegation is materially useful;
- represent each delegated node as a bounded `TaskContract`;
- execute an acyclic dependency graph in topological waves;
- assign non-overlapping read scopes, write scopes, and resource locks;
- route work by required capability and risk floor instead of model branding alone;
- distinguish requested, observed, and unattested routes;
- require evidence-bearing `WorkerReceipt` records;
- choose deterministic, root, independent, or frontier review gates;
- stop or replan when scope, evidence, permissions, or dependencies are invalid.

## What it is — and what it is not

| It provides | It does not provide |
|---|---|
| A repo-local Codex Skill and policy set | A persistent queue, service, database, or scheduler |
| Task contracts, route decisions, receipts, and review gates | A replacement for Codex's own tools, permissions, or sandbox |
| Dependency-aware orchestration and write-ownership rules | Automatic permission expansion or unbounded autonomous delegation |
| Capability-aware routing with fail-closed risk floors | Guaranteed model availability or route attestation |
| Standard-library fixture and evidence-validation tools | Production, throughput, latency, or cross-machine guarantees |
| Single-host instrumented overlap evidence | Cross-host clock correctness or distributed tracing |

Codex remains the execution environment. The current conversation model remains responsible for scope, authorization, conflict resolution, external actions, integration, and final delivery.

## When to use it

Use the Skill when at least one benefit is material:

- several independent read-heavy lanes can run in parallel;
- subtasks require different capabilities or context packages;
- a broad task can be split into bounded, dependency-aware outputs;
- shared writes require explicit ownership and ordering;
- risk or weak verifiability warrants a fresh reviewer;
- the result needs an auditable evidence trail.

Keep the work in the root task when it is small, sequential, tightly coupled, or cheaper to verify directly. The Skill explicitly rejects delegation for its own sake.

## Use in a repository

### Requirements

- A Codex environment that supports repository-local Skills.
- Multi-agent tools when delegation is needed. The Skill can still guide low-risk root-only work when delegation is unavailable.
- Python 3 and Git only if you want to run the included validation fixture.

The fixture has no third-party Python dependencies.

### Install the Skill locally

Copy this directory into the repository where Codex will run:

```text
.agents/skills/adaptive-task-orchestrator/
```

The directory must contain `SKILL.md`, `agents/openai.yaml`, and the referenced policy files. Do not install an external runtime or broaden repository permissions merely to use the Skill.

### Invoke it

Explicit invocation:

```text
$adaptive-task-orchestrator
```

Example request:

```text
Use $adaptive-task-orchestrator to plan this API migration.
Keep the shared contract under one owner, dispatch independent consumers only
after the contract is accepted, and require evidence-backed receipts plus a
fresh integration review.
```

The Skill also permits implicit invocation for work that clearly benefits from dependency-aware delegation.

## How orchestration works

```text
Classify the work
        ↓
Decide whether delegation is worthwhile
        ↓
Create bounded TaskContracts
        ↓
Validate dependencies, scopes, locks, and permissions
        ↓
Preflight routes and record requested vs. observed status
        ↓
Dispatch topological waves with non-overlapping ownership
        ↓
Verify WorkerReceipts and deterministic checks
        ↓
Root integration and, when required, fresh independent review
        ↓
Accept, revise, replan, or stop
```

### Task contract

A task definition is kept separate from its model route and execution receipt. The full contract shape is documented in [the TaskContract reference](.agents/skills/adaptive-task-orchestrator/references/task-contract.md).

Illustrative excerpt:

```yaml
id: contract-migration
revision: 1
objective: Add a compatibility field while preserving legacy input.
task_type: implementation
mode: write
dependencies: []
read_scope:
  - contract/openapi.json
  - tests/test_migration.py
write_scope:
  - contract/openapi.json
resource_locks:
  - compatibility-contract
acceptance_checks:
  - contract tests pass
evidence_required:
  - scoped diff
  - test result
assurance_requirement: independent
```

This is a policy artifact, not an external scheduler configuration or public service API. If an acceptance command imports additional project resources, those transitive reads must be declared or isolated.

### Routing

Plans use stable capability aliases such as `fast_reader`, `general_worker`, `deep_reasoner`, and `frontier_reviewer`. The runtime must be preflighted before binding an alias to an actual model and reasoning effort.

An unattested route is never presented as observed. High-risk floors constrain analysis quality but do not grant additional permissions. See the [routing policy](.agents/skills/adaptive-task-orchestrator/references/routing-policy.md).

### Evidence and review

Workers return structured claims, evidence, checks, uncertainty, accessed resources, external calls, and a recommended next action. The root verifies this receipt instead of accepting a success narrative at face value.

Review strength is proportional to impact and oracle quality:

- `deterministic`: a reliable executable or structural check;
- `root_check`: bounded evidence that the root can inspect directly;
- `independent`: fresh-context specification and quality review;
- `frontier`: adversarial assurance for high-impact weak-oracle, security, cryptography, or unresolved-conflict work.

See [review and escalation](.agents/skills/adaptive-task-orchestrator/references/review-and-escalation.md).

## Repository layout

```text
.agents/skills/adaptive-task-orchestrator/  live Skill and policy references
fixtures/adaptive-task-orchestrator-write-dag/
                                            local validation tools and tests
docs/decisions/                             architecture decision records
docs/specs/                                 approved validation scopes
docs/context/                               immutable versioned evidence packages
```

The live Skill is authoritative for current behavior. Versioned context packages are validation evidence, not active instructions. See [the evidence-package guide](docs/context/README.md).

## Validate locally

Run from the repository root.

### Full fixture tooling suite

```bash
python -B -m unittest discover \
  -s fixtures/adaptive-task-orchestrator-write-dag/tests -v
```

On Windows with the Python launcher:

```powershell
py -3 -B -m unittest discover `
  -s fixtures/adaptive-task-orchestrator-write-dag/tests -v
```

The current suite contains 44 tests covering atomic materialization, evidence validation, and worker-owned event streams.

### Validate the published evidence packages

```bash
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py \
  --context-root docs/context/adaptive-task-orchestrator-v0.2

python -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py \
  --context-root docs/context/adaptive-task-orchestrator-v0.3
```

Exit `0` means all selected TaskContract, route, immutable-revision, and receipt records passed. The validator does not prove signatures, artifact authenticity, arbitrary domain JSON correctness, OpenAPI semantics, or runtime model availability.

### Materialize a new fixture run

This command writes a self-contained nested Git fixture. Use a unique run ID and never target the project root:

```bash
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/materialize.py \
  --run-id my-local-run
```

Generated runs are intentionally ignored by the public repository. The materializer refuses to overwrite an existing run or baseline receipt.

## Validation status

| Milestone | Evidence-backed result | Boundary |
|---|---|---|
| v0.1 | Initial Codex-native policy baseline | No real write-producing multi-agent DAG was completed at v0.1 |
| v0.2 | One bounded local nested-Git write-producing software-development DAG | No persistent scheduler, production workload, cross-machine coordination, or universal route validation |
| v0.3 | Atomic fixture publication, fail-closed evidence validation, worker-owned event streams, and one real two-agent overlap probe | Single-host local evidence only; no throughput, crash recovery, signature, or cross-host claim |

The published v0.3 receipt records 44/44 fixture tests on local Python 3.10 and 3.11 runtimes, valid v0.2/v0.3 evidence packages, and an independent review with no unresolved Critical or Required findings. The overall result remains `ACCEPT_WITH_CAVEATS`, not production certification.

Detailed evidence:

- [v0.2 write-DAG specification](docs/specs/adaptive-task-orchestrator-v0.2-write-dag.md)
- [v0.2 evidence package](docs/context/adaptive-task-orchestrator-v0.2/README.md)
- [v0.3 hardening specification](docs/specs/adaptive-task-orchestrator-v0.3-hardening.md)
- [v0.3 evidence package](docs/context/adaptive-task-orchestrator-v0.3/README.md)
- [architecture decisions](docs/decisions/README.md)

## Known limitations

The following remain intentionally unclaimed or deferred:

- persistent scheduling, queues, databases, services, dashboards, or web APIs;
- production workload readiness or performance guarantees;
- cross-machine execution and cross-host clock correctness;
- process-crash recovery, stale-lock detection, and stale-lock reclamation;
- cryptographic signatures, trusted timestamps, or artifact authenticity;
- third-party OpenAPI semantic validation;
- proof that every runtime model, effort, capability tier, or domain topology works;
- a second end-to-end domain fixture, including reverse engineering;
- exact reconstruction of eleven early v0.2 contract bodies that were not preserved at the time.

## Contributing and security

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing the live Skill, evidence schemas, fixtures, or bilingual capability claims.

Please report vulnerabilities privately according to [SECURITY.md](SECURITY.md). Do not put credentials, private repository data, or unsanitized agent evidence in a public issue.

Community participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

Licensed under the [Apache License 2.0](LICENSE).
