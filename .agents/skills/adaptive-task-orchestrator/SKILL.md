---
name: adaptive-task-orchestrator
description: Decompose complex or high-risk work into dependency-aware subagent tasks, route each task to an available model and reasoning tier, enforce evidence and review gates, and consolidate through the current root model. Use for multi-lane research, multi-file development, reverse engineering, or work where heterogeneous models improve quality; skip trivial, tightly coupled, or single-step tasks.
---

# Adaptive Task Orchestrator

Coordinate bounded subagents while keeping the current conversation model as the root manager and final authority.

## Decide Whether to Delegate

Delegate only when at least one of these benefits is material:

- independent read-heavy lanes can run in parallel;
- different subtasks need meaningfully different capabilities or context;
- the task is too broad for one context but can be partitioned cleanly;
- risk or weak verifiability justifies a fresh independent reviewer.

Keep work in the root task when it is small, sequential, tightly coupled, cheaper to do directly, or would create overlapping writers. Do not invent subagents merely to satisfy a pattern.

## Preserve Authority

- Keep the user-selected current model as root. Do not attempt to switch it.
- Root owns scope, permissions, external mutations, plan changes, conflict resolution, and final delivery.
- Delegation never grants authority beyond the user's request. A child must stop before any unapproved destructive, public, paid, credentialed, or otherwise material external action.
- Treat child model and effort overrides as runtime capabilities, not guarantees. Preflight the exposed tool contract and degrade transparently when a requested route is unavailable.

## Orchestrate

1. Classify the task's domain, risk, coupling, context size, uncertainty, and verifiability.
2. If delegating, read [references/task-contract.md](references/task-contract.md), then build the smallest useful dependency graph. Every node must produce a bounded artifact or decision with explicit acceptance checks.
3. Assign non-overlapping read/write scopes. Parallelize independent readers; serialize shared writers unless isolation is proven.
4. Read [references/routing-policy.md](references/routing-policy.md), then route each node by required capability, applying risk floors before cost optimization.
5. Send each worker a self-contained context package. When a model override prevents full-history inheritance, include only the facts and artifacts needed for that node.
6. Accept results only with the required evidence and checks. On failure, add missing context, split the node, or escalate capability; do not blindly repeat the same request on the same route.
7. For high-impact, weakly verifiable, conflicting, or final-assurance work, read [references/review-and-escalation.md](references/review-and-escalation.md) and use a fresh reviewer. Reviewer capability must not be lower than the authoring worker.
8. Root reconciles accepted artifacts, records unresolved uncertainty, runs final checks, and delivers one coherent result.

Workers should return one of `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`, together with claims, evidence, uncertainty, artifacts or changes, checks, contradictions, and a recommended next action.

## Domain Guidance

- For software implementation, debugging, migration, or code review, read [references/domains/software-development.md](references/domains/software-development.md).
- For binary analysis, pseudocode, IDA/Ghidra work, protocol recovery, or vulnerability reasoning, read [references/domains/reverse-engineering.md](references/domains/reverse-engineering.md).
- Do not load a domain reference that does not apply.

## Bound the Search

- Respect the runtime concurrency limit; the root also consumes a slot.
- Default to one delegation level. Do not create recursive swarms unless the user or a more specific policy explicitly requires them.
- Allow at most one capability escalation and two author-review repair loops per node unless the user requests a larger budget.
- Do not retry an unchanged prompt on an unchanged route.
- If orchestration tools are unavailable, low-risk work may execute sequentially in the root with appropriate checks. For a node with a hard capability floor, continue only when the runtime can attest that root meets that floor; otherwise stop that node and report the capability limitation instead of silently weakening it.
