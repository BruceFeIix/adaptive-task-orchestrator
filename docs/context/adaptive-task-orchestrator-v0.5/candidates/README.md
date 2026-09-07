# v0.5 candidates, not active policy

These files are root-authored review inputs. They are not a completed run, an
effective-model attestation, or an update to either live Skill copy.

- `model-registry.json` is a proposed versioned policy. Native and API effort
  lists intentionally differ; unlisted surfaces cannot supply a candidate.
- `planned-astra-bundle.json` is an illustrative planned high-risk Astra route.
  The host snapshot is based on the current native tool declaration, but no agent
  execution is claimed. Its extra GPT-5.5 host entry is not an eligible registry
  candidate. Effective-configuration reporting is deliberately false.

From the repository root:

```text
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_runtime_routes.py --registry docs/context/adaptive-task-orchestrator-v0.5/candidates/model-registry.json --bundle docs/context/adaptive-task-orchestrator-v0.5/candidates/planned-astra-bundle.json
```

The planned example should pass. Merely changing its dispatch status to
`completed` must fail with `EFFECTIVE_ROUTE_UNATTESTED`. Do not fill in fabricated
effective values to make that check pass. A real host result, if available, needs
an appropriate reporting-capability snapshot and matching identities.

Profile defaults are provisional: frugal/balanced retain Luna, Terra, Sol and
Astra roles; quality raises the first three roles one level. These lists do not
prove a quality, cost, or latency advantage. User pins take precedence without
waiving task floors, permissions or runtime compatibility.
