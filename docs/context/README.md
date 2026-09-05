# Versioned validation evidence

The directories in this location preserve accepted validation artifacts. They are evidence, not active runtime instructions.

## Included packages

- `adaptive-task-orchestrator-v0.2/` records the first bounded local write-producing multi-agent software-development DAG.
- `adaptive-task-orchestrator-v0.3/` records atomic fixture hardening, evidence validation, worker-owned event streams, and one real single-host overlap probe.
- [v0.4 local candidate](adaptive-task-orchestrator-v0.4/README.md) records portable integrity corrections and independent local review. Actual four-cell CI and real-symlink execution remain pending; this is not a cross-platform release acceptance.

Each package defines its own read order, claim boundary, caveats, and self-excluding SHA-256 manifest. Treat accepted package files as immutable. Record later corrections through a new ADR or a new versioned package.

Some immutable historical documents retain the original
`F:\Projects\CodexProjects` workspace path. That path is provenance, not a public
usage instruction. Run the commands documented in the top-level READMEs from the
root of your clone, and do not rewrite evidence packages merely to make historical
paths portable.

## Public packaging boundary

The original v0.1 archive is not included in this public repository because it contains task transcripts, local paths, identifiers, and verbatim historical material that are not required to use the Skill. Its immutable private baseline is not rewritten or presented here as publicly reproducible evidence.

The public ADR and specification history retains the material v0.1 design decisions and the fingerprint erratum. In particular:

- the historical listed-order / `OrdinalIgnoreCase` fingerprint was `8563586856A87E5309CE35459ACAFBC785C413833B3A8494ACA6EA50E1BDFE8D`;
- the true case-sensitive `Ordinal` fingerprint was `11B134AD4C9611F3845BCB1655AA208F361C020AD03D19C06E66E8FC6E295E42`;
- the seven individual file hashes were unaffected;
- v0.1 did not complete a real write-producing multi-agent DAG.

See [ADR-0002](../decisions/0002-record-v0.1-bundle-fingerprint-errata.md) and [ADR-0008](../decisions/0008-publish-a-curated-open-source-repository.md).
