# Review, Conflict Resolution, and Stopping Rules

Read this reference for high-impact work, weakly verifiable outputs, conflicting receipts, final assurance, or an author-review repair loop.

## Select the Smallest Sufficient Gate

| Gate | Use when | Required action |
|---|---|---|
| `deterministic` | low-risk output has a reliable executable or structural oracle | run the check and retain its result |
| `root_check` | bounded result is easy for the root to inspect or sample | inspect evidence and repeat the critical check |
| `independent` | medium risk, non-trivial judgment, or implementation needs separation of duties | fresh worker reviews requirements, artifact, and evidence |
| `frontier` | high impact with weak oracle, security/crypto, unresolved conflict, or maximum-quality request | strongest allowed fresh reviewer performs adversarial evidence review |

Do not spend a frontier review on every mechanical task. A high-risk artifact with a strong deterministic oracle normally needs one fresh independent reviewer at least as capable as its author plus root integration checks, not an automatic frontier review. Use frontier only for the conditions in the routing policy. Conversely, passing tests do not replace review when the tests cannot observe the relevant failure mode.

## Reviewer Independence

The reviewer must not be the authoring child. Give the reviewer:

- the original task contract and user constraints;
- the produced artifact or patch;
- evidence locations and check results;
- known uncertainties and upstream assumptions.

For high-risk or contradiction reviews, omit the author's persuasive narrative when raw artifacts and evidence are sufficient. Ask the reviewer to reconstruct the decision, search for counterexamples, and identify unsupported claims. Require concise findings and evidence, not hidden reasoning traces.

Reviewer capability must be at least the author's capability. Prefer a different model family or fresh context when available and worth the extra cost. If the runtime cannot provide model diversity, disclose that limitation instead of describing the review as cross-model.

Specification, quality, and integration are review concerns, not automatically three reviewer agents. One independent reviewer may cover specification and quality for the same artifact and evidence package; root normally owns deterministic integration. Default to at most one frontier review per final artifact, adding another only after a material conflict or a changed artifact requires re-review.

## Review Outcome

Use one of these decisions:

```yaml
decision: ACCEPT | ACCEPT_WITH_CAVEATS | REVISE | REPLAN | STOP
critical_findings: []
evidence_checked: []
failed_or_missing_checks: []
residual_risk: []
required_next_action: none | author_fix | new_task | root_decision | user_input
```

- `ACCEPT`: the contract is met and material claims are supported.
- `ACCEPT_WITH_CAVEATS`: the result is useful, with explicitly bounded residual uncertainty.
- `REVISE`: the plan remains sound and a bounded correction can satisfy it.
- `REPLAN`: assumptions, dependencies, or scope were wrong; do not patch around the plan.
- `STOP`: further work needs new authority, unavailable evidence, unsafe action, or a user decision.

## Resolve Conflicts by Evidence

Never merge conclusions by majority vote. For each disputed claim:

1. normalize terminology and confirm workers addressed the same question;
2. compare authoritative evidence and reproduce decisive checks;
3. identify whether disagreement is factual, interpretive, or caused by different inputs;
4. dispatch a narrowly scoped adjudication task only if existing evidence cannot decide;
5. preserve unresolved alternatives and their consequences in the root result.

If a conflict exposes a missing dependency, update the graph and invalidate only downstream receipts that relied on it. A weaker worker's counterexample is not overruled merely because a stronger model produced the original claim.

## Repair Loop

Use no more than two author-review repair cycles by default:

1. Reviewer returns bounded actionable findings.
2. Root assigns each finding to one owner and preserves non-overlapping write scope.
3. Author fixes only rejected contract items and reruns relevant checks.
4. Reviewer verifies the changed artifact and regression evidence.

After two failed cycles, split the node, change the approach or capability, or report the blocking condition. A third cycle is justified only when the root can state the new information or method expected to change the outcome.

## Stop and Return to the User

Stop before proceeding when completion requires:

- authorization outside the user's request;
- a destructive, public, paid, credentialed, or irreversible action not already approved;
- a product, risk, or scope choice that materially changes the result;
- unavailable evidence that cannot safely be reconstructed;
- exceeding an explicit cost, time, model, or effort ceiling.

When stopping, report accepted facts, rejected or uncertain claims, checks already performed, the exact blocker, and the smallest decision or artifact needed to resume.
