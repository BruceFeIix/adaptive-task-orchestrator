# Spec: v0.5 runtime-aware Astra routing

## Status and objective

The user approved the staged v0.4/v0.5 direction on 2026-09-06. This is the root's
implementation contract under that authorization; independent design review is
pending before the new live routing policy is accepted.

Keep Codex as executor. Add a versioned candidate registry, an explicit host/tool
capability snapshot, and an offline standard-library semantic checker. The checker
validates declared routing evidence; it neither spawns agents nor proves the truth
of arbitrary supplied host records. Existing TaskContracts and legacy validators
keep their meaning. No external runtime, service, dependency, or global installer.

## Sources and policy assumptions

- [Astra model](https://developers.openai.com/api/docs/models/gpt-6-astra): API effort
  low, medium, high, xhigh, max (checked 2026-09-06).
- [Astra guide](https://developers.openai.com/api/docs/guides/latest-model): API
  tool calling and asynchronous features belong to the API surface, not implicitly
  to every Codex tool.
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents):
  configuration precedence, model/effort defaults, and a child-thread limit that
  excludes the primary. The current collaboration tool instead declares four
  total slots including root, explicit overrides with no/bounded history, and
  Astra efforts low through ultra. A fresh tool snapshot is required per run.

Capability assignments are versioned project policy, not measured universal model
rankings. Initial defaults: Luna fast_reader; Terra general_worker; Sol
deep_reasoner; Astra frontier_reviewer and quality-profile difficult reasoning.
Keep root on the user-selected model. The current continuation pins important work
to Astra; generic examples must not override that session preference.

## Artifacts and ownership

- New registry: `.agents/skills/adaptive-task-orchestrator/references/model-registry.json`.
- New checker: `fixtures/adaptive-task-orchestrator-write-dag/tools/validate_runtime_routes.py`.
- New tests: `fixtures/adaptive-task-orchestrator-write-dag/tests/test_runtime_routes.py`.
- New policy reference: `references/runtime-routing.md` inside the live Skill.
- New ADR and v0.5 context package; bilingual README, CI, and indexes updated last.
- Root owns shared writes. Fresh reviewers inspect frozen contracts and artifacts.

## Interface

`validate_runtime_routes(registry: dict, bundle: dict) -> list[Finding]` is a pure
function. Findings are frozen `code`, `path`, `detail` strings, unique and ordered
by all three fields. Paths are JSON pointers into `/registry` or `/bundle`, never
host-local paths. No wall clock, environment lookup, file traversal, network,
subprocess, or mutation occurs in this function.

CLI: `python -B .../validate_runtime_routes.py --registry FILE --bundle FILE`.
Read only the two explicitly supplied UTF-8 JSON files. Reject duplicate object
keys, nonfinite numbers, invalid UTF-8, wrong top-level types, and invalid schemas.
Emit ASCII-escaped sorted-key compact JSONL with explicit LF bytes. Exit 0 means
declared routing records are consistent, 1 means findings, 2 means usage error.
Zero findings do not mean every task ran, the run is complete, or identity is
authentic. Legacy `validate_evidence.py` is unchanged.

## Registry v1

Required fields: `schema_version` (1), `registry_id`, `revision` (positive integer),
`sources` (nonempty source descriptions), `capabilities` (exact ordered aliases
fast_reader, general_worker, deep_reasoner, frontier_reviewer), `models` (map of
exact IDs), and `defaults` (map for frugal, balanced, quality).

Each model has `capability` (maximum approved alias), `family` (project label for
disclosing diversity, not statistical independence), and `efforts_by_surface`
(surface -> nonempty unique effort list). Supported efforts have explicit ordering
low, medium, high, xhigh, max, ultra. Unknown models and efforts fail validation.
Unregistered models may appear in a host snapshot but are never eligible selected,
effective, or fallback candidates. Defaults map each capability to an ordered candidate model list. Candidates must
exist and satisfy that capability. No model-name lexical ranking or online lookup.
The first registry's concrete choices remain provisional until evaluation.

## Bundle v1

Required fields: `schema_version` (1), `profile` (`runtime-routes-v1`), `run_id`,
`registry_id`, `registry_revision`, `runtime`, `requirements`, `routes`, `root_only`.
Unknown fields are rejected in v1 objects; future extensions require a new version.

`runtime` fields:

- `snapshot_id`, `run_id`, `host_id`, `surface`, `source_ref`: nonempty strings.
- `source_kind`: `runtime-schema` or `runtime-result`; it describes the snapshot,
  not the identity of later agent execution.
- `models`: exact model -> nonempty unique supported effort list.
- `model_override`, `effort_override`, `full_history_with_overrides`: booleans.
- `configuration_overrides`: `none`, `known`, or `unknown`.
- `effective_config_reporting`: boolean.
- `concurrency`: `limit` (positive integer), `includes_root` (boolean),
  `root_slots` (positive integer). If includes_root, child capacity is limit minus
  root_slots, otherwise limit is already the child capacity. Invalid or negative
  capacity is rejected; do not subtract root twice.

The snapshot's run_id must equal the bundle run_id. Every route, including planned
routes, must reference this snapshot_id. Effective configuration evidence requires
effective_config_reporting=true. A later reporting capability needs an updated
snapshot and consistent rebinding, not silent disregard of a false declaration.

`requirements` is an array of root-declared policy assessments, separate from
TaskContracts: `task_id`, `task_revision`, `minimum_capability`, `assurance`
(deterministic, root_check, independent, independent_adversarial). Each task
identity is unique. This checker verifies consistency with these assessments; it
does not infer security impact or assurance from natural-language objectives.

Each `routes` entry has:

- `route_id`, `task_id`, `task_revision`, `snapshot_id`, `wave` (nonnegative integer),
  `worker_id`, `profile` (frugal, balanced, quality, user_pinned).
- `requested_capability`, `selected_model`, `selected_effort`.
- `model_override`, `effort_override` booleans; `fork_turns` is `none`, `all`, or a
  positive integer. Overrides with all require snapshot support. Inherited values
  must still be described as selected/requested, not observed.
- `context_complete`: boolean; an override with no/bounded history requires true.
- `fallback_chain`: array of objects with `model`, `effort`. Validate the entire
  sequence `[selected_candidate] + fallback_chain`: each must be available, meet
  both minimum/requested capabilities, and be monotonic in capability from its
  predecessor. Equal-capability moves cannot lower effort. No duplicate pair in
  the entire sequence, including repetition of the selected pair. Empty is valid.
- `dispatch_status`: `planned`, `accepted`, `rejected`, `completed`, or `cancelled`.
- `effective_route`: null or object with `model`, `effort`, `source_kind`
  (`runtime-result`), `source_ref`, `run_id`, `snapshot_id`, `worker_id`.
- `review_of`: null or an author route ID; `fresh_context`: boolean.

Availability is derived from the registry/snapshot intersection, never supplied as
an unchecked boolean. Every selected pair, including planned routes, must exist
in that intersection and meet both minimum_capability and requested_capability.
A requested_capability below the minimum is itself invalid. Stronger selected
candidates are allowed. Effective routes must also meet both declared requirements.

`user_pinned` pins the exact selected model AND effort. Its fallback_chain must be
empty; any effective route must match the selected pair regardless of known custom
configuration overrides. Changing either value needs a new authorized decision.
Unpinned profiles may honor known overrides when all effective constraints pass.

Only accepted/completed dispatches may carry effective route
evidence; schema-only observations cannot do so. Effective model/effort must be
available, satisfy the floor, and carry matching run/snapshot/worker bindings.
When configuration overrides are none, effective and selected values must match.
Known overrides may differ if effective constraints pass; unknown overrides cannot
support accepted/completed high-risk routes without effective evidence.

High-risk means minimum capability >= deep_reasoner or independent_adversarial
assurance. Planned high-risk routes may be checked without execution evidence;
accepted/completed high-risk routes require effective-route evidence. This is a
policy acceptance gate, not a claim that the checker enforces host dispatch.

Review routes require a real author route, a different worker, fresh_context=true,
and capability at least the author's. A planned review compares both SELECTED
model capabilities; it makes no claim about effective execution. An accepted or
completed review requires an accepted/completed author and compares both EFFECTIVE
model capabilities. Missing either effective identity produces a specific
unsubstantiated-review finding, even for a low-risk author. A standalone low-risk
execution without review_of may remain valid without identity evidence. Never
substitute selected identity in an execution-level comparison. Family equality is
not a failure; disclose diversity separately rather than equating freshness with
cross-model assurance. Self/cyclic review is invalid. Rejected/cancelled reviews
validate the relationship and planned capability compatibility only; they claim
no execution-level comparative assurance.

Routes sharing a wave represent one concurrent batch. Planned, accepted, and
completed entries count toward that batch's capacity; rejected/cancelled entries
  do not. Worker IDs must be unique per wave. This offline convention does not
reconstruct arbitrary event timing or peak live concurrency across wave history.

Each `root_only` entry has task identity, `reason`, and `check_ref`. It may satisfy
only deterministic/root_check low-risk requirements. A task cannot be both a
root-only record and a route. This v1 profile allows only one selected route per
task identity; retries/attempt histories require separate bundles, not an implied
strict-complete-run model. All declared requirements need a route or root record.
This is structural coverage of the declared subset: planned, rejected and cancelled
routes satisfy record coverage too. A zero-finding bundle may contain unfinished
work and must never be described as a complete successful run.

## Diagnostics and tests

Codes distinguish malformed inputs/schema, unsupported version, registry mismatch,
snapshot binding, unavailable model/effort, floor violation, unsupported override,
history/context conflict, unsafe fallback, concurrency overflow, illegal dispatch,
unsubstantiated effective route, invalid review, and ineligible root-only work.
Each failing field has a stable pointer and fixed or input-derived detail without
host exception strings. Invalid structures must yield findings rather than crash.

Test all positive and negative cases above on Python 3.10/3.11, nested wrong types,
bool-as-int, duplicate IDs, unmatched task revisions, empty lists, invalid states,
input immutability, deterministic complete bytes, and usage/read/JSON errors.
Inject fake runtime snapshots offline; do not spawn an agent merely to test a
schema rejection. Keep historical v0.2/v0.3 validators and manifests green.

## Native smoke, claims, and closure

Run a bounded native Astra subagent task when quota is sufficient; retain the tool
request and returned fields. If the host does not expose effective identity, record
accepted-but-unattested, not observed. Do not fabricate a passing high-risk bundle
from that result; disclose that high-risk result acceptance is unsupported by the
available attestation surface. Test this failure gate with offline records.
Compare a few fixed low/medium-risk tasks before changing generic defaults. Record
quality, first-pass acceptance, repairs, elapsed time, and only available usage.
No API-cost inference for a Codex subscription and no broad performance claim.

Update live Skill references only after independent review. Preserve old packages;
add v0.5 evidence, source identities and a manifest generated last. Actual CI and
real symlinks remain separately evidenced. Public push/tag/release require the
user's publication decision. Full attempt/event/effect closure, automatic online
model discovery, persistent scheduling, external model CLIs, and global install
are outside this version.
