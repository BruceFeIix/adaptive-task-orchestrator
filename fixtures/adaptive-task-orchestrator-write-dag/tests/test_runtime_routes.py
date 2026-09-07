from __future__ import annotations

import copy
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
CAPABILITIES = ["fast_reader", "general_worker", "deep_reasoner", "frontier_reviewer"]
MODELS = ["gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol", "gpt-6-astra"]
EFFORTS = ["low", "medium", "high", "xhigh", "max", "ultra"]
SURFACE = "codex.collaboration"


def registry() -> dict:
    return {
        "schema_version": 1, "registry_id": "test-policy", "revision": 1,
        "sources": ["Explicit synthetic runtime fixture; not an observed model run."],
        "capabilities": CAPABILITIES.copy(),
        "models": {model: {"capability": capability, "family": model,
            "efforts_by_surface": {SURFACE: EFFORTS.copy()}}
            for model, capability in zip(MODELS, CAPABILITIES)},
        "defaults": {profile: {capability: [model] for model, capability in zip(MODELS, CAPABILITIES)}
            for profile in ("frugal", "balanced", "quality")},
    }


def requirement(task_id: str = "task", capability: str = "general_worker") -> dict:
    return {"task_id": task_id, "task_revision": 1, "minimum_capability": capability, "assurance": "root_check"}


def route(task_id: str = "task", model: str = "gpt-5.6-terra") -> dict:
    return {
        "route_id": task_id + "-route", "task_id": task_id, "task_revision": 1,
        "snapshot_id": "snapshot-1", "wave": 0, "worker_id": task_id + "-worker",
        "profile": "balanced", "requested_capability": "general_worker",
        "selected_model": model, "selected_effort": "high", "model_override": True,
        "effort_override": True, "fork_turns": "none", "context_complete": True,
        "fallback_chain": [], "dispatch_status": "planned", "effective_route": None,
        "review_of": None, "fresh_context": True,
    }


def bundle() -> dict:
    return {
        "schema_version": 1, "profile": "runtime-routes-v1", "run_id": "run-1",
        "registry_id": "test-policy", "registry_revision": 1,
        "runtime": {"snapshot_id": "snapshot-1", "run_id": "run-1", "host_id": "test-host",
            "surface": SURFACE, "source_kind": "runtime-schema", "source_ref": "synthetic-tool-schema",
            "models": {model: EFFORTS.copy() for model in MODELS},
            "model_override": True, "effort_override": True, "full_history_with_overrides": False,
            "configuration_overrides": "none", "effective_config_reporting": True,
            "concurrency": {"limit": 4, "includes_root": True, "root_slots": 1}},
        "requirements": [requirement()], "routes": [route()], "root_only": [],
    }


def effective(value: dict, model: str | None = None, effort: str | None = None) -> dict:
    return {"model": model or value["selected_model"], "effort": effort or value["selected_effort"],
        "source_kind": "runtime-result", "source_ref": "synthetic-result",
        "run_id": "run-1", "snapshot_id": "snapshot-1", "worker_id": value["worker_id"]}


class RuntimeRouteTests(unittest.TestCase):
    def validate(self, data: dict, policy: dict | None = None):
        module = importlib.import_module("validate_runtime_routes")
        return module.validate_runtime_routes(registry() if policy is None else policy, data)

    def assert_valid(self, data: dict, policy: dict | None = None) -> None:
        before = copy.deepcopy(data)
        selected_policy = registry() if policy is None else policy
        policy_before = copy.deepcopy(selected_policy)
        self.assertEqual(self.validate(data, selected_policy), [])
        self.assertEqual(self.validate(data, selected_policy), [])
        self.assertEqual(data, before)
        self.assertEqual(selected_policy, policy_before)

    def assert_invalid(self, data: dict, code: str, policy: dict | None = None) -> None:
        before = copy.deepcopy(data)
        findings = self.validate(data, policy)
        self.assertIn(code, [finding.code for finding in findings])
        self.assertEqual(findings, sorted(set(findings)))
        self.assertEqual([asdict(item) for item in findings], [asdict(item) for item in self.validate(data, policy)])
        self.assertTrue(all(item.path.startswith(("/bundle", "/registry")) and item.detail for item in findings))
        self.assertEqual(data, before)

    def test_planned_and_unfinished_records_do_not_claim_completion(self):
        for state in ("planned", "accepted", "completed", "rejected", "cancelled"):
            with self.subTest(state=state):
                data = bundle()
                data["routes"][0]["dispatch_status"] = state
                self.assert_valid(data)

    def test_selected_pair_meets_floor_and_requested_capability(self):
        data = bundle()
        data["requirements"][0]["minimum_capability"] = "frontier_reviewer"
        data["routes"][0]["requested_capability"] = "frontier_reviewer"
        data["routes"][0]["selected_model"] = MODELS[0]
        self.assert_invalid(data, "CAPABILITY_FLOOR")
        data["routes"][0]["selected_model"] = MODELS[3]
        self.assert_valid(data)
        data["routes"][0]["requested_capability"] = "general_worker"
        self.assert_invalid(data, "CAPABILITY_FLOOR")

    def test_selected_unknown_or_unavailable_model_and_effort(self):
        for model, effort, code in (("unknown", "high", "MODEL_UNAVAILABLE"),
                (MODELS[1], "none", "SCHEMA_INVALID"), (MODELS[1], "ultra", "EFFORT_UNAVAILABLE")):
            with self.subTest(model=model, effort=effort):
                data = bundle()
                data["runtime"]["models"][MODELS[1]] = ["high"]
                data["routes"][0].update(selected_model=model, selected_effort=effort)
                self.assert_invalid(data, code)
        data = bundle()
        data["runtime"]["models"]["future-model"] = ["high"]
        self.assert_valid(data)

    def test_surface_support_intersection(self):
        policy = registry()
        policy["models"][MODELS[1]]["efforts_by_surface"] = {"responses-api": ["high"]}
        self.assert_invalid(bundle(), "MODEL_UNAVAILABLE", policy)
        policy = registry()
        policy["models"][MODELS[1]]["efforts_by_surface"][SURFACE] = ["low"]
        self.assert_invalid(bundle(), "EFFORT_UNAVAILABLE", policy)

    def test_version_registry_and_snapshot_bindings(self):
        for field, value, code in (("schema_version", 2, "VERSION_UNSUPPORTED"),
                ("registry_revision", 2, "REGISTRY_MISMATCH"), ("registry_id", "other", "REGISTRY_MISMATCH")):
            with self.subTest(field=field):
                data = bundle(); data[field] = value
                self.assert_invalid(data, code)
        for target in ("runtime", "route"):
            data = bundle()
            if target == "runtime": data["runtime"]["run_id"] = "other"
            else: data["routes"][0]["snapshot_id"] = "other"
            self.assert_invalid(data, "SNAPSHOT_MISMATCH")

    def test_overrides_fork_and_context(self):
        for field in ("model_override", "effort_override"):
            data = bundle(); data["runtime"][field] = False
            self.assert_invalid(data, "OVERRIDE_UNSUPPORTED")
        data = bundle(); data["routes"][0]["fork_turns"] = "all"
        self.assert_invalid(data, "HISTORY_CONFLICT")
        data["runtime"]["full_history_with_overrides"] = True
        self.assert_valid(data)
        for fork in ("none", 2):
            data = bundle(); data["routes"][0].update(fork_turns=fork, context_complete=False)
            self.assert_invalid(data, "CONTEXT_INCOMPLETE")

    def test_fallback_starts_at_selected_pair_and_never_downgrades(self):
        for selected, alternatives in ((MODELS[3], [{"model": MODELS[1], "effort": "high"}]),
                (MODELS[1], [{"model": MODELS[1], "effort": "low"}]),
                (MODELS[1], [{"model": MODELS[1], "effort": "high"}])):
            data = bundle(); data["routes"][0].update(selected_model=selected, fallback_chain=alternatives)
            self.assert_invalid(data, "FALLBACK_INVALID")
        data = bundle()
        data["routes"][0]["fallback_chain"] = [{"model": MODELS[2], "effort": "low"}, {"model": MODELS[3], "effort": "high"}]
        self.assert_valid(data)

    def test_exact_user_pin_survives_known_configuration_override(self):
        data = bundle(); value = data["routes"][0]
        data["runtime"]["configuration_overrides"] = "known"
        value.update(profile="user_pinned", selected_model=MODELS[3], dispatch_status="completed")
        value["effective_route"] = effective(value, MODELS[2])
        self.assert_invalid(data, "PIN_VIOLATION")
        value["effective_route"] = effective(value, effort="medium")
        self.assert_invalid(data, "PIN_VIOLATION")
        value["effective_route"] = effective(value)
        self.assert_valid(data)
        value["fallback_chain"] = [{"model": MODELS[3], "effort": "xhigh"}]
        self.assert_invalid(data, "PIN_VIOLATION")

    def test_high_risk_dispatch_requires_effective_evidence(self):
        for state in ("accepted", "completed"):
            data = bundle(); value = data["routes"][0]
            data["requirements"][0]["minimum_capability"] = "deep_reasoner"
            value.update(selected_model=MODELS[2], requested_capability="deep_reasoner", dispatch_status=state)
            self.assert_invalid(data, "EFFECTIVE_ROUTE_UNATTESTED")
            value["effective_route"] = effective(value)
            self.assert_valid(data)

    def test_effective_source_binding_reporting_and_override(self):
        data = bundle(); value = data["routes"][0]
        value.update(dispatch_status="completed", effective_route=effective(value))
        self.assert_valid(data)
        for key, wrong in (("run_id", "other"), ("snapshot_id", "other"), ("worker_id", "other")):
            changed = copy.deepcopy(data); changed["routes"][0]["effective_route"][key] = wrong
            self.assert_invalid(changed, "SNAPSHOT_MISMATCH")
        changed = copy.deepcopy(data); changed["runtime"]["effective_config_reporting"] = False
        self.assert_invalid(changed, "EFFECTIVE_ROUTE_UNATTESTED")
        changed = copy.deepcopy(data); changed["routes"][0]["effective_route"]["source_kind"] = "runtime-schema"
        self.assert_invalid(changed, "SCHEMA_INVALID")
        changed = copy.deepcopy(data); changed["routes"][0]["dispatch_status"] = "planned"
        self.assert_invalid(changed, "DISPATCH_INVALID")
        changed = copy.deepcopy(data); changed["routes"][0]["effective_route"]["model"] = MODELS[3]
        self.assert_invalid(changed, "EFFECTIVE_ROUTE_MISMATCH")
        changed["runtime"]["configuration_overrides"] = "known"
        self.assert_valid(changed)

    def test_concurrency_counting_conventions(self):
        data = bundle()
        data["requirements"] = [requirement(str(index)) for index in range(4)]
        data["routes"] = [route(str(index)) for index in range(4)]
        self.assert_invalid(data, "CONCURRENCY_EXCEEDED")
        data["runtime"]["concurrency"]["includes_root"] = False
        self.assert_valid(data)
        data["runtime"]["concurrency"]["includes_root"] = True
        data["routes"][3]["dispatch_status"] = "cancelled"
        self.assert_valid(data)

    def test_review_planning_and_effective_comparisons(self):
        data = bundle()
        author = data["routes"][0]
        review = route("review", MODELS[3]); review["review_of"] = author["route_id"]
        data["requirements"].append(requirement("review")); data["routes"].append(review)
        self.assert_valid(data)
        review["worker_id"] = author["worker_id"]
        self.assert_invalid(data, "REVIEW_INVALID")
        review["worker_id"] = "review-worker"; review["fresh_context"] = False
        self.assert_invalid(data, "REVIEW_INVALID")
        review["fresh_context"] = True; review["dispatch_status"] = "completed"
        self.assert_invalid(data, "REVIEW_UNATTESTED")
        author["dispatch_status"] = "completed"
        author["effective_route"] = effective(author)
        review["effective_route"] = effective(review)
        self.assert_valid(data)
        data["runtime"]["configuration_overrides"] = "known"
        author["effective_route"]["model"] = MODELS[3]
        review["effective_route"]["model"] = MODELS[1]
        self.assert_invalid(data, "REVIEW_INVALID")

    def test_review_cycles_and_unknown_author(self):
        data = bundle(); data["routes"][0]["review_of"] = "missing"
        self.assert_invalid(data, "REVIEW_INVALID")
        data["routes"][0]["review_of"] = "task-route"
        self.assert_invalid(data, "REVIEW_INVALID")

    def test_root_only_is_low_risk_and_explicitly_checked(self):
        data = bundle(); data["routes"] = []
        data["root_only"] = [{"task_id": "task", "task_revision": 1, "reason": "No subagent tool", "check_ref": "root-check-1"}]
        self.assert_valid(data)
        data["requirements"][0]["minimum_capability"] = "deep_reasoner"
        self.assert_invalid(data, "ROOT_ONLY_INELIGIBLE")

    def test_duplicate_identity_and_uncovered_requirements(self):
        data = bundle(); data["routes"] = []
        self.assert_invalid(data, "REQUIREMENT_UNCOVERED")
        data = bundle(); data["requirements"].append(copy.deepcopy(data["requirements"][0]))
        self.assert_invalid(data, "IDENTITY_DUPLICATE")
        data = bundle(); data["routes"][0]["task_revision"] = 2
        self.assert_invalid(data, "TASK_IDENTITY_MISMATCH")

    def test_malformed_nested_types_fail_without_crashing(self):
        for bad in (None, True, [], "string", 5):
            with self.subTest(bad=bad):
                self.assert_invalid(bad, "SCHEMA_INVALID")
                data = bundle(); data["runtime"] = bad
                self.assert_invalid(data, "SCHEMA_INVALID")
                data = bundle(); data["routes"][0]["effective_route"] = bad
                if bad is not None: self.assert_invalid(data, "SCHEMA_INVALID")
        data = bundle(); data["routes"][0]["task_revision"] = True
        self.assert_invalid(data, "SCHEMA_INVALID")
        data = bundle(); data["extra"] = "unknown"
        self.assert_invalid(data, "SCHEMA_INVALID")

    def test_cli_exact_bytes_json_failures_and_usage(self):
        self.validate(bundle())  # RED must fail for the missing module, not a missing CLI path.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); policy_file = root / "registry.json"; bundle_file = root / "bundle.json"
            policy_file.write_text(json.dumps(registry()), encoding="utf-8")
            bundle_file.write_text(json.dumps(bundle()), encoding="utf-8")
            command = [sys.executable, "-B", str(TOOLS / "validate_runtime_routes.py"), "--registry", str(policy_file), "--bundle", str(bundle_file)]
            success = subprocess.run(command, capture_output=True, check=False)
            self.assertEqual((success.returncode, success.stdout, success.stderr), (0, b"", b""))
            for raw in (b'{"schema_version":1,"schema_version":1}', b'{"value":NaN}', b'\xff', b'{'):
                bundle_file.write_bytes(raw)
                actual = subprocess.run(command, capture_output=True, check=False)
                self.assertEqual(actual.returncode, 1)
                self.assertEqual(actual.stderr, b"")
                self.assertEqual(actual.stdout, b'{"code":"JSON_INVALID","detail":"expected strict UTF-8 JSON object","path":"/bundle"}\n')
            bundle_file.unlink()
            missing = subprocess.run(command, capture_output=True, check=False)
            self.assertEqual(missing.stdout, b'{"code":"INPUT_READ_ERROR","detail":"input file could not be read","path":"/bundle"}\n')
            self.assertEqual(missing.returncode, 1)
            usage = subprocess.run([sys.executable, "-B", str(TOOLS / "validate_runtime_routes.py")], capture_output=True, check=False)
            self.assertEqual(usage.returncode, 2)


if __name__ == "__main__":
    unittest.main()
