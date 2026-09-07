# Task Contract and Execution Graph

Read this reference after deciding that delegation is worthwhile. Keep the task definition, route decision, and execution receipt separate so future model changes do not alter what the task means.

## Task Contract

Represent each node with the following semantics. YAML is illustrative; use an equivalent structure if the host has another format.

```yaml
id: stable-short-id
revision: 1
objective: one bounded outcome
task_type: research | implementation | verification | review | synthesis
mode: read | write | external_action

dependencies: []
inputs: []
deliverable: path, patch, structured findings, or decision

read_scope: []
write_scope: []
resource_locks: []

context_package:
  authoritative_facts: []
  relevant_artifacts: []
  accepted_upstream_results: []
  user_constraints: []
  permissions: []
  non_goals: []

classification:
  reasoning_depth: 0
  context_breadth: 0
  uncertainty: 0
  novelty: 0
  impact: 0
  verifiability: 3
  coupling: 0

acceptance_checks: []
evidence_required: []
assurance_requirement: deterministic | root_check | independent | independent_adversarial
```

Use a `0..3` scale for classification only to make comparisons and later evaluation possible. Scores are observations, not routing authority. Keep capability preferences, concrete model names, reasoning efforts, and reviewer routes out of this contract; record them in route decisions. The assurance requirement describes the independence and adversarial strength the result needs, not a model tier.

## Contract Quality Rules

A dispatchable node must satisfy all of these:

- The objective has one observable outcome, not an instruction such as “analyze everything.”
- Inputs and scope are bounded enough for a fresh worker to start without reconstructing the parent task.
- The deliverable is named and can be consumed by the root or a downstream node.
- At least one required acceptance check distinguishes completion from a plausible narrative.
- Evidence requirements identify what supports every material claim.
- Dependencies name only results that must exist before dispatch.
- Write scope and external effects are explicit; an empty write scope means read-only.
- Permissions reproduce the user's existing authorization and never enlarge it.

Split a node when it has unrelated deliverables, incompatible tools, a mix of exploration and mutation, or different risk levels. Keep it intact when splitting would force workers to share most of their context or mutable state.

## Route Decision

Create a route decision only after validating the contract and preflighting the runtime:

The sketch below is the legacy structural record shape. Existing records retain
their meaning; do not rewrite historical evidence to fit a newer registry. New
runtime-specific checks use a separate versioned registry and `runtime-routes-v1`
bundle as described in [runtime routing](runtime-routing.md). A legacy
`runtime-schema` source does not by itself establish an execution's effective
model/effort pair.

```yaml
task_id: stable-short-id
task_revision: 1
profile: frugal | balanced | quality | user_pinned
preferred_capability: general_worker
requested_capability: general_worker
route_reason_codes: []
effective_floor: general_worker
floor_reasons: []
selected_model: exact-runtime-model-id
selected_effort: exact-runtime-effort
fork_turns: none | bounded-positive-count | inherited
fallback_chain: []
selection_reason: lowest-safe | preferred | quality-raise | escalation
route_status: requested | observed | inherited-unattested
capability_attested: true | false
attestation_source: runtime-schema | runtime-result | none
floor_satisfied: true | false
```

If the host cannot attest the effective route, label it `requested` or `inherited-unattested`; never present it as observed fact. A high-risk result cannot be accepted as capability-assured from a schema-only or unattested route. Check planned candidate eligibility separately from effective execution evidence. A child cannot change its own task contract, capability floor, route policy, or permissions.

Every route decision references one exact `task_id + task_revision`. Changing only model selection creates a new route decision without changing the task revision. Changing objective, scope, permissions, classification, acceptance, evidence, or assurance requirements increments the task revision and makes prior routes and receipts stale. Any difference between `preferred_capability` and `requested_capability` must be explained by `route_reason_codes` or `floor_reasons`.

## Graph Invariants

Before dispatching a wave, verify:

1. The graph is acyclic and every dependency refers to a real node.
2. A node runs only after all dependencies have accepted receipts.
3. Nodes in the same wave are genuinely independent, not merely named differently.
4. Concurrent nodes do not share a write path, mutable database, service state, resource lock, or external side effect.
5. A downstream node receives the accepted upstream artifact, not an informal paraphrase when the artifact is available.
6. Every required final deliverable is owned by exactly one node or the root synthesis step.
7. The root retains a coordination slot and never exceeds the runtime's actual concurrency limit.

Execute the graph in topological waves. Parallelize read-heavy nodes first. Prefer one merge owner for all shared writes. If isolated worktrees or output directories make writers independent, record that isolation before parallelizing them.

When a dependency is invalidated, a contract is revised, or a permission violation occurs, root stops unfinished descendants, prevents pending writers from starting, releases their locks, and marks their scheduler attempts `STALE` or `CANCELLED`; these are graph lifecycle states, not worker self-reported receipt statuses. Preserve only independently valid read-only evidence. If a writer may have polluted shared state, pause the graph and compare the affected resources with their recorded baseline before any other writer proceeds.

## Context Package

Give a child the smallest sufficient package:

- exact objective and expected deliverable;
- authoritative user requirements and decisions;
- relevant files, symbols, addresses, excerpts, URLs, or accepted upstream artifacts;
- allowed tools and current permission boundary;
- acceptance checks and evidence format;
- explicit non-goals and write scope;
- known uncertainties or competing hypotheses.

Do not rely on the child having seen the full conversation. Do not include unrelated history simply because it is available. When the host cannot combine full-history forking with a model override, use no fork or a bounded recent-turn fork and place required facts in this package.

## Scope and Baseline Closure

An acceptance command does not grant implicit read permission. Before dispatch, include every project resource that the command may load transitively in `read_scope`—for example imported modules, test configuration, fixtures, plugins, generated metadata, or referenced manifests—or isolate the command so it cannot load undeclared project resources. If a receipt discloses an undeclared transitive read, revise the contract and mark the prior route and receipt stale; do not retroactively treat the command itself as authorization.

Before each dispatch, preserve the exact serialized TaskContract under an immutable `task_id + task_revision` identity. A mutable convenience pointer may reference the latest revision, but it must not replace the revisioned evidence. If an older contract body was not preserved and cannot be recovered exactly from authoritative execution records, mark it unavailable and narrow later claims; never reconstruct missing permissions, scopes, or acceptance terms from memory.

In a shared or already-dirty workspace, a global status or diff cannot by itself attribute a changed path to one worker. Record a node-local pre-write identity for every owned mutable artifact and preserve the known shared baseline. At acceptance, combine the worker's exact write operations, owned-path pre/post identities, scoped diff, and the scheduler's accepted ownership history. Treat fixture-wide cleanliness only as a state inventory, not as sole proof of scope compliance.

## Worker Receipt

Require this response shape:

```yaml
status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
task_id: stable-short-id
task_revision: 1
summary: concise outcome
claims:
  - claim: material assertion
    confidence: high | medium | low
    evidence: []
uncertainty: []
artifacts_or_changes: []
resources_accessed: []
external_calls: []
checks:
  - check: command, inspection, or oracle
    result: pass | fail | inconclusive
contradictions: []
recommended_next: accept | supply-context | split | escalate | review | stop
```

`DONE` means every acceptance check passed. `DONE_WITH_CONCERNS` means the requested artifact exists but material uncertainty remains. `NEEDS_CONTEXT` must name the missing input. `BLOCKED` must report the attempted approach and concrete blocking condition.

The root rejects receipts that omit required evidence, claim success despite failed checks, access resources outside the declared read/write scopes, modify resources outside the write scope, make undeclared external calls, or depend on unapproved actions. For a shared or dirty resource, record its baseline identity or user diff before dispatching a writer.
