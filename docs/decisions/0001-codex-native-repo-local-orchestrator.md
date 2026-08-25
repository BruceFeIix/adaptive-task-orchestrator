# ADR-0001: Use a Codex-native repo-local orchestration Skill

## Status

Accepted for v0.1

## Date

2026-08-24

## Context

The requested capability must decompose varied work, keep the user-selected conversation model as root, route bounded subtasks to suitable Sol/Terra/Luna capability and reasoning tiers, handle dependency-aware concurrency, apply domain-specific evidence rules, escalate failures, and consolidate through independent review.

The investigation found reusable pieces but no existing project that satisfied all of those requirements inside the current Codex runtime without duplicating its task, permission, sandbox, and UI mechanisms.

## Decision

Build `adaptive-task-orchestrator` as a repo-local Codex Skill with progressive disclosure:

- `SKILL.md` contains only delegation criteria, root authority, the orchestration loop, domain routing, and bounded stopping rules.
- Supporting references define the task contract, runtime route decision, worker receipt, capability policy, review gates, and software/reverse-engineering domain rules.
- The current conversation model remains root and final authority.
- Plans use stable capability aliases; concrete model IDs and effort are selected only after runtime preflight.
- High-risk capability floors fail closed when effective capability cannot be attested.
- Shared writers are serialized unless isolation and ownership are proven.
- Material claims require evidence, and high-impact weak-oracle results receive fresh independent review.

## Alternatives considered

### Install Superpowers unchanged

Rejected as the complete solution. Its worker and two-stage review structure is valuable, but it is predominantly software-development-oriented, uses broad capability labels, and lacks the requested reverse-engineering evidence model and Codex-specific Sol/Terra/Luna routing policy.

### Depend directly on Fable5-mode

Rejected as a runtime dependency. Its task cards, objective verification before downgrading, and failure escalation were adopted as design ideas, but the project was young and oriented toward a different agent environment.

### Embed vLLM Semantic Router

Deferred. Its workflow graph, fan-out, trace, and policy ideas are useful, but installing the full router would duplicate capabilities already supplied by Codex and add gateway/model-service operations.

### Use LangGraph or Microsoft Agent Framework immediately

Deferred until persistent queues, hard budgets, checkpoints, cross-machine execution, multi-provider routing, or a service API justify an external runtime.

### Use a request-level router such as RouteLLM or LiteLLM alone

Rejected as insufficient. These systems can choose a model for a whole request or optimize deployment routing, but do not supply the requested semantic task DAG, domain evidence contracts, or root-led review flow.

## Consequences

- v0.1 remains lightweight and discoverable by Codex without global installation.
- The design can evolve when model names change because tasks refer to capabilities rather than embedding permanent model IDs.
- Policy execution is partly model-driven; it is not yet a deterministic scheduler with durable checkpoints.
- Real behavior must be calibrated with representative tasks, not assumed correct from prose or structural validation alone.
- The first baseline consists of seven files and no executable validator script.
- If operational requirements grow beyond one Codex task, a plugin or external runner can be introduced later without discarding the task/evidence contracts.
