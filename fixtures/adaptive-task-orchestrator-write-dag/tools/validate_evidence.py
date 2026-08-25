from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


TASK_TYPES = {"research", "implementation", "verification", "review", "synthesis"}
MODES = {"read", "write", "external_action"}
ASSURANCE_REQUIREMENTS = {
    "deterministic",
    "root_check",
    "independent",
    "independent_adversarial",
}
ROUTE_STATUSES = {"requested", "observed", "inherited-unattested"}
ROUTE_PROFILES = {"frugal", "balanced", "quality", "user_pinned"}
RECEIPT_STATUSES = {"DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"}
CLAIM_CONFIDENCES = {"high", "medium", "low"}
CHECK_RESULTS = {
    "pass",
    "fail",
    "inconclusive",
    "expected_red",
    "expected_fail",
    "concern",
    "absent",
    "not_authorized",
    "transient_command_error",
}
DONE_PASSING_CHECK_RESULTS = {"pass", "expected_red", "expected_fail"}
ROOT_RECORD_KINDS = {
    "root_execution_record",
    "root_execution_record_with_legacy_route_fields",
}
CONTRACT_CORE_FIELDS = {
    "id",
    "revision",
    "objective",
    "task_type",
    "mode",
    "dependencies",
    "inputs",
    "deliverable",
    "read_scope",
    "write_scope",
    "resource_locks",
    "acceptance_checks",
    "evidence_required",
    "assurance_requirement",
}
EXECUTABLE_CONTRACT_FIELDS = CONTRACT_CORE_FIELDS | {"context_package", "classification"}
CONTEXT_PACKAGE_FIELDS = {
    "authoritative_facts",
    "relevant_artifacts",
    "accepted_upstream_results",
    "user_constraints",
    "permissions",
    "non_goals",
}
CLASSIFICATION_FIELDS = {
    "reasoning_depth",
    "context_breadth",
    "uncertainty",
    "novelty",
    "impact",
    "verifiability",
    "coupling",
}
CHILD_ROUTE_FIELDS = {
    "task_id",
    "task_revision",
    "profile",
    "preferred_capability",
    "requested_capability",
    "route_reason_codes",
    "effective_floor",
    "floor_reasons",
    "selected_model",
    "selected_effort",
    "fork_turns",
    "fallback_chain",
    "selection_reason",
    "route_status",
    "capability_attested",
    "attestation_source",
    "floor_satisfied",
}
PREFLIGHT_ROUTE_FIELDS = {
    "task_id",
    "task_revision",
    "requested_capability",
    "route_status",
    "capability_attested",
    "attestation_source",
    "floor_satisfied",
    "dispatch_result",
}
ROOT_ROUTE_FIELDS = {
    "record_kind",
    "task_id",
    "task_revision",
    "execution_target",
    "execution_status",
    "exact_root_model_attested",
    "route_status",
    "reason",
}
LEGACY_ROOT_ROUTE_FIELDS = {
    "record_kind",
    "semantic_note",
    "task_id",
    "task_revision",
    "preferred_capability",
    "requested_capability",
    "route_reason_codes",
    "effective_floor",
    "floor_reasons",
    "selected_model",
    "selected_effort",
    "fork_turns",
    "fallback_chain",
    "selection_reason",
    "route_status",
    "capability_attested",
    "attestation_source",
    "floor_satisfied",
    "execution_status",
    "worker",
}
RECEIPT_FIELDS = {
    "status",
    "task_id",
    "task_revision",
    "summary",
    "claims",
    "uncertainty",
    "artifacts_or_changes",
    "resources_accessed",
    "external_calls",
    "checks",
    "contradictions",
    "recommended_next",
}
IDENTITY_PATTERN = re.compile(r"^(.+)@([1-9][0-9]*)$")


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    path: str
    detail: str


def _relative(path: Path, context_root: Path) -> str:
    return path.relative_to(context_root).as_posix()


def _finding(code: str, path: str, detail: str) -> Finding:
    return Finding(code=code, path=path, detail=detail)


def _load_json(path: Path, context_root: Path, findings: list[Finding]) -> Any | None:
    relative_path = _relative(path, context_root)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        findings.append(_finding("JSON_INVALID", relative_path, "expected UTF-8 JSON"))
        return None
    if not isinstance(value, dict):
        findings.append(_finding("RECORD_INVALID_TYPE", relative_path, "expected JSON object"))
        return None
    return value


def _identity(value: Any, id_field: str, revision_field: str) -> tuple[str, int] | None:
    task_id = value.get(id_field) if isinstance(value, dict) else None
    revision = value.get(revision_field) if isinstance(value, dict) else None
    if not isinstance(task_id, str) or not task_id or isinstance(revision, bool):
        return None
    if not isinstance(revision, int) or revision < 1:
        return None
    return task_id, revision


def _parse_identity(value: Any) -> tuple[str, int] | None:
    if not isinstance(value, str):
        return None
    match = IDENTITY_PATTERN.fullmatch(value)
    if match is None:
        return None
    return match.group(1), int(match.group(2))


def _missing_fields(
    value: dict[str, Any], required: Iterable[str], code: str, path: str
) -> list[Finding]:
    return [
        _finding(code, path, field)
        for field in sorted(set(required).difference(value))
    ]


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _validate_contract_types(
    value: dict[str, Any],
    path: str,
    *,
    strict: bool,
    require_complete_context: bool = True,
) -> list[Finding]:
    findings: list[Finding] = []
    identity = _identity(value, "id", "revision")
    if identity is None:
        findings.append(
            _finding("CONTRACT_INVALID_TYPE", path, "id must be non-empty and revision positive")
        )
    for field in (
        "objective",
        "deliverable",
        "task_type",
        "mode",
        "assurance_requirement",
    ):
        if field in value and (not isinstance(value[field], str) or not value[field]):
            findings.append(_finding("CONTRACT_INVALID_TYPE", path, field))
    for field in (
        "dependencies",
        "inputs",
        "read_scope",
        "write_scope",
        "resource_locks",
        "acceptance_checks",
        "evidence_required",
    ):
        if field in value and not _is_string_list(value[field]):
            findings.append(_finding("CONTRACT_INVALID_TYPE", path, field))

    if strict:
        for field, allowed in (
            ("task_type", TASK_TYPES),
            ("mode", MODES),
            ("assurance_requirement", ASSURANCE_REQUIREMENTS),
        ):
            if field in value and isinstance(value[field], str) and value[field] not in allowed:
                findings.append(_finding("CONTRACT_INVALID_ENUM", path, field))

        context_package = value.get("context_package")
        if context_package is not None:
            if not isinstance(context_package, dict):
                findings.append(_finding("CONTRACT_INVALID_TYPE", path, "context_package"))
            else:
                if require_complete_context:
                    for field in sorted(CONTEXT_PACKAGE_FIELDS.difference(context_package)):
                        findings.append(
                            _finding(
                                "CONTRACT_MISSING_FIELD",
                                path,
                                f"context_package.{field}",
                            )
                        )
                for field in CONTEXT_PACKAGE_FIELDS.intersection(context_package):
                    if not _is_string_list(context_package[field]):
                        findings.append(
                            _finding("CONTRACT_INVALID_TYPE", path, f"context_package.{field}")
                        )

        classification = value.get("classification")
        if classification is not None:
            if not isinstance(classification, dict):
                findings.append(_finding("CONTRACT_INVALID_TYPE", path, "classification"))
            else:
                findings.extend(
                    _missing_fields(
                        classification,
                        CLASSIFICATION_FIELDS,
                        "CONTRACT_MISSING_FIELD",
                        path,
                    )
                )
                for field in CLASSIFICATION_FIELDS.intersection(classification):
                    score = classification[field]
                    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 3:
                        findings.append(
                            _finding("CONTRACT_INVALID_TYPE", path, f"classification.{field}")
                        )
    return findings


def _historical_boundaries(
    context_root: Path, findings: list[Finding]
) -> tuple[set[tuple[str, int]], set[tuple[str, int]]]:
    ledger_path = context_root / "evidence" / "historical-contract-fidelity.json"
    if not ledger_path.is_file():
        return set(), set()
    ledger = _load_json(ledger_path, context_root, findings)
    if ledger is None:
        return set(), set()

    exact: set[tuple[str, int]] = set()
    unavailable: set[tuple[str, int]] = set()
    for field, target in (("exact_revisions", exact), ("unavailable_exact_bodies", unavailable)):
        entries = ledger.get(field)
        if not isinstance(entries, list):
            findings.append(
                _finding("HISTORICAL_BOUNDARY_INVALID", _relative(ledger_path, context_root), field)
            )
            continue
        for index, entry in enumerate(entries):
            identity = _parse_identity(entry.get("task")) if isinstance(entry, dict) else None
            if identity is None:
                findings.append(
                    _finding(
                        "HISTORICAL_BOUNDARY_INVALID",
                        _relative(ledger_path, context_root),
                        f"{field}[{index}].task",
                    )
                )
            else:
                target.add(identity)
    return exact, unavailable


def _contract_records(
    context_root: Path,
    historical_exact: set[tuple[str, int]],
    findings: list[Finding],
) -> tuple[
    dict[tuple[str, int], tuple[Path, dict[str, Any]]],
    set[tuple[str, int]],
    set[tuple[str, int]],
]:
    contracts_root = context_root / "contracts"
    current: dict[tuple[str, int], tuple[Path, dict[str, Any]]] = {}
    known: set[tuple[str, int]] = set()
    if not contracts_root.is_dir():
        return current, known, set()

    for path in sorted(contracts_root.glob("*.json")):
        value = _load_json(path, context_root, findings)
        if value is None:
            continue
        relative_path = _relative(path, context_root)
        record_kind = value.get("record_kind")
        if record_kind not in (None, "preflight_fixture_record"):
            findings.append(_finding("RECORD_UNKNOWN_KIND", relative_path, str(record_kind)))
            continue
        required = CONTRACT_CORE_FIELDS if record_kind == "preflight_fixture_record" else EXECUTABLE_CONTRACT_FIELDS
        findings.extend(_missing_fields(value, required, "CONTRACT_MISSING_FIELD", relative_path))
        identity = _identity(value, "id", "revision")
        findings.extend(
            _validate_contract_types(
                value,
                relative_path,
                strict=True,
                require_complete_context=identity not in historical_exact,
            )
        )
        if identity is None:
            continue
        if identity in current:
            findings.append(_finding("CONTRACT_DUPLICATE_IDENTITY", relative_path, f"{identity[0]}@{identity[1]}"))
        current[identity] = (path, value)
        known.add(identity)

    revisions_root = contracts_root / "revisions"
    preflight_identities = {
        identity
        for identity, (_, value) in current.items()
        if value.get("record_kind") == "preflight_fixture_record"
    }
    if revisions_root.is_dir():
        for path in sorted(revisions_root.glob("*.contract.json")):
            value = _load_json(path, context_root, findings)
            if value is None:
                continue
            relative_path = _relative(path, context_root)
            record_kind = value.get("record_kind")
            if record_kind not in (None, "preflight_fixture_record"):
                findings.append(
                    _finding("RECORD_UNKNOWN_KIND", relative_path, str(record_kind))
                )
                continue
            identity = _identity(value, "id", "revision")
            required = (
                CONTRACT_CORE_FIELDS
                if identity in historical_exact
                or identity in preflight_identities
                or record_kind == "preflight_fixture_record"
                else EXECUTABLE_CONTRACT_FIELDS
            )
            findings.extend(_missing_fields(value, required, "CONTRACT_MISSING_FIELD", relative_path))
            findings.extend(
                _validate_contract_types(
                    value,
                    relative_path,
                    strict=identity not in historical_exact,
                    require_complete_context=identity not in historical_exact,
                )
            )
            if identity is not None:
                known.add(identity)

    for identity, (current_path, value) in current.items():
        if value.get("record_kind") == "preflight_fixture_record":
            continue
        revision_path = revisions_root / f"{identity[0]}-r{identity[1]}.contract.json"
        relative_path = _relative(current_path, context_root)
        if not revision_path.is_file():
            findings.append(
                _finding(
                    "CURRENT_REVISION_MISSING",
                    relative_path,
                    _relative(revision_path, context_root),
                )
            )
        elif current_path.read_bytes() != revision_path.read_bytes():
            findings.append(
                _finding(
                    "CURRENT_REVISION_MISMATCH",
                    relative_path,
                    _relative(revision_path, context_root),
                )
            )
    return current, known, preflight_identities


def _validate_dependencies(
    current: dict[tuple[str, int], tuple[Path, dict[str, Any]]],
    known: set[tuple[str, int]],
    context_root: Path,
) -> list[Finding]:
    findings: list[Finding] = []
    for _, (path, value) in current.items():
        dependencies = value.get("dependencies")
        if not isinstance(dependencies, list):
            continue
        relative_path = _relative(path, context_root)
        for dependency in dependencies:
            identity = _parse_identity(dependency)
            if identity is None:
                findings.append(_finding("DEPENDENCY_INVALID_IDENTITY", relative_path, str(dependency)))
            elif identity not in known:
                findings.append(_finding("DEPENDENCY_UNRESOLVED", relative_path, dependency))
    return findings


def _validate_route_optional_fields(value: dict[str, Any], path: str) -> list[Finding]:
    findings: list[Finding] = []
    for field in (
        "worker",
        "dispatch_result",
        "stale_reason",
        "cancel_reason",
        "evidence_disposition",
        "review_decision",
        "semantic_note",
    ):
        if field in value and value[field] is not None and not _is_nonempty_string(value[field]):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, field))
    scheduler_state = value.get("scheduler_state")
    if scheduler_state is not None:
        if not isinstance(scheduler_state, str):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, "scheduler_state"))
        elif scheduler_state not in {"STALE", "CANCELLED"}:
            findings.append(_finding("ROUTE_INVALID_ENUM", path, "scheduler_state"))
    if "conflicts_with" in value and _parse_identity(value["conflicts_with"]) is None:
        findings.append(_finding("ROUTE_INVALID_TYPE", path, "conflicts_with"))
    return findings


def _validate_child_route_types(
    value: dict[str, Any],
    path: str,
    *,
    require_complete: bool,
) -> list[Finding]:
    findings: list[Finding] = []
    if require_complete:
        findings.extend(_missing_fields(value, CHILD_ROUTE_FIELDS, "ROUTE_MISSING_FIELD", path))
    else:
        findings.extend(_missing_fields(value, PREFLIGHT_ROUTE_FIELDS, "ROUTE_MISSING_FIELD", path))

    if _identity(value, "task_id", "task_revision") is None:
        findings.append(_finding("ROUTE_INVALID_TYPE", path, "task identity"))

    for field in (
        "preferred_capability",
        "requested_capability",
        "effective_floor",
        "selected_model",
        "selected_effort",
        "fork_turns",
        "selection_reason",
    ):
        if field in value and not _is_nonempty_string(value[field]):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, field))
    for field in ("route_reason_codes", "floor_reasons", "fallback_chain"):
        if field in value and not _is_string_list(value[field]):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, field))

    profile = value.get("profile")
    if "profile" in value:
        if not _is_nonempty_string(profile):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, "profile"))
        elif profile not in ROUTE_PROFILES:
            findings.append(_finding("ROUTE_INVALID_ENUM", path, "profile"))

    route_status = value.get("route_status")
    if not isinstance(route_status, str):
        findings.append(_finding("ROUTE_INVALID_TYPE", path, "route_status"))
    elif route_status not in ROUTE_STATUSES:
        findings.append(_finding("ROUTE_INVALID_ENUM", path, "route_status"))

    attested = value.get("capability_attested")
    source = value.get("attestation_source")
    floor = value.get("floor_satisfied")
    if not isinstance(attested, bool):
        findings.append(_finding("ROUTE_INVALID_TYPE", path, "capability_attested"))
    if require_complete:
        if not isinstance(source, str):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, "attestation_source"))
        elif source not in {"runtime-schema", "runtime-result", "none"}:
            findings.append(_finding("ROUTE_INVALID_ENUM", path, "attestation_source"))
        if not isinstance(floor, bool):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, "floor_satisfied"))
    else:
        if source is not None and not isinstance(source, str):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, "attestation_source"))
        elif isinstance(source, str) and source != "none":
            findings.append(_finding("ROUTE_INVALID_ENUM", path, "attestation_source"))
        if floor is not None and not isinstance(floor, bool):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, "floor_satisfied"))
    findings.extend(_validate_route_optional_fields(value, path))
    return findings


def _validate_child_route(value: dict[str, Any], path: str) -> list[Finding]:
    findings = _validate_child_route_types(
        value,
        path,
        require_complete=True,
    )
    route_status = value.get("route_status")
    attested = value.get("capability_attested")
    source = value.get("attestation_source")
    floor = value.get("floor_satisfied")
    if route_status == "inherited-unattested":
        findings.append(
            _finding("ROUTE_ILLEGAL_STATE", path, "child route cannot be inherited-unattested")
        )
    if attested is True and (
        not isinstance(source, str) or source not in {"runtime-schema", "runtime-result"}
    ):
        findings.append(
            _finding("ROUTE_ILLEGAL_STATE", path, "attested route needs runtime source")
        )
    if attested is False and source != "none":
        findings.append(
            _finding("ROUTE_ILLEGAL_STATE", path, "unattested route cannot name runtime source")
        )
    if route_status == "observed" and (attested is not True or floor is not True):
        findings.append(
            _finding(
                "ROUTE_ILLEGAL_STATE",
                path,
                "observed route must be attested and satisfy floor",
            )
        )
    if attested is False and floor is True:
        findings.append(
            _finding("ROUTE_ILLEGAL_STATE", path, "unattested child route cannot satisfy floor")
        )
    return findings


def _validate_preflight_route(value: dict[str, Any], path: str) -> list[Finding]:
    findings = _validate_child_route_types(
        value,
        path,
        require_complete=False,
    )
    if value.get("route_status") != "requested":
        findings.append(
            _finding("ROUTE_ILLEGAL_STATE", path, "preflight route must remain requested")
        )
    if value.get("capability_attested") is not False:
        findings.append(
            _finding("ROUTE_ILLEGAL_STATE", path, "non-dispatched preflight must be unattested")
        )
    preflight_source = value.get("attestation_source")
    if preflight_source is not None and preflight_source != "none":
        findings.append(
            _finding("ROUTE_ILLEGAL_STATE", path, "preflight cannot name runtime attestation")
        )
    preflight_floor = value.get("floor_satisfied")
    if preflight_floor is not None and preflight_floor is not False:
        findings.append(
            _finding("ROUTE_ILLEGAL_STATE", path, "preflight cannot claim floor satisfaction")
        )
    dispatch_result = value.get("dispatch_result")
    if not isinstance(dispatch_result, str) or not dispatch_result.startswith("not_dispatched_"):
        findings.append(
            _finding("ROUTE_ILLEGAL_STATE", path, "preflight must record non-dispatch")
        )
    return findings


def _validate_root_route(value: dict[str, Any], path: str) -> list[Finding]:
    findings = _missing_fields(value, ROOT_ROUTE_FIELDS, "ROUTE_MISSING_FIELD", path)
    if _identity(value, "task_id", "task_revision") is None:
        findings.append(_finding("ROUTE_INVALID_TYPE", path, "task identity"))
    for field in ("execution_target", "reason"):
        if field in value and not _is_nonempty_string(value[field]):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, field))
    if "exact_root_model_attested" in value and not isinstance(
        value["exact_root_model_attested"], bool
    ):
        findings.append(_finding("ROUTE_INVALID_TYPE", path, "exact_root_model_attested"))
    if "execution_result" in value and not _is_nonempty_string(value["execution_result"]):
        findings.append(_finding("ROUTE_INVALID_TYPE", path, "execution_result"))

    route_status = value.get("route_status")
    if not isinstance(route_status, str):
        findings.append(_finding("ROUTE_INVALID_TYPE", path, "route_status"))
    elif route_status not in ROUTE_STATUSES:
        findings.append(_finding("ROUTE_INVALID_ENUM", path, "route_status"))
    if route_status != "inherited-unattested":
        findings.append(
            _finding("ROUTE_ILLEGAL_STATE", path, "root execution must be inherited-unattested")
        )

    execution_status = value.get("execution_status")
    if not isinstance(execution_status, str):
        findings.append(_finding("ROUTE_INVALID_TYPE", path, "execution_status"))
    elif execution_status not in {"observed", "cancelled_pre_dispatch"}:
        findings.append(_finding("ROUTE_INVALID_ENUM", path, "execution_status"))
    findings.extend(_validate_route_optional_fields(value, path))
    return findings


def _validate_legacy_root_route(value: dict[str, Any], path: str) -> list[Finding]:
    findings = _missing_fields(value, LEGACY_ROOT_ROUTE_FIELDS, "ROUTE_MISSING_FIELD", path)
    if _identity(value, "task_id", "task_revision") is None:
        findings.append(_finding("ROUTE_INVALID_TYPE", path, "task identity"))
    for field in (
        "semantic_note",
        "preferred_capability",
        "requested_capability",
        "effective_floor",
        "selected_model",
        "selected_effort",
        "fork_turns",
        "selection_reason",
        "worker",
    ):
        if field in value and not _is_nonempty_string(value[field]):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, field))
    for field in ("route_reason_codes", "floor_reasons", "fallback_chain"):
        if field in value and not _is_string_list(value[field]):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, field))
    for field in ("capability_attested", "floor_satisfied"):
        if field in value and not isinstance(value[field], bool):
            findings.append(_finding("ROUTE_INVALID_TYPE", path, field))
    if value.get("route_status") != "inherited-unattested":
        findings.append(
            _finding("ROUTE_ILLEGAL_STATE", path, "legacy root must be inherited-unattested")
        )
    if value.get("execution_status") != "observed":
        findings.append(_finding("ROUTE_INVALID_ENUM", path, "execution_status"))
    if value.get("capability_attested") is not False:
        findings.append(_finding("ROUTE_ILLEGAL_STATE", path, "legacy root must be unattested"))
    if value.get("attestation_source") != "none":
        findings.append(_finding("ROUTE_ILLEGAL_STATE", path, "legacy root has no attestation"))
    if value.get("floor_satisfied") is not True:
        findings.append(
            _finding("ROUTE_ILLEGAL_STATE", path, "legacy root retains root-authority floor")
        )
    findings.extend(_validate_route_optional_fields(value, path))
    return findings


def _validate_routes(
    context_root: Path,
    known: set[tuple[str, int]],
    preflight_identities: set[tuple[str, int]],
    findings: list[Finding],
) -> None:
    routes_root = context_root / "routes"
    if not routes_root.is_dir():
        return
    for path in sorted(routes_root.glob("*.json")):
        value = _load_json(path, context_root, findings)
        if value is None:
            continue
        relative_path = _relative(path, context_root)
        record_kind = value.get("record_kind")
        identity = _identity(value, "task_id", "task_revision")
        if record_kind is None:
            dispatch_result = value.get("dispatch_result")
            is_preflight = (
                identity in preflight_identities
                and isinstance(dispatch_result, str)
                and dispatch_result.startswith("not_dispatched_")
            )
            if is_preflight:
                findings.extend(_validate_preflight_route(value, relative_path))
            else:
                findings.extend(_validate_child_route(value, relative_path))
        elif record_kind == "root_execution_record":
            findings.extend(_validate_root_route(value, relative_path))
        elif record_kind == "root_execution_record_with_legacy_route_fields":
            findings.extend(_validate_legacy_root_route(value, relative_path))
        else:
            findings.append(_finding("RECORD_UNKNOWN_KIND", relative_path, str(record_kind)))
            continue
        if identity is not None and identity not in known:
            findings.append(
                _finding("ROUTE_REVISION_MISMATCH", relative_path, f"{identity[0]}@{identity[1]}")
            )


def _validate_claims(value: Any, path: str) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(value, list):
        return [_finding("RECEIPT_INVALID_TYPE", path, "claims")]
    for index, claim in enumerate(value):
        prefix = f"claims[{index}]"
        if not isinstance(claim, dict):
            findings.append(_finding("RECEIPT_INVALID_TYPE", path, prefix))
            continue
        for field in sorted({"claim", "confidence", "evidence"}.difference(claim)):
            findings.append(
                _finding("RECEIPT_MISSING_FIELD", path, f"{prefix}.{field}")
            )
        if "claim" in claim and not _is_nonempty_string(claim["claim"]):
            findings.append(_finding("RECEIPT_INVALID_TYPE", path, f"{prefix}.claim"))
        confidence = claim.get("confidence")
        if "confidence" in claim:
            if not isinstance(confidence, str):
                findings.append(
                    _finding("RECEIPT_INVALID_TYPE", path, f"{prefix}.confidence")
                )
            elif confidence not in CLAIM_CONFIDENCES:
                findings.append(
                    _finding("RECEIPT_INVALID_ENUM", path, f"{prefix}.confidence")
                )
        evidence = claim.get("evidence")
        if "evidence" in claim:
            if not _is_string_list(evidence):
                findings.append(
                    _finding("RECEIPT_INVALID_TYPE", path, f"{prefix}.evidence")
                )
            elif not evidence:
                findings.append(
                    _finding("RECEIPT_CLAIM_EVIDENCE_MISSING", path, f"{prefix}.evidence")
                )
    return findings


def _validate_checks(value: Any, path: str) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    results: list[str] = []
    if not isinstance(value, list):
        return [_finding("RECEIPT_INVALID_TYPE", path, "checks")], results
    for index, check in enumerate(value):
        prefix = f"checks[{index}]"
        if not isinstance(check, dict):
            findings.append(_finding("RECEIPT_INVALID_TYPE", path, prefix))
            continue
        for field in sorted({"check", "result"}.difference(check)):
            findings.append(
                _finding("RECEIPT_MISSING_FIELD", path, f"{prefix}.{field}")
            )
        if "check" in check and not _is_nonempty_string(check["check"]):
            findings.append(_finding("RECEIPT_INVALID_TYPE", path, f"{prefix}.check"))
        result = check.get("result")
        if "result" in check:
            if not isinstance(result, str):
                findings.append(
                    _finding("RECEIPT_INVALID_TYPE", path, f"{prefix}.result")
                )
            elif result not in CHECK_RESULTS:
                findings.append(
                    _finding("RECEIPT_INVALID_ENUM", path, f"{prefix}.result")
                )
                results.append(result)
            else:
                results.append(result)
    return findings, results


def _validate_receipts(
    context_root: Path,
    known: set[tuple[str, int]],
    historical_unavailable: set[tuple[str, int]],
    findings: list[Finding],
) -> None:
    receipts_root = context_root / "receipts"
    if not receipts_root.is_dir():
        return
    for path in sorted(receipts_root.glob("*.json")):
        value = _load_json(path, context_root, findings)
        if value is None:
            continue
        relative_path = _relative(path, context_root)
        if value.get("record_kind") is not None:
            findings.append(
                _finding("RECORD_UNKNOWN_KIND", relative_path, str(value.get("record_kind")))
            )
            continue
        findings.extend(_missing_fields(value, RECEIPT_FIELDS, "RECEIPT_MISSING_FIELD", relative_path))
        status = value.get("status")
        if not isinstance(status, str):
            findings.append(_finding("RECEIPT_INVALID_TYPE", relative_path, "status"))
        elif status not in RECEIPT_STATUSES:
            findings.append(_finding("RECEIPT_INVALID_ENUM", relative_path, "status"))
        identity = _identity(value, "task_id", "task_revision")
        if identity is None:
            findings.append(_finding("RECEIPT_INVALID_TYPE", relative_path, "task identity"))
        elif identity not in known:
            findings.append(
                _finding(
                    "RECEIPT_REVISION_MISMATCH",
                    relative_path,
                    f"{identity[0]}@{identity[1]}",
                )
            )
        for field in ("summary", "recommended_next"):
            if field in value and not _is_nonempty_string(value[field]):
                findings.append(_finding("RECEIPT_INVALID_TYPE", relative_path, field))

        if "claims" in value:
            findings.extend(_validate_claims(value["claims"], relative_path))
        check_results: list[str] = []
        if "checks" in value:
            check_findings, check_results = _validate_checks(value["checks"], relative_path)
            findings.extend(check_findings)

        for field in (
            "uncertainty",
            "resources_accessed",
            "external_calls",
            "contradictions",
        ):
            if field in value and not _is_string_list(value[field]):
                findings.append(_finding("RECEIPT_INVALID_TYPE", relative_path, field))

        artifacts = value.get("artifacts_or_changes")
        if "artifacts_or_changes" in value:
            if not isinstance(artifacts, list) or any(
                not isinstance(item, dict) and not _is_nonempty_string(item)
                for item in artifacts
            ):
                findings.append(
                    _finding("RECEIPT_INVALID_TYPE", relative_path, "artifacts_or_changes")
                )

        if (
            status == "DONE"
            and identity not in historical_unavailable
            and any(result not in DONE_PASSING_CHECK_RESULTS for result in check_results)
        ):
            findings.append(
                _finding(
                    "RECEIPT_STATUS_CHECK_CONFLICT",
                    relative_path,
                    "DONE requires only passing or expected-failure checks",
                )
            )


def validate_context(context_root: Path) -> list[Finding]:
    context_root = Path(context_root).resolve()
    if not context_root.is_dir():
        return [
            _finding("CONTEXT_ROOT_NOT_FOUND", str(context_root), "expected context directory")
        ]

    findings: list[Finding] = []
    historical_exact, historical_unavailable = _historical_boundaries(context_root, findings)
    current, known, preflight_identities = _contract_records(
        context_root, historical_exact, findings
    )
    known.update(historical_unavailable)
    findings.extend(_validate_dependencies(current, known, context_root))
    _validate_routes(
        context_root,
        known,
        preflight_identities,
        findings,
    )
    _validate_receipts(context_root, known, historical_unavailable, findings)
    return sorted(set(findings))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed validation for orchestrator context evidence."
    )
    parser.add_argument("--context-root", required=True, type=Path)
    arguments = parser.parse_args(argv)

    findings = validate_context(arguments.context_root)
    for finding in findings:
        print(json.dumps(asdict(finding), sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
