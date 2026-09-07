# Spec: Adaptive Task Orchestrator v0.4 portable evidence integrity

## Status

Approved by the user on 2026-08-31. Implementation may proceed under Assumptions
1-8, the bounded scope below, ADR-0009, and the approved task plan.

## Objective

Add a read-only, fail-closed, Python-standard-library verifier for the
self-excluding SHA-256 manifests used by versioned evidence packages. For a
quiescent package, the verifier must provide the same deterministic result on
supported Windows and Linux Python runtimes without relying on GNU `sha256sum`.

Success means a trusted manifest can be used to prove that the package's current
bytes and complete regular-file inventory match that manifest. This version does
not prove who created the manifest, when it was created, or whether the recorded
evidence describes events that actually happened.

## Assumptions

1. v0.4 is a backward-compatible experimental minor release.
2. `docs/context/adaptive-task-orchestrator-v0.2/` and
   `docs/context/adaptive-task-orchestrator-v0.3/` remain byte-identical.
3. The project remains Codex-native, repository-local, standard-library-only, and
   free of persistent services or external orchestration runtimes.
4. The new verifier is a separate CLI. Existing `validate_evidence.py` function and
   CLI behavior remain unchanged.
5. The manifest itself is the trust input. SHA-256 provides tamper detection and
   internal integrity relative to that input, not signatures or authenticity.
6. Manifest paths are package-relative POSIX-style paths using `/`. Absolute paths,
   drive-qualified paths, backslashes, empty segments, `.` segments, `..` segments,
   and paths that resolve outside the package are invalid.
7. Manifest paths use the printable ASCII grammar defined below. Case-sensitive
   ordinal ordering is ASCII byte ordering; the collision key maps `A` through `Z`
   to `a` through `z` and leaves all other permitted bytes unchanged.
8. The selected package is quiescent for the duration of one validation call. The
   verifier rejects observed symlinks and unsafe objects, but it is not a sandbox or
   a defense against an attacker concurrently replacing filesystem entries between
   inspection and read operations.

## Tech Stack

- Python 3.10 and 3.11 standard library only.
- `unittest` for deterministic small and medium tests.
- `pathlib`, `hashlib`, and explicit UTF-8 decoding for package inspection.
- Stable JSON Lines findings using the existing `code`, `path`, and `detail`
  diagnostic shape.
- GitHub Actions on `ubuntu-latest` and `windows-latest`, each with Python 3.10 and
  3.11, for the supported OS/runtime matrix.

No dependency, schema service, key store, network call, or host-specific checksum
binary is added.

## Commands

Run all commands from the repository root.

```powershell
# Targeted v0.4 tests.
py -3 -B -m unittest `
  discover -s fixtures/adaptive-task-orchestrator-write-dag/tests `
  -p "test_verify_integrity.py" -v

# Full fixture tooling regression suite.
py -3 -B -m unittest discover `
  -s fixtures/adaptive-task-orchestrator-write-dag/tests -v

# Verify both published evidence packages.
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/verify_integrity.py `
  --context-root docs/context/adaptive-task-orchestrator-v0.2
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/verify_integrity.py `
  --context-root docs/context/adaptive-task-orchestrator-v0.3

# Preserve the existing structural evidence checks.
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py `
  --context-root docs/context/adaptive-task-orchestrator-v0.2
py -3 -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py `
  --context-root docs/context/adaptive-task-orchestrator-v0.3
```

Platform-neutral equivalents use `python` and shell continuation:

```bash
python -B -m unittest discover \
  -s fixtures/adaptive-task-orchestrator-write-dag/tests \
  -p "test_verify_integrity.py" -v
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/verify_integrity.py \
  --context-root docs/context/adaptive-task-orchestrator-v0.2
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/verify_integrity.py \
  --context-root docs/context/adaptive-task-orchestrator-v0.3
```

The new CLI returns `0` when no findings exist, `1` when stable findings are
emitted, and `2` for command-line usage errors.

## Project Structure

```text
fixtures/adaptive-task-orchestrator-write-dag/
    tools/verify_integrity.py       new read-only manifest verifier
    tools/validate_evidence.py      unchanged selected-record validator
    tests/test_verify_integrity.py  v0.4 RED/GREEN and mutation tests

docs/decisions/
    0009-verify-evidence-manifests-portably.md

docs/context/adaptive-task-orchestrator-v0.4/
    README.md
    contracts/revisions/
    routes/
    receipts/
    evidence/
    integrity.sha256

tasks/
    plan.md
    todo.md
```

The accepted v0.2 and v0.3 evidence directories are immutable inputs, never write
targets.

## Public Interface

### Python

```python
findings = verify_integrity(context_root)
```

The function accepts a `pathlib.Path` and returns a deterministically sorted list of
immutable finding records. It does not write diagnostics, caches, normalized
manifests, or repair output into the package.

### CLI

```text
verify_integrity.py --context-root <package-directory>
```

Each finding is one stable JSON object on stdout:

```json
{"code":"MANIFEST_DIGEST_MISMATCH","detail":"expected ...; actual ...","path":"evidence/result.json"}
```

Human-readable prose may explain a finding in documentation, but scripts must rely
on the stable code and path rather than parsing the detail field.

## Manifest Contract

`integrity.sha256` is canonical LF-terminated UTF-8 without a BOM. It contains
exactly six header lines, followed immediately by zero or more entry lines. Blank
lines, extra comments, CRLF, trailing spaces, lowercase hashes, and inline comments
are invalid.

The normative grammar is:

```text
manifest       = title LF algorithm LF paths LF ordering LF self_exclusion LF count LF *entry
title          = "# " title_start *127title_char
title_start    = ASCII letter / digit
title_char     = ASCII letter / digit / SP / "." / "_" / "-"
algorithm      = "# Algorithm: SHA-256"
paths          = "# Paths are relative to this directory."
ordering       = "# Ordering: case-sensitive ordinal relative path."
self_exclusion = "# integrity.sha256 is intentionally self-excluded."
count          = "# Entries: " ("0" / nonzero_digit *digit)
entry          = 64uppercase_hex SP "*" relative_path LF
relative_path  = segment *("/" segment)
segment        = 1*(ASCII letter / digit / "." / "_" / "-")
```

`segment` must not equal `.` or `..`. `relative_path` therefore cannot be empty,
absolute, drive-qualified, URI-like, contain `//`, contain `\`, contain a control or
non-ASCII byte, or include an empty, `.` or `..` segment. The manifest path
`integrity.sha256` is forbidden as an entry. The title's 128-character bound is
measured in ASCII bytes. The decimal count has no sign and no leading zero except
for the single value `0`.

Entry paths must be strictly increasing by their ASCII bytes. A duplicate path is
reported separately from an order violation. A case-collision key is computed by
mapping ASCII `A`-`Z` to `a`-`z`; two different serialized paths with the same key
are invalid. No Unicode normalization or host-filesystem case rule is inferred.

The verifier must fail closed when any of the following is true:

- `context_root` is absent, is not a directory, cannot be inventoried, or resolves
  unexpectedly during the quiescent call;
- the manifest is absent, is a symlink or non-regular object, cannot be read, is not
  valid UTF-8, contains a BOM/CRLF, or lacks a final LF;
- a header or entry differs from the normative grammar;
- an entry path is unsafe, duplicated, case-colliding, non-ordinal, or includes the
  manifest itself;
- the declared entry count differs from the parsed count;
- a listed path is absent, is a symlink or non-regular object, cannot be read, or
  resolves outside the context root;
- a listed file digest differs from the manifest;
- a regular package file other than `integrity.sha256` is not listed exactly once;
- a symlink, including a symlinked directory, or another unsupported filesystem
  object exists anywhere in the package inventory.

Inventory traversal must inspect entries without following symlinks and must reject
symlinked directories instead of descending into them. Manifest paths are validated
before a listed target is opened. For the quiescent-package model, an unsafe manifest
path must not cause an out-of-root target read. Concurrent hostile replacement is an
explicit non-goal rather than a claim that portable `pathlib` is a sandbox boundary.

## Stable Finding Codes

The initial public code surface is additive and includes at least:

- `CONTEXT_ROOT_NOT_FOUND`
- `CONTEXT_ROOT_NOT_DIRECTORY`
- `INVENTORY_READ_ERROR`
- `MANIFEST_NOT_FOUND`
- `MANIFEST_NOT_REGULAR`
- `MANIFEST_READ_ERROR`
- `MANIFEST_INVALID_UTF8`
- `MANIFEST_FINAL_NEWLINE_MISSING`
- `MANIFEST_HEADER_INVALID`
- `MANIFEST_ENTRY_INVALID`
- `MANIFEST_PATH_UNSAFE`
- `MANIFEST_SELF_INCLUDED`
- `MANIFEST_DUPLICATE_PATH`
- `MANIFEST_CASE_COLLISION`
- `MANIFEST_ORDER_INVALID`
- `MANIFEST_ENTRY_COUNT_MISMATCH`
- `MANIFEST_FILE_MISSING`
- `MANIFEST_FILE_NOT_REGULAR`
- `MANIFEST_FILE_READ_ERROR`
- `MANIFEST_DIGEST_MISMATCH`
- `MANIFEST_UNLISTED_FILE`
- `MANIFEST_UNSUPPORTED_OBJECT`

New codes may be added during RED tests only when they distinguish materially
different corrective actions. Existing codes must not be silently renamed after
publication.

## Code Style

- Use small pure helpers for manifest parsing, canonical path validation, package
  inventory, and digest comparison.
- Keep filesystem reads in an explicit verification phase after parsing and path
  checks.
- Use frozen dataclasses for serialized findings.
- Sort findings by `(code, path, detail)` before returning or printing them.
- Do not use broad `except Exception` handlers to turn programmer defects into
  validation findings.
- Do not normalize or repair malformed input silently.
- Write no files from verifier production code.

Illustrative boundary style:

```python
def verify_integrity(context_root: Path) -> list[Finding]:
    resolved_root = context_root.resolve()
    parsed_manifest, findings = parse_manifest(resolved_root)
    if parsed_manifest is None:
        return sorted(set(findings))
    findings.extend(verify_inventory(resolved_root, parsed_manifest))
    return sorted(set(findings))
```

This is illustrative rather than a required internal implementation.

## Testing Strategy

Follow RED, GREEN, and REFACTOR without weakening existing tests.

### Positive cases

- a minimal valid self-excluding package returns no findings;
- the unchanged v0.2 package verifies all 100 entries;
- the unchanged v0.3 package verifies all 65 entries;
- two validations of the same package emit byte-identical output.

### Single-mutation negative cases

- mutate one listed byte;
- delete one listed file;
- add one unlisted regular file;
- duplicate one manifest path;
- create two paths that collide under case folding;
- reverse two adjacent paths;
- falsify the declared entry count;
- include `integrity.sha256` in its own entries;
- provide absolute, drive-qualified, backslash, empty-segment, `.`, `..`, and
  traversal paths;
- use malformed hex, a missing `*`, invalid UTF-8, or a missing final newline;
- present a context root that is a file, a manifest symlink, a listed-file symlink,
  or a symlinked directory;
- inject manifest-read, inventory, and listed-file-read `OSError` conditions;
- replace or remove a listed file at the tested read boundary under a controlled
  test double and require a stable read-error finding;
- present a directory or supported test double for another unsupported filesystem
  object where a regular file is required.

Each mutation must assert the exact stable finding code and package-relative path.
Where one mutation necessarily causes multiple findings, the test must assert the
complete deterministic set rather than accepting any one of them.

### Read-only oracle

For every negative package, record the complete pre-validation inventory and file
digests, run validation twice, and prove:

- both outputs are byte-identical;
- no package bytes changed;
- no package entry was created or removed;
- Python bytecode is not written when invoked with `-B`.

### Regression

- the full existing fixture suite remains green;
- existing v0.2/v0.3 structural validation remains green;
- existing materializer and event-log public interfaces remain unchanged.

### Supported platform matrix

- `ubuntu-latest` with Python 3.10 and 3.11;
- `windows-latest` with Python 3.10 and 3.11;
- every matrix cell runs the same positive and mutation tests;
- tests assert the exact canonical JSON finding sequence, so a passing matrix proves
  the defined corpus has identical cross-OS output rather than merely similar exit
  codes.

## Boundaries

### Always

- Treat every manifest and package path as untrusted input.
- Require a quiescent package; resolve and contain paths before reading listed
  targets, and reject symlinks without following them.
- Preserve accepted evidence packages byte-for-byte.
- Run a targeted failing test before implementing each behavior group.
- Keep README capability and caveat claims synchronized in English and Chinese.
- Record the final v0.4 claim in a new immutable evidence package and manifest.

### Ask first

- Adding third-party dependencies or a formal signing library.
- Changing the live Skill's general TaskContract or WorkerReceipt requirements.
- Introducing a strict complete-run evidence profile.
- Adding a second domain fixture or external analysis tool.
- Changing CI beyond the approved Windows/Linux Python 3.10/3.11 matrix, replacing
  the platform-specific manifest command, and adding v0.4 validation gates.

### Never

- Rewrite v0.2 or v0.3 evidence, manifests, contracts, routes, or receipts.
- Under the quiescent-package model, read a target outside the selected context root
  because a manifest named it.
- Follow symlinks while computing package integrity.
- Repair, rewrite, or canonicalize a package as a side effect of validation.
- Describe SHA-256 consistency as a signature, trusted timestamp, provenance, or
  authenticity guarantee.
- Add a scheduler, service, daemon, database, persistent queue, or cross-host lease.
- Execute unknown binaries or broaden reverse-engineering claims in this version.

## Success Criteria

1. The proposed spec and ADR are accepted before implementation begins.
2. Every new behavior has a recorded RED test that fails for the expected reason
   before production code exists.
3. All targeted tests and the complete fixture suite pass in the four-cell
   Windows/Linux by Python 3.10/3.11 matrix.
4. The Python verifier accepts the unchanged v0.2 100-entry and v0.3 65-entry
   manifests.
5. Every specified malformed input fails closed with the exact stable finding set.
6. Under the quiescent-package model, unsafe entry paths never trigger an
   out-of-root target read; symlinks and read/inventory errors fail closed.
7. Validation is repeatable and demonstrably read-only.
8. CI uses the Python verifier instead of GNU `sha256sum`, retains the structural
   validators, and executes every test in the supported Windows/Linux matrix.
9. v0.2 and v0.3 integrity manifests and all covered bytes remain unchanged.
10. README, README.zh-CN, fixture documentation, changelog, ADR index, context index,
    and CI describe one coherent v0.4 capability and limitation boundary.
11. A fresh independent reviewer reports no unresolved Critical or Required finding.
12. A new self-excluding, case-sensitive-ordinal v0.4 evidence package records the
    accepted implementation, mutation matrix, compatibility checks, review, and
    final validation receipt.

## Non-Goals

- Signatures, signer identity, key management, trusted timestamps, or provenance.
- Full `strict-complete-run` contract/route/receipt/effect closure.
- Process-crash recovery, PID identity, stale-lock detection, or lock reclamation.
- Third-party OpenAPI semantic validation.
- A reverse-engineering or second-domain end-to-end fixture.
- Persistent scheduling, services, queues, databases, dashboards, or web APIs.
- Cross-machine execution, distributed tracing, performance, or throughput claims.
- Changes to `materialize_run`, event stream schema v1, or existing validator codes.

## Resolved Decisions

1. The user accepted Assumptions 1-8 and this bounded v0.4 objective on 2026-08-31.
2. Strict evidence closure and the second-domain fixture remain deferred until after
   the portable integrity foundation is implemented and reviewed.
