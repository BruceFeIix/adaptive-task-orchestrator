"""Offline consistency checks; neither an executor nor evidence authentication."""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


CAPABILITIES = ("fast_reader", "general_worker", "deep_reasoner", "frontier_reviewer")
EFFORTS = ("low", "medium", "high", "xhigh", "max", "ultra")
PROFILES = ("frugal", "balanced", "quality", "user_pinned")
DISPATCHED = {"accepted", "completed"}
COUNTED = {"planned", "accepted", "completed"}
CAPABILITY = ("enum", CAPABILITIES)
EFFORT = ("enum", EFFORTS)
PAIR = {"model": "text", "effort": EFFORT}
IDENTITY = {"task_id": "text", "task_revision": "positive"}
EFFECTIVE = {
    **PAIR, "source_kind": ("enum", ("runtime-result",)), "source_ref": "text",
    "run_id": "text", "snapshot_id": "text", "worker_id": "text",
}
REQUIREMENT = {
    **IDENTITY, "minimum_capability": CAPABILITY,
    "assurance": ("enum", ("deterministic", "root_check", "independent", "independent_adversarial")),
}
ROUTE = {
    **IDENTITY, "route_id": "text", "snapshot_id": "text", "wave": "nonnegative",
    "worker_id": "text", "profile": ("enum", PROFILES),
    "requested_capability": CAPABILITY, "selected_model": "text", "selected_effort": EFFORT,
    "model_override": "bool", "effort_override": "bool", "fork_turns": "fork",
    "context_complete": "bool", "fallback_chain": ("array", PAIR),
    "dispatch_status": ("enum", ("planned", "accepted", "rejected", "completed", "cancelled")),
    "effective_route": ("nullable", EFFECTIVE), "review_of": ("nullable", "text"),
    "fresh_context": "bool",
}
RUNTIME = {
    "snapshot_id": "text", "run_id": "text", "host_id": "text", "surface": "text",
    "source_ref": "text", "source_kind": ("enum", ("runtime-schema", "runtime-result")),
    "models": ("map", ("unique", EFFORT)), "model_override": "bool", "effort_override": "bool",
    "full_history_with_overrides": "bool", "configuration_overrides": ("enum", ("none", "known", "unknown")),
    "effective_config_reporting": "bool",
    "concurrency": {"limit": "positive", "includes_root": "bool", "root_slots": "positive"},
}
REGISTRY = {
    "schema_version": "positive", "registry_id": "text", "revision": "positive",
    "sources": ("nonempty", "text"), "capabilities": ("array", CAPABILITY),
    "models": ("map", {"capability": CAPABILITY, "family": "text",
        "efforts_by_surface": ("map", ("unique", EFFORT))}),
    "defaults": {profile: {capability: ("unique", "text") for capability in CAPABILITIES}
        for profile in PROFILES[:3]},
}
BUNDLE = {
    "schema_version": "positive", "profile": ("enum", ("runtime-routes-v1",)),
    "run_id": "text", "registry_id": "text", "registry_revision": "positive",
    "runtime": RUNTIME, "requirements": ("array", REQUIREMENT), "routes": ("array", ROUTE),
    "root_only": ("array", {**IDENTITY, "reason": "text", "check_ref": "text"}),
}


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    path: str
    detail: str


def _pointer(path: str, key: str | int) -> str:
    return path + "/" + str(key).replace("~", "~0").replace("/", "~1")


def _shape(value: Any, schema: Any, path: str, findings: list[Finding]) -> None:
    """Walk the fixed schema, never arbitrary input structure or referenced paths."""
    def invalid(detail: str) -> None:
        findings.append(Finding("SCHEMA_INVALID", path, detail))

    if isinstance(schema, dict):
        if not isinstance(value, dict):
            invalid("expected object")
            return
        for key, child_schema in schema.items():
            child_path = _pointer(path, key)
            if key not in value:
                findings.append(Finding("SCHEMA_INVALID", child_path, "required field missing"))
            else:
                _shape(value[key], child_schema, child_path, findings)
        for key in value:
            if not isinstance(key, str):
                invalid("object keys must be strings")
            elif key not in schema:
                findings.append(Finding("SCHEMA_INVALID", _pointer(path, key), "unknown field"))
        return
    if isinstance(schema, tuple):
        kind, child = schema
        if kind == "nullable":
            if value is not None:
                _shape(value, child, path, findings)
        elif kind == "enum":
            if not isinstance(value, str) or value not in child:
                invalid("unsupported enumeration value")
        elif kind == "map":
            if not isinstance(value, dict):
                invalid("expected object map")
                return
            for key, item in value.items():
                if not isinstance(key, str) or not key.strip():
                    invalid("map keys must be nonempty strings")
                else:
                    _shape(item, child, _pointer(path, key), findings)
        else:
            if not isinstance(value, list):
                invalid("expected array")
                return
            if kind in {"nonempty", "unique"} and not value:
                invalid("expected nonempty array")
            for index, item in enumerate(value):
                _shape(item, child, _pointer(path, index), findings)
            # Unique arrays in v1 only contain scalar strings. Check types first.
            if kind == "unique" and all(isinstance(item, str) for item in value):
                if len(set(value)) != len(value):
                    invalid("array values must be unique")
        return
    valid = False
    if schema == "text":
        valid = isinstance(value, str) and bool(value.strip())
    elif schema == "bool":
        valid = isinstance(value, bool)
    elif schema in {"positive", "nonnegative"}:
        valid = type(value) is int and value >= (1 if schema == "positive" else 0)
    elif schema == "fork":
        valid = (isinstance(value, str) and value in {"none", "all"}) or (type(value) is int and value > 0)
    if not valid:
        invalid("expected " + schema)


class _RouteChecks:
    def __init__(self, registry: dict, bundle: dict, findings: list[Finding]):
        self.registry = registry
        self.bundle = bundle
        self.runtime = bundle["runtime"]
        self.models = registry["models"]
        self.findings = findings

    def add(self, code: str, path: str, detail: str) -> None:
        self.findings.append(Finding(code, path, detail))

    def rank(self, model: str) -> int | None:
        record = self.models.get(model)
        return CAPABILITIES.index(record["capability"]) if record is not None else None

    def pair(self, model: str, effort: str, floor: int, path: str,
             model_field: str = "model", effort_field: str = "effort") -> int | None:
        record = self.models.get(model)
        surface_efforts = record["efforts_by_surface"].get(self.runtime["surface"]) if record else None
        host_efforts = self.runtime["models"].get(model)
        if surface_efforts is None or host_efforts is None:
            self.add("MODEL_UNAVAILABLE", _pointer(path, model_field), "model not in registry/runtime surface intersection")
        elif effort not in surface_efforts or effort not in host_efforts:
            self.add("EFFORT_UNAVAILABLE", _pointer(path, effort_field), "effort not in registry/runtime surface intersection")
        rank = self.rank(model)
        if rank is not None and rank < floor:
            self.add("CAPABILITY_FLOOR", _pointer(path, model_field), "model below minimum or requested capability")
        return rank

    def registry_rules(self) -> None:
        if self.registry["capabilities"] != list(CAPABILITIES):
            self.add("REGISTRY_INVALID", "/registry/capabilities", "capabilities must match the ordered v1 aliases")
        for profile, choices in self.registry["defaults"].items():
            for capability, models in choices.items():
                for index, model in enumerate(models):
                    rank = self.rank(model)
                    if rank is None or rank < CAPABILITIES.index(capability):
                        path = _pointer(_pointer("/registry/defaults", profile), capability)
                        self.add("REGISTRY_INVALID", _pointer(path, index), "default candidate must exist and satisfy capability")
        for key, registry_key in (("registry_id", "registry_id"), ("registry_revision", "revision")):
            if self.bundle[key] != self.registry[registry_key]:
                self.add("REGISTRY_MISMATCH", "/bundle/" + key, "bundle must reference the supplied registry revision")
        if self.runtime["run_id"] != self.bundle["run_id"]:
            self.add("SNAPSHOT_MISMATCH", "/bundle/runtime/run_id", "runtime must belong to the enclosing run")

    def planned(self, route: dict, requirement: dict, path: str) -> int:
        minimum = CAPABILITIES.index(requirement["minimum_capability"])
        requested = CAPABILITIES.index(route["requested_capability"])
        floor = max(minimum, requested)
        if requested < minimum:
            self.add("CAPABILITY_FLOOR", path + "/requested_capability", "requested capability below minimum")
        self.pair(route["selected_model"], route["selected_effort"], floor, path, "selected_model", "selected_effort")
        if route["snapshot_id"] != self.runtime["snapshot_id"]:
            self.add("SNAPSHOT_MISMATCH", path + "/snapshot_id", "route must reference the supplied runtime snapshot")
        for field in ("model_override", "effort_override"):
            if route[field] and not self.runtime[field]:
                self.add("OVERRIDE_UNSUPPORTED", path + "/" + field, "override is not supported by runtime")
        if route["model_override"] or route["effort_override"]:
            if route["fork_turns"] == "all":
                if not self.runtime["full_history_with_overrides"]:
                    self.add("HISTORY_CONFLICT", path + "/fork_turns", "full history with overrides is not supported")
            elif not route["context_complete"]:
                self.add("CONTEXT_INCOMPLETE", path + "/context_complete", "overridden no/bounded-history worker needs complete context")
        self.fallback(route, floor, path)
        return floor

    def fallback(self, route: dict, floor: int, path: str) -> None:
        if route["profile"] == "user_pinned" and route["fallback_chain"]:
            self.add("PIN_VIOLATION", path + "/fallback_chain", "pinned route cannot have fallback candidates")
        previous = (route["selected_model"], route["selected_effort"])
        seen = {previous}
        for index, candidate in enumerate(route["fallback_chain"]):
            candidate_path = _pointer(path + "/fallback_chain", index)
            pair = (candidate["model"], candidate["effort"])
            rank = self.pair(*pair, floor, candidate_path)
            previous_rank = self.rank(previous[0])
            if pair in seen:
                self.add("FALLBACK_INVALID", candidate_path, "candidate pair repeats selected or prior fallback")
            if rank is not None and previous_rank is not None:
                if rank < previous_rank or (rank == previous_rank and EFFORTS.index(pair[1]) < EFFORTS.index(previous[1])):
                    self.add("FALLBACK_INVALID", candidate_path, "fallback must not lower capability or same-tier effort")
            previous = pair
            seen.add(pair)

    def effective(self, route: dict, requirement: dict, floor: int, path: str) -> None:
        value = route["effective_route"]
        dispatched = route["dispatch_status"] in DISPATCHED
        high_risk = (CAPABILITIES.index(requirement["minimum_capability"]) >= 2
            or requirement["assurance"] == "independent_adversarial")
        effective_path = path + "/effective_route"
        if value is None:
            if dispatched and high_risk:
                self.add("EFFECTIVE_ROUTE_UNATTESTED", effective_path, "high-risk dispatch requires effective configuration evidence")
            return
        if not dispatched:
            self.add("DISPATCH_INVALID", effective_path, "only accepted/completed dispatches may carry effective evidence")
        if not self.runtime["effective_config_reporting"]:
            self.add("EFFECTIVE_ROUTE_UNATTESTED", effective_path, "runtime does not report effective configuration")
        expected = {"run_id": self.bundle["run_id"], "snapshot_id": self.runtime["snapshot_id"],
            "worker_id": route["worker_id"]}
        for key, identity in expected.items():
            if value[key] != identity:
                self.add("SNAPSHOT_MISMATCH", effective_path + "/" + key, "effective evidence identity does not match run/snapshot/worker")
        self.pair(value["model"], value["effort"], floor, effective_path)
        if (value["model"], value["effort"]) != (route["selected_model"], route["selected_effort"]):
            if route["profile"] == "user_pinned":
                self.add("PIN_VIOLATION", effective_path, "effective configuration must match pinned model and effort")
            elif self.runtime["configuration_overrides"] == "none":
                self.add("EFFECTIVE_ROUTE_MISMATCH", effective_path, "effective configuration differs without configuration overrides")

    def review(self, route: dict, authors: dict, path: str) -> None:
        author_id = route["review_of"]
        if author_id is None:
            return
        author = authors.get(author_id)
        if author is None:
            self.add("REVIEW_INVALID", path + "/review_of", "review author route does not exist")
            return
        if author["worker_id"] == route["worker_id"]:
            self.add("REVIEW_INVALID", path + "/worker_id", "reviewer must be a different worker")
        if not route["fresh_context"]:
            self.add("REVIEW_INVALID", path + "/fresh_context", "review requires fresh context")
        if route["dispatch_status"] in DISPATCHED:
            if author["dispatch_status"] not in DISPATCHED:
                self.add("REVIEW_INVALID", path + "/review_of", "executed review requires an accepted/completed author")
            if route["effective_route"] is None or author["effective_route"] is None:
                self.add("REVIEW_UNATTESTED", path + "/review_of", "executed review requires both effective identities")
                return
            reviewer_rank = self.rank(route["effective_route"]["model"])
            author_rank = self.rank(author["effective_route"]["model"])
        else:
            reviewer_rank = self.rank(route["selected_model"])
            author_rank = self.rank(author["selected_model"])
        if reviewer_rank is not None and author_rank is not None and reviewer_rank < author_rank:
            self.add("REVIEW_INVALID", path + "/review_of", "reviewer capability is below author capability")

    def review_cycles(self, authors: dict, paths: dict) -> None:
        finished: set[str] = set()
        for start in authors:
            trail: list[str] = []
            positions: dict[str, int] = {}
            node = start
            while node in authors and node not in finished:
                if node in positions:
                    for member in trail[positions[node]:]:
                        self.add("REVIEW_INVALID", paths[member] + "/review_of", "review relationship contains a cycle")
                    break
                positions[node] = len(trail)
                trail.append(node)
                node = authors[node]["review_of"]
            finished.update(trail)

    def run(self) -> None:
        self.registry_rules()
        requirements: dict = {}
        for index, item in enumerate(self.bundle["requirements"]):
            identity = (item["task_id"], item["task_revision"])
            if identity in requirements:
                self.add("IDENTITY_DUPLICATE", _pointer("/bundle/requirements", index), "task identity must be unique")
            requirements[identity] = item

        covered: set = set()
        authors: dict = {}
        paths: dict = {}
        workers: set = set()
        waves: dict[int, int] = {}
        for collection in ("routes", "root_only"):
            for index, item in enumerate(self.bundle[collection]):
                path = _pointer("/bundle/" + collection, index)
                identity = (item["task_id"], item["task_revision"])
                requirement = requirements.get(identity)
                if requirement is None:
                    self.add("TASK_IDENTITY_MISMATCH", path, "record must match a declared task identity and revision")
                if identity in covered:
                    self.add("IDENTITY_DUPLICATE", path, "task identity may have only one route or root-only record")
                covered.add(identity)
                if collection == "root_only":
                    if requirement is not None and (CAPABILITIES.index(requirement["minimum_capability"]) >= 2
                            or requirement["assurance"] not in {"deterministic", "root_check"}):
                        self.add("ROOT_ONLY_INELIGIBLE", path, "root-only record requires low-risk deterministic/root-check work")
                    continue
                if item["route_id"] in authors:
                    self.add("IDENTITY_DUPLICATE", path + "/route_id", "route identity must be unique")
                else:
                    authors[item["route_id"]] = item
                    paths[item["route_id"]] = path
                worker = (item["wave"], item["worker_id"])
                if worker in workers:
                    self.add("WORKER_DUPLICATE", path + "/worker_id", "worker identity must be unique within a wave")
                workers.add(worker)
                if item["dispatch_status"] in COUNTED:
                    waves[item["wave"]] = waves.get(item["wave"], 0) + 1
                if requirement is not None:
                    floor = self.planned(item, requirement, path)
                    self.effective(item, requirement, floor, path)
        for index, item in enumerate(self.bundle["requirements"]):
            if (item["task_id"], item["task_revision"]) not in covered:
                self.add("REQUIREMENT_UNCOVERED", _pointer("/bundle/requirements", index), "requirement needs a route or root-only record")
        concurrency = self.runtime["concurrency"]
        capacity = concurrency["limit"] - (concurrency["root_slots"] if concurrency["includes_root"] else 0)
        if capacity < 0:
            self.add("CONCURRENCY_INVALID", "/bundle/runtime/concurrency", "root slots exceed the total capacity")
        elif any(count > capacity for count in waves.values()):
            self.add("CONCURRENCY_EXCEEDED", "/bundle/routes", "concurrent wave exceeds normalized child capacity")
        for index, item in enumerate(self.bundle["routes"]):
            self.review(item, authors, _pointer("/bundle/routes", index))
        self.review_cycles(authors, paths)


def validate_runtime_routes(registry: dict, bundle: dict) -> list[Finding]:
    """Return stable findings without mutating inputs or reading external state."""
    findings: list[Finding] = []
    _shape(registry, REGISTRY, "/registry", findings)
    _shape(bundle, BUNDLE, "/bundle", findings)
    if findings:
        return sorted(set(findings))
    for path, value in (("/registry", registry), ("/bundle", bundle)):
        if value["schema_version"] != 1:
            findings.append(Finding("VERSION_UNSUPPORTED", path + "/schema_version", "expected schema version 1"))
    if findings:
        return sorted(set(findings))
    _RouteChecks(registry, bundle, findings).run()
    return sorted(set(findings))


def _strict_object(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("nonfinite number")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite number")
    return number


def _read_json(file: str, path: str) -> tuple[dict | None, list[Finding]]:
    try:
        raw = Path(file).read_bytes()
    except (OSError, ValueError):
        return None, [Finding("INPUT_READ_ERROR", path, "input file could not be read")]
    try:
        # Decimal preserves JSON integers without Python 3.11's text-to-int limit.
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object,
            parse_constant=_reject_constant, parse_float=_finite_float,
            parse_int=lambda token: int(Decimal(token)))
        if not isinstance(value, dict):
            raise ValueError("expected object")
    except (ValueError, RecursionError):
        return None, [Finding("JSON_INVALID", path, "expected strict UTF-8 JSON object")]
    return value, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--bundle", required=True)
    args = parser.parse_args(argv)
    registry, registry_errors = _read_json(args.registry, "/registry")
    bundle, bundle_errors = _read_json(args.bundle, "/bundle")
    findings = registry_errors + bundle_errors
    if not findings:
        findings = validate_runtime_routes(registry, bundle)
    for finding in sorted(set(findings)):
        line = json.dumps(asdict(finding), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        sys.stdout.buffer.write((line + "\n").encode("ascii"))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
