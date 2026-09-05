from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_runtime_routes import CAPABILITIES, EFFORTS, MODELS, SURFACE, TOOLS
from test_runtime_routes import bundle, effective, registry, requirement, route
import validate_runtime_routes as checker


class RuntimeRouteHardeningTests(unittest.TestCase):
    def check(self, data, code=None, policy=None):
        policy = registry() if policy is None else policy
        before = copy.deepcopy((policy, data))
        results = checker.validate_runtime_routes(policy, data)
        if code is None:
            self.assertEqual(results, [])
        else:
            self.assertIn(code, [item.code for item in results])
        self.assertEqual(results, sorted(set(results)))
        self.assertEqual(results, checker.validate_runtime_routes(policy, data))
        self.assertEqual((policy, data), before)
        return results

    def test_registry_shapes_versions_and_candidate_policy(self):
        cases = [
            (("schema_version",), True, "SCHEMA_INVALID"),
            (("schema_version",), 2, "VERSION_UNSUPPORTED"),
            (("revision",), False, "SCHEMA_INVALID"),
            (("sources",), [], "SCHEMA_INVALID"),
            (("capabilities",), CAPABILITIES[::-1], "REGISTRY_INVALID"),
            (("models",), [], "SCHEMA_INVALID"),
            (("models", MODELS[0], "capability"), "unknown", "SCHEMA_INVALID"),
            (("models", MODELS[0], "family"), " ", "SCHEMA_INVALID"),
            (("models", MODELS[0], "efforts_by_surface", SURFACE), ["none"], "SCHEMA_INVALID"),
            (("models", MODELS[0], "efforts_by_surface", SURFACE), ["high", "high"], "SCHEMA_INVALID"),
            (("defaults", "balanced", "general_worker"), [], "SCHEMA_INVALID"),
            (("defaults", "balanced", "general_worker"), ["unknown"], "REGISTRY_INVALID"),
            (("defaults", "balanced", "general_worker"), [MODELS[0]], "REGISTRY_INVALID"),
        ]
        for keys, bad, code in cases:
            with self.subTest(keys=keys, bad=bad):
                policy = registry()
                target = policy
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = bad
                self.check(bundle(), code, policy)
        for bad in (None, [], "registry", True, 7):
            self.assertTrue(checker.validate_runtime_routes(bad, bundle()))

    def test_every_required_record_field_missing_or_unknown(self):
        data = bundle()
        data["routes"][0].update(dispatch_status="completed", effective_route=effective(data["routes"][0]))
        object_paths = [(), ("runtime",), ("runtime", "concurrency"), ("requirements", 0),
            ("routes", 0), ("routes", 0, "effective_route")]
        for keys in object_paths:
            target = data
            for key in keys:
                target = target[key]
            for missing in target:
                with self.subTest(keys=keys, missing=missing):
                    changed = copy.deepcopy(data)
                    child = changed
                    for key in keys:
                        child = child[key]
                    del child[missing]
                    self.check(changed, "SCHEMA_INVALID")
            changed = copy.deepcopy(data)
            child = changed
            for key in keys:
                child = child[key]
            child["unexpected"] = True
            self.check(changed, "SCHEMA_INVALID")

    def test_nested_wrong_types_and_bool_integer_boundaries(self):
        for key in ("requirements", "routes", "root_only"):
            for bad in (None, {}, True, "array", [False]):
                data = bundle(); data[key] = bad
                self.check(data, "SCHEMA_INVALID")
        for key in ("task_revision", "wave", "fork_turns"):
            for bad in (True, False, -1, 1.5, [], {}):
                data = bundle(); data["routes"][0][key] = bad
                self.check(data, "SCHEMA_INVALID")
        for key in ("model_override", "effort_override", "fresh_context", "context_complete"):
            data = bundle(); data["routes"][0][key] = 1
            self.check(data, "SCHEMA_INVALID")
        data = bundle(); data["runtime"]["models"][MODELS[0]] = []
        self.check(data, "SCHEMA_INVALID")

    def test_selected_capability_cartesian_floor_matrix(self):
        for minimum in range(4):
            for requested in range(4):
                for selected in range(4):
                    with self.subTest(minimum=minimum, requested=requested, selected=selected):
                        data = bundle()
                        data["requirements"][0]["minimum_capability"] = CAPABILITIES[minimum]
                        data["routes"][0].update(requested_capability=CAPABILITIES[requested], selected_model=MODELS[selected])
                        self.check(data, None if requested >= minimum and selected >= requested else "CAPABILITY_FLOOR")

    def test_fallback_and_effective_candidates_obey_intersection_and_both_floors(self):
        for model, effort, code in (("missing", "high", "MODEL_UNAVAILABLE"),
                (MODELS[2], "ultra", "EFFORT_UNAVAILABLE"), (MODELS[0], "high", "CAPABILITY_FLOOR")):
            for location in ("fallback", "effective"):
                data = bundle(); value = data["routes"][0]
                data["runtime"]["models"][MODELS[2]] = ["high"]
                data["runtime"]["configuration_overrides"] = "known"
                if location == "fallback":
                    value["fallback_chain"] = [{"model": model, "effort": effort}]
                else:
                    value.update(dispatch_status="completed", effective_route=effective(value, model, effort))
                self.check(data, code)
        data = bundle(); value = data["routes"][0]
        value.update(selected_model=MODELS[3], requested_capability="frontier_reviewer", dispatch_status="completed")
        value["effective_route"] = effective(value, MODELS[2])
        data["runtime"]["configuration_overrides"] = "known"
        self.check(data, "CAPABILITY_FLOOR")

    def test_unknown_override_and_adversarial_assurance_are_not_attestation(self):
        data = bundle(); value = data["routes"][0]
        data["requirements"][0]["assurance"] = "independent_adversarial"
        data["runtime"]["configuration_overrides"] = "unknown"
        value["dispatch_status"] = "accepted"
        self.check(data, "EFFECTIVE_ROUTE_UNATTESTED")
        value["effective_route"] = effective(value)
        self.check(data)
        data["runtime"]["effective_config_reporting"] = False
        self.check(data, "EFFECTIVE_ROUTE_UNATTESTED")

    def test_effective_records_for_rejected_and_cancelled_dispatches_are_invalid(self):
        for state in ("rejected", "cancelled"):
            data = bundle(); value = data["routes"][0]
            value.update(dispatch_status=state, effective_route=effective(value))
            self.check(data, "DISPATCH_INVALID")

    def test_no_override_does_not_require_full_context(self):
        for fork in ("all", "none", 2):
            data = bundle()
            data["runtime"].update(model_override=False, effort_override=False)
            data["routes"][0].update(model_override=False, effort_override=False, context_complete=False, fork_turns=fork)
            self.check(data)

    def test_capacity_zero_and_root_counting_boundaries(self):
        data = bundle()
        data["runtime"]["concurrency"].update(limit=1, root_slots=1)
        self.check(data, "CONCURRENCY_EXCEEDED")
        data["routes"][0]["dispatch_status"] = "rejected"
        self.check(data)
        data["runtime"]["concurrency"]["root_slots"] = 2
        self.check(data, "CONCURRENCY_INVALID")
        data["runtime"]["concurrency"]["includes_root"] = False
        data["routes"][0]["dispatch_status"] = "completed"
        self.check(data)

    def test_worker_reuse_allowed_between_waves_not_within_a_wave(self):
        data = bundle()
        data["requirements"].append(requirement("second"))
        second = route("second"); second["worker_id"] = data["routes"][0]["worker_id"]
        data["routes"].append(second)
        self.check(data, "WORKER_DUPLICATE")
        second["wave"] = 1
        self.check(data)

    def test_declared_subset_coverage_and_root_only_constraints(self):
        data = bundle(); data.update(requirements=[], routes=[])
        self.check(data)
        root_record = {"task_id": "task", "task_revision": 1, "reason": "bounded root check", "check_ref": "check-1"}
        data = bundle(); data["root_only"] = [root_record]
        self.check(data, "IDENTITY_DUPLICATE")
        data["routes"] = []; data["runtime"]["models"] = {}
        self.check(data)
        for assurance in ("independent", "independent_adversarial"):
            data["requirements"][0]["assurance"] = assurance
            self.check(data, "ROOT_ONLY_INELIGIBLE")
        data["requirements"][0]["assurance"] = "root_check"
        for key in ("task_id", "task_revision", "reason", "check_ref"):
            changed = copy.deepcopy(data); del changed["root_only"][0][key]
            self.check(changed, "SCHEMA_INVALID")

    def test_duplicate_routes_and_root_records_do_not_hide_coverage(self):
        data = bundle(); data["routes"].append(copy.deepcopy(data["routes"][0]))
        self.check(data, "IDENTITY_DUPLICATE")
        data = bundle(); data["requirements"].append(requirement("second"))
        value = route("second"); value["route_id"] = data["routes"][0]["route_id"]
        data["routes"].append(value)
        self.check(data, "IDENTITY_DUPLICATE")
        data = bundle(); data["routes"] = []
        data["root_only"] = [{"task_id": "missing", "task_revision": 1, "reason": "check", "check_ref": "check-1"}]
        self.check(data, "TASK_IDENTITY_MISMATCH")
        self.check(data, "REQUIREMENT_UNCOVERED")

    def test_review_capability_uses_selected_or_both_effective_models(self):
        data = bundle(); author = data["routes"][0]
        author["selected_model"] = MODELS[3]
        reviewer = route("review"); reviewer["review_of"] = author["route_id"]
        data["routes"].append(reviewer); data["requirements"].append(requirement("review"))
        self.check(data, "REVIEW_INVALID")
        reviewer["selected_model"] = MODELS[3]
        self.check(data)
        author["dispatch_status"] = "completed"; author["effective_route"] = effective(author)
        reviewer["dispatch_status"] = "completed"
        self.check(data, "REVIEW_UNATTESTED")
        reviewer["effective_route"] = effective(reviewer)
        self.check(data)
        author["effective_route"] = None
        self.check(data, "REVIEW_UNATTESTED")
        author["dispatch_status"] = "cancelled"
        self.check(data, "REVIEW_INVALID")

    def test_review_graph_long_chain_and_cycle_do_not_recurse(self):
        data = bundle(); count = 1100
        data["requirements"] = [requirement(str(index)) for index in range(count)]
        data["routes"] = [route(str(index)) for index in range(count)]
        data["runtime"]["concurrency"]["limit"] = count + 1
        for index in range(1, count):
            data["routes"][index]["review_of"] = data["routes"][index - 1]["route_id"]
        self.check(data)
        data["routes"][0]["review_of"] = data["routes"][-1]["route_id"]
        results = self.check(data, "REVIEW_INVALID")
        self.assertEqual(len(results), count)

    def test_literal_complete_diagnostics_and_escaped_json_pointer(self):
        data = bundle(); data["/~unknown"] = True
        results = self.check(data, "SCHEMA_INVALID")
        self.assertEqual([asdict(item) for item in results], [
            {"code": "SCHEMA_INVALID", "path": "/bundle/~1~0unknown", "detail": "unknown field"}])
        data = bundle(); data["routes"][0]["selected_model"] = "unknown"
        results = self.check(data, "MODEL_UNAVAILABLE")
        self.assertEqual([asdict(item) for item in results], [{
            "code": "MODEL_UNAVAILABLE", "path": "/bundle/routes/0/selected_model",
            "detail": "model not in registry/runtime surface intersection"}])

    def test_pure_checker_never_follows_evidence_references(self):
        data = bundle(); data["runtime"]["source_ref"] = "https://invalid.example/do-not-fetch"
        with patch.object(Path, "read_bytes", side_effect=AssertionError("unexpected file read")), \
                patch.object(subprocess, "run", side_effect=AssertionError("unexpected subprocess")):
            self.check(data)

    def test_cli_reads_exactly_explicit_files_and_emits_complete_lf_bytes(self):
        data = bundle(); data["runtime"]["source_ref"] = "do-not-follow.json"
        data["/~unknown"] = True
        inputs = {"policy.json": json.dumps(registry()).encode(), "bundle.json": json.dumps(data).encode()}
        reads = []
        def read(file):
            reads.append(str(file))
            return inputs[str(file)]
        stdout = io.BytesIO()
        with patch.object(Path, "read_bytes", read), patch.object(checker.sys, "stdout", SimpleNamespace(buffer=stdout)):
            result = checker.main(["--registry", "policy.json", "--bundle", "bundle.json"])
        self.assertEqual(reads, ["policy.json", "bundle.json"])
        self.assertEqual(result, 1)
        self.assertEqual(stdout.getvalue(), b'{"code":"SCHEMA_INVALID","detail":"unknown field","path":"/bundle/~1~0unknown"}\n')

    def test_native_cli_strict_json_large_integer_and_input_immutability(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy_file, bundle_file = root / "registry.json", root / "bundle.json"
            policy_file.write_text(json.dumps(registry()), encoding="utf-8")
            sentinel = root / "unrelated.txt"; sentinel.write_bytes(b"must remain untouched")
            command = [sys.executable, "-B", str(TOOLS / "validate_runtime_routes.py"),
                "--registry", str(policy_file), "--bundle", str(bundle_file)]
            def inventory():
                return {file.name: hashlib.sha256(file.read_bytes()).hexdigest() for file in root.iterdir()}
            bad_json = [b'[]', b'null', b'{"x":Infinity}', b'{"x":-Infinity}', b'{"x":1e9999}',
                b'{"x":{"a":1,"a":2}}', b'{"x":' + b'[' * 2000 + b'0' + b']' * 2000 + b'}']
            for raw in bad_json:
                bundle_file.write_bytes(raw); before = inventory()
                for _ in range(2):
                    result = subprocess.run(command, capture_output=True, check=False)
                    self.assertEqual((result.returncode, result.stderr), (1, b""))
                    self.assertEqual(result.stdout, b'{"code":"JSON_INVALID","detail":"expected strict UTF-8 JSON object","path":"/bundle"}\n')
                self.assertEqual(inventory(), before)
            huge = "9" * 5000
            raw = json.dumps(bundle()).replace('"task_revision": 1', '"task_revision": ' + huge)
            bundle_file.write_bytes(raw.encode()); before = inventory()
            result = subprocess.run(command, capture_output=True, check=False)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
            self.assertEqual(inventory(), before)
            raw = json.dumps(bundle()).replace('"schema_version": 1', '"schema_version": ' + huge)
            bundle_file.write_bytes(raw.encode())
            result = subprocess.run(command, capture_output=True, check=False)
            self.assertEqual((result.returncode, result.stderr), (1, b""))
            self.assertEqual(result.stdout, b'{"code":"VERSION_UNSUPPORTED","detail":"expected schema version 1","path":"/bundle/schema_version"}\n')

    def test_native_cli_literal_multiple_findings_and_unicode_bytes(self):
        data = bundle()
        data["routes"][0].update(requested_capability="fast_reader", selected_model="unknown", context_complete=False)
        expected = (
            b'{"code":"CAPABILITY_FLOOR","detail":"requested capability below minimum","path":"/bundle/routes/0/requested_capability"}\n'
            b'{"code":"CONTEXT_INCOMPLETE","detail":"overridden no/bounded-history worker needs complete context","path":"/bundle/routes/0/context_complete"}\n'
            b'{"code":"MODEL_UNAVAILABLE","detail":"model not in registry/runtime surface intersection","path":"/bundle/routes/0/selected_model"}\n'
        )
        unicode_data = bundle(); unicode_data["/\u00e9~"] = 1
        unicode_expected = b'{"code":"SCHEMA_INVALID","detail":"unknown field","path":"/bundle/~1\\u00e9~0"}\n'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); policy_file = root / "registry.json"; bundle_file = root / "bundle.json"
            policy_file.write_text(json.dumps(registry()), encoding="utf-8")
            command = [sys.executable, "-B", str(TOOLS / "validate_runtime_routes.py"),
                "--registry", str(policy_file), "--bundle", str(bundle_file)]
            for value, literal in ((data, expected), (unicode_data, unicode_expected)):
                bundle_file.write_text(json.dumps(value), encoding="utf-8")
                before = (policy_file.read_bytes(), bundle_file.read_bytes())
                for _ in range(2):
                    result = subprocess.run(command, capture_output=True, check=False)
                    self.assertEqual((result.returncode, result.stdout, result.stderr), (1, literal, b""))
                self.assertEqual((policy_file.read_bytes(), bundle_file.read_bytes()), before)


if __name__ == "__main__":
    unittest.main()
