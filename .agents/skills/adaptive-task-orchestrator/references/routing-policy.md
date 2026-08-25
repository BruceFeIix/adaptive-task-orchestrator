# Capability and Model Routing Policy

Read this reference when assigning a worker or reviewer. Choose the lowest capability likely to satisfy the contract, then apply hard risk floors and runtime availability. The current conversation model is the immutable root identity, not a routable capability alias.

## Preflight the Runtime

Before heterogeneous delegation, determine from the exposed tool contract or host configuration:

- callable child models and supported reasoning efforts;
- whether explicit model and effort overrides are accepted;
- fork/history restrictions for overridden children;
- total and per-parent concurrency limits;
- sandbox, tool, and permission inheritance;
- whether the effective route can be attested.

Intersect the policy registry with the runtime-declared capabilities. Do not infer availability from old documentation or probe by spawning unnecessary agents. If a spawn rejects a model or effort, mark that candidate unavailable for the current run, refresh once, and choose another candidate at the same or higher floor.

If overrides are unavailable, use an inherited child or the root only when the runtime can attest that it meets the node's effective floor. An unattested route is not eligible for high-risk work. Low-risk work may run in the root with deterministic or root checks and a disclosed routing limitation. Otherwise return `NO_ELIGIBLE_RUNTIME` or a policy conflict; never silently weaken the floor or claim that a requested route was honored.

## Stable Capability Aliases

Use aliases in plans so model revisions require changing one registry rather than every task:

| Capability | Typical work | Current-family default when available |
|---|---|---|
| `fast_reader` | bounded extraction, inventory, classification, formatting, repeatable checks | Luna low/medium |
| `general_worker` | large-file reading, ordinary analysis, focused debugging, bounded implementation | Terra medium/high |
| `deep_reasoner` | ambiguous multi-step reasoning, architecture, cross-boundary semantics, difficult diagnosis | Sol high/xhigh |
| `frontier_reviewer` | independent assurance, conflict adjudication, high-impact weak-oracle conclusions | Sol high/xhigh; max or ultra only when supported and justified |

These are defaults, not identity claims. User ceilings, unavailable routes, and future registries may change concrete models while preserving the required capability.

Fallback is monotonic: `fast_reader` may fall upward to `general_worker`, then `deep_reasoner`, then `frontier_reviewer`; it must not fall below the effective floor. An unknown or unranked model cannot satisfy a high-risk floor unless the user explicitly selects it and accepts that limitation.

## Routing Features

Assess each feature on `0..3` and attach reason codes:

- `reasoning_depth`: direct transformation to multi-stage inference;
- `context_breadth`: one bounded artifact to many modules or sources;
- `uncertainty`: well-specified facts to ambiguous competing hypotheses;
- `novelty`: known pattern to unfamiliar mechanism or domain;
- `impact`: cheap reversible error to critical or irreversible harm;
- `verifiability`: weak subjective oracle to deterministic repeatable checks;
- `coupling`: isolated task to cross-component shared state.

A diagnostic score may aid logging:

```text
reasoning_depth + context_breadth + uncertainty + novelty + impact + (3 - verifiability)
```

Low values often suggest `fast_reader`, middle values `general_worker`, and high values `deep_reasoner`. Do not embed universal numeric cutoffs until real evaluations calibrate them, and never let a score override a hard floor.

## Hard Floors

Set at least `deep_reasoner` for nodes that decide, infer, or adjudicate any of the following unless a deterministic tool completely resolves the relevant question:

- authentication, authorization, security boundaries, exploitability, or secrets;
- cryptography, obfuscation, anti-debugging, indirect control flow, or unknown protocols;
- concurrency, distributed state, ABI, kernel, driver, or memory-safety invariants;
- irreversible or public external effects, destructive actions, migrations, or public API compatibility;
- cross-module root cause or global consistency;
- safety-critical or other high-stakes conclusions with weak verification;
- contradictory evidence or a material claim prior workers could not substantiate.

Require `frontier_reviewer` only when impact is high **and** the relevant material claims have a weak oracle, when security or cryptography requires adversarial assurance, when independent workers have an unresolved material conflict, or when the user explicitly requests maximum-quality assurance. A `deep_reasoner` author or a high-risk label alone is not sufficient.

Hard floors constrain analysis quality; they do not authorize actions. Permission checks remain with the root immediately before mutation.

A mechanical descendant does not automatically inherit the highest floor of its parent workflow. Once a risky contract is frozen and the descendant has bounded inputs plus a strong oracle, route that descendant by its own task features. For example, deterministic code generation or parameterized tests for an already accepted migration contract may use `general_worker`, while the compatibility decision and disputed results retain the higher floor.

## Safe Downgrade Conditions

Downgrade to `fast_reader` only when all material conditions hold:

- input and output boundaries are explicit;
- work is narrow, repeatable, and low-impact;
- no hidden cross-component semantics are required;
- acceptance is objective and inexpensive;
- the result is easy for the root or a tool to sample-check;
- failure cannot mutate external or shared state.

Large volume alone is not difficulty. A million mechanical records may suit a fast worker; a twenty-line security check may require the deepest route.

## Quality Profiles

Honor a user-selected profile. Otherwise default to `balanced`:

| Profile | Behavior |
|---|---|
| `frugal` | choose the lowest safe candidate, maximize deterministic checks, sample-review low-risk work, stop early |
| `balanced` | use the normal alias mapping, independently review medium-risk weak-oracle work, escalate on evidence |
| `quality` | raise ambiguous work one tier when useful, increase independent review, favor stronger synthesis |
| `user_pinned` | use the pinned child route only if it satisfies the hard floor and runtime constraints |

No profile may bypass a hard floor or authorization boundary. If a user model/effort ceiling is below the floor, keep the task with a runtime-attested capable root or report a policy conflict; do not silently weaken the route. Each frontier route must record the rule and evidence showing why an ordinary independent reviewer is insufficient.

## Escalation

Classify failure before changing models:

| Trigger | First response |
|---|---|
| missing context | add the named artifact and revise the task contract |
| invalid or ambiguous contract | root clarifies objective, scope, or acceptance |
| failed acceptance or poor reasoning | raise effort, then capability if needed |
| runtime candidate unavailable | refresh preflight and choose a same-or-higher candidate |
| worker disagreement | dispatch a fresh reviewer at least as capable as the strongest worker |
| permission or scope violation | stop the child, isolate its output, return control to root |

Within the same task revision, escalation must be monotonic. Do not retry an unchanged prompt on the same model and effort after a deterministic failure. Default to one capability escalation per node; further attempts require root judgment and an explicit statement of the new information or method expected to change the outcome.
