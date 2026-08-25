# User compatibility fixture

This baseline supports the legacy `name` field. The migration target is to introduce `displayName` as the canonical field while preserving legacy payload compatibility.

The public contract and generated directory each have one writer. The server and client consumer directories may be updated independently only after the contract and generated artifact are accepted.
