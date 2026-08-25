# Security policy

## Supported versions

Security fixes are applied to the current `main` branch. Until the project publishes a stable `1.x` release, older experimental milestones are evidence records rather than separately supported release lines.

## Report a vulnerability

Do not put vulnerability details in a public issue for a suspected vulnerability,
credential exposure, private-repository leak, unsafe fixture behavior, or
permission-boundary bypass. Use the detail-free fallback below only when private
reporting is unavailable.

Use [GitHub private vulnerability reporting](https://github.com/BruceFeIix/adaptive-task-orchestrator/security/advisories/new) to send:

- a concise impact statement;
- affected paths or versions;
- a minimal, sanitized reproduction;
- the expected permission or evidence boundary;
- any suggested mitigation;
- confirmation that the report contains no unrelated secrets or private project data.

If private vulnerability reporting is unavailable, open a public issue containing
no vulnerability details and ask the maintainer to establish a private reporting
channel. For an active exposure of GitHub-hosted data, use GitHub's abuse-reporting
flow as appropriate. Never publish exploit details, secrets, or affected-user data
in an issue.

The project does not currently promise a response-time SLA, bug bounty, certification, or production security support. Maintainers will acknowledge and assess reports on a best-effort basis and coordinate disclosure when a fix is ready.

## Security scope

Security-relevant areas include:

- permission and scope preservation;
- resource-lock and writer-ownership enforcement;
- fixture path validation and non-overwrite guarantees;
- evidence parser fail-closed behavior;
- route-attestation and receipt-consistency claims;
- accidental publication of credentials, local paths, or user-owned content.

The current validator checks selected structural and lifecycle invariants. It does not establish cryptographic authenticity, trusted timestamps, third-party OpenAPI semantics, runtime model safety, or production suitability.
