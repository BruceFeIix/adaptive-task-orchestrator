# Runtime-specific routing and evidence

Candidate reference for independent policy review. This is not active Skill policy
until accepted and copied into the live Skill's references directory.

Read this reference when binding model aliases to a current host or checking route
evidence. Keep TaskContracts separate from concrete model choices. Registry ranks
and profile defaults are versioned project policy, not benchmark results.

## Preflight and candidate selection

1. Read `model-registry.json` and the current exposed tool contract. Identify the
   exact surface: a Codex native tool and the Responses API are different surfaces.
2. Record a fresh snapshot with run, host, snapshot and source identities; exact
   models/efforts; override/history restrictions; configuration-override knowledge;
   effective-configuration reporting; and the concurrency counting convention.
3. Intersect the registry's surface support with the snapshot. Do not infer model
   rank from names, infer availability from old receipts, or spawn just to probe.
4. Select a candidate satisfying both the task minimum and requested capability.
   Stronger is allowed, but requesting below the minimum is an error. Generic
   profile defaults are preferences, not ceilings or substitutes for a user pin.
5. With explicit overrides and no/bounded history, provide a complete bounded
   context package. Use full history with overrides only if the tool permits it.

`user_pinned` binds both exact model and effort. Its fallback chain must be empty.
Custom agent configuration may change effective values; that does not authorize a
silent change to a pin. A different pair requires a new authorized decision.

For unpinned routes, validate `[selected] + fallback_chain`. Every pair must remain
available and above both floors. Capability cannot decrease; at equal capability,
effort cannot decrease. Pairs cannot repeat, including the selected pair. Rejected
candidates should refresh preflight once; never repeat an unchanged failed request.

## Evidence has separate meanings

- **Declared availability:** the tool schema permits a request.
- **Selected/requested pair:** what root planned or submitted.
- **Accepted dispatch:** the host accepted a request, possibly returning only an ID.
- **Effective pair:** a runtime result reports actual model and effort with matching
  run, snapshot and worker identities. A schema is not this result.

Preserve unknowns. Neither a child's self-description nor a successful test proves
model identity. Effective evidence also requires a snapshot declaring that the
host reports it. If the host later gains reporting support, record a new snapshot
and rebind the evidence consistently.

High-risk means a minimum of `deep_reasoner` or `independent_adversarial` assurance.
A high-risk plan can be checked without claiming execution. An accepted/completed
high-risk record without effective evidence fails result acceptance. Disclose an
unavailable attestation surface instead of manufacturing a passing record. This
checker does not control dispatch permissions or authenticate supplied evidence.

## Review, capacity and coverage

A review names a real author route, uses a different worker and fresh context, and
cannot participate in a cycle. Planned/rejected/cancelled reviews compare selected
capabilities. Accepted/completed reviews require a dispatched author and both
effective identities, then compare effective capabilities. A weaker reviewer is
invalid. Fresh context is not the same as cross-family or statistical independence.

Normalize child capacity: subtract root slots only when the host's limit includes
root. A `wave` is one declared concurrent batch, not a reconstructed execution
timeline. Planned/accepted/completed routes count; rejected/cancelled ones do not.
Worker identities are unique within a wave.

Every declared task identity needs one route or one explicit root-only record.
Root-only is limited to low-risk deterministic/root-check work. This is coverage
of declared records, not proof all tasks completed: planned, rejected and cancelled
routes still cover a record. Attempt histories require separate bundles in v1.

## Optional offline checker

The source repository ships `validate_runtime_routes.py` under the standard-library
fixture tools. Copying only the Skill does not install that CLI. If it is absent,
apply the policy directly and disclose that automated route validation was not run;
do not invent an installed command or add a runtime/dependency automatically.

The CLI accepts explicit registry and bundle JSON files. It does not fetch source
references, scan host configuration, spawn agents, or modify inputs. Exit 0 means
declared records are consistent, 1 means findings, and 2 means usage error. Findings
are stable `code`, JSON-pointer `path`, and `detail`, emitted as canonical LF JSONL.
Strict v1 objects reject unknown fields; full field definitions belong to the
versioned source-repository specification, not an implicit live-host guarantee.
