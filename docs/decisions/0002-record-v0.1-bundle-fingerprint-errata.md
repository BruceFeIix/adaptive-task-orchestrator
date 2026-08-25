# ADR-0002: Record the v0.1 bundle fingerprint ordering errata

## Status

Accepted

## Date

2026-08-24

## Context

The immutable v0.1 snapshot manifest describes its canonical bundle fingerprint as sorting relative paths with ordinal ordering. The historical value recorded in `first-implementation.sha256` and `MANIFEST.json` is:

```text
8563586856A87E5309CE35459ACAFBC785C413833B3A8494ACA6EA50E1BDFE8D
```

Deterministic reproduction established that this value is produced both by the manifest's listed order and by `OrdinalIgnoreCase` sorting. A truly case-sensitive `Ordinal` sort places `SKILL.md` before the lowercase paths and produces:

```text
11B134AD4C9611F3845BCB1655AA208F361C020AD03D19C06E66E8FC6E295E42
```

The seven individual file hashes are identical under both procedures and remain valid. The archive-wide manifest also remains valid at 25 of 25 entries.

## Decision

Treat the historical value as an auditable v0.1 record whose sorting label was inaccurate, not as corrupted file evidence.

- Preserve `docs/context/adaptive-task-orchestrator-v0.1/snapshot/` unchanged.
- Preserve the verbatim historical reports unchanged.
- Preserve `archive.sha256`, `first-implementation.sha256`, and `MANIFEST.json` unchanged.
- Use `11B134AD4C9611F3845BCB1655AA208F361C020AD03D19C06E66E8FC6E295E42` when a later document explicitly claims case-sensitive ordinal ordering.
- State the historical value as `OrdinalIgnoreCase / manifest listed order` whenever comparing the two fingerprints.

## Alternatives Considered

### Rewrite the v0.1 manifests

Rejected. Those files are part of the preserved historical baseline. Rewriting them would erase the evidence of what v0.1 originally claimed and invalidate the archive manifest.

### Ignore the discrepancy

Rejected. Future verification could otherwise report inconsistent bundle identities despite every file being unchanged.

### Treat the snapshot as corrupted

Rejected. All seven individual SHA-256 values pass, live and snapshot files match, and the discrepancy is fully explained by string ordering semantics.

## Consequences

- v0.1 remains byte-for-byte auditable.
- Later verification must name its string comparer rather than using the ambiguous word "ordinal" alone.
- The errata is additive and does not change the live Skill.
- A future v0.2 evidence manifest may use a separately documented canonicalization procedure without retroactively changing v0.1.
