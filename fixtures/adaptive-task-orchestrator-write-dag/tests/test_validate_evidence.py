from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


FIXTURE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = FIXTURE_ROOT.parents[1]
sys.path.insert(0, str(FIXTURE_ROOT / "tools"))

from validate_evidence import validate_context


def executable_contract(task_id: str = "T1", revision: int = 1) -> dict[str, object]:
    return {
        "id": task_id,
        "revision": revision,
        "objective": "Produce one bounded artifact.",
        "task_type": "implementation",
        "mode": "write",
        "dependencies": [],
        "inputs": [],
        "deliverable": "artifact.txt",
        "read_scope": [],
        "write_scope": ["artifact.txt"],
        "resource_locks": ["artifact:one"],
        "context_package": {
            "authoritative_facts": [],
            "relevant_artifacts": [],
            "accepted_upstream_results": [],
            "user_constraints": [],
            "permissions": ["Write artifact.txt."],
            "non_goals": [],
        },
        "classification": {
            "reasoning_depth": 1,
            "context_breadth": 1,
            "uncertainty": 0,
            "novelty": 0,
            "impact": 1,
            "verifiability": 3,
            "coupling": 1,
        },
        "acceptance_checks": ["artifact.txt exists"],
        "evidence_required": ["path and check output"],
        "assurance_requirement": "deterministic",
    }


def preflight_contract() -> dict[str, object]:
    contract = executable_contract("P1")
    contract["record_kind"] = "preflight_fixture_record"
    del contract["context_package"]
    del contract["classification"]
    return contract


def child_route(task_id: str = "T1", revision: int = 1) -> dict[str, object]:
    return {
        "task_id": task_id,
        "task_revision": revision,
        "profile": "balanced",
        "preferred_capability": "general_worker",
        "requested_capability": "general_worker",
        "route_reason_codes": [],
        "effective_floor": "general_worker",
        "floor_reasons": [],
        "selected_model": "test-model",
        "selected_effort": "medium",
        "fork_turns": "none",
        "fallback_chain": [],
        "selection_reason": "preferred",
        "route_status": "observed",
        "capability_attested": True,
        "attestation_source": "runtime-result",
        "floor_satisfied": True,
    }


def root_record(task_id: str = "T1", revision: int = 1) -> dict[str, object]:
    return {
        "record_kind": "root_execution_record",
        "task_id": task_id,
        "task_revision": revision,
        "execution_target": "current_root",
        "execution_status": "observed",
        "exact_root_model_attested": False,
        "route_status": "inherited-unattested",
        "reason": "Executed by the current root.",
    }


def legacy_root_record(task_id: str = "T1", revision: int = 1) -> dict[str, object]:
    return {
        "record_kind": "root_execution_record_with_legacy_route_fields",
        "semantic_note": "Preserved historical root route fields.",
        "task_id": task_id,
        "task_revision": revision,
        "preferred_capability": "root_controller",
        "requested_capability": "root_controller",
        "route_reason_codes": ["root-final-authority"],
        "effective_floor": "root_controller",
        "floor_reasons": ["Root owns integration."],
        "selected_model": "root-current-model",
        "selected_effort": "current",
        "fork_turns": "inherited",
        "fallback_chain": [],
        "selection_reason": "root-authority",
        "route_status": "inherited-unattested",
        "capability_attested": False,
        "attestation_source": "none",
        "floor_satisfied": True,
        "execution_status": "observed",
        "worker": "/root",
    }


def preflight_route(task_id: str = "P1", revision: int = 1) -> dict[str, object]:
    return {
        "task_id": task_id,
        "task_revision": revision,
        "requested_capability": "general_worker",
        "route_status": "requested",
        "capability_attested": False,
        "attestation_source": None,
        "floor_satisfied": None,
        "dispatch_result": "not_dispatched_writer_conflict",
        "conflicts_with": "P2@1",
    }


def receipt(task_id: str = "T1", revision: int = 1) -> dict[str, object]:
    return {
        "status": "DONE",
        "task_id": task_id,
        "task_revision": revision,
        "summary": "Completed.",
        "claims": [
            {
                "claim": "The bounded artifact exists.",
                "confidence": "high",
                "evidence": ["artifact exists check passed"],
            }
        ],
        "uncertainty": [],
        "artifacts_or_changes": ["artifact.txt"],
        "resources_accessed": [],
        "external_calls": [],
        "checks": [{"check": "artifact exists", "result": "pass"}],
        "contradictions": [],
        "recommended_next": "accept",
    }


class ContextBuilder:
    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "contracts" / "revisions").mkdir(parents=True)
        (root / "routes").mkdir()
        (root / "receipts").mkdir()

    def write_json(self, relative_path: str, value: object) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def add_contract(self, value: dict[str, object], *, exact_copy: bool = True) -> None:
        task_id = value["id"]
        revision = value["revision"]
        self.write_json(f"contracts/{task_id}.json", value)
        if exact_copy:
            current_bytes = (self.root / f"contracts/{task_id}.json").read_bytes()
            (self.root / f"contracts/revisions/{task_id}-r{revision}.contract.json").write_bytes(
                current_bytes
            )


class EvidenceValidatorTests(unittest.TestCase):
    def finding_codes(self, root: Path) -> list[str]:
        return [finding.code for finding in validate_context(root)]

    def finding_details(self, root: Path, code: str) -> list[str]:
        return [finding.detail for finding in validate_context(root) if finding.code == code]

    def test_accepts_each_explicit_record_variant(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            builder.add_contract(executable_contract())
            builder.add_contract(preflight_contract())
            builder.write_json("routes/T1.route.json", child_route())
            builder.write_json("routes/T1-root.route.json", root_record())
            builder.write_json("routes/T1-legacy-root.route.json", legacy_root_record())
            builder.write_json("routes/P1-preflight.route.json", preflight_route())
            builder.write_json("receipts/T1-r1.json", receipt())

            self.assertEqual(validate_context(builder.root), [])

    def test_missing_contract_field_has_stable_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            malformed = executable_contract()
            del malformed["classification"]
            builder.add_contract(malformed)

            self.assertIn("CONTRACT_MISSING_FIELD", self.finding_codes(builder.root))

    def test_invalid_contract_enum_has_stable_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            malformed = executable_contract()
            malformed["task_type"] = "investigation"
            builder.add_contract(malformed)

            self.assertIn("CONTRACT_INVALID_ENUM", self.finding_codes(builder.root))

    def test_current_contract_requires_every_nested_context_package_field(self) -> None:
        context_fields = (
            "authoritative_facts",
            "relevant_artifacts",
            "accepted_upstream_results",
            "user_constraints",
            "permissions",
            "non_goals",
        )
        for field in context_fields:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary_directory:
                builder = ContextBuilder(Path(temporary_directory))
                malformed = executable_contract()
                del malformed["context_package"][field]  # type: ignore[index]
                builder.add_contract(malformed)

                self.assertIn(
                    f"context_package.{field}",
                    self.finding_details(builder.root, "CONTRACT_MISSING_FIELD"),
                )

    def test_context_package_fields_must_be_string_lists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            malformed = executable_contract()
            malformed["context_package"]["permissions"] = [7]  # type: ignore[index]
            builder.add_contract(malformed)

            self.assertIn(
                "context_package.permissions",
                self.finding_details(builder.root, "CONTRACT_INVALID_TYPE"),
            )

    def test_unresolved_dependency_has_stable_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            malformed = executable_contract()
            malformed["dependencies"] = ["missing@7"]
            builder.add_contract(malformed)

            self.assertIn("DEPENDENCY_UNRESOLVED", self.finding_codes(builder.root))

    def test_current_contract_must_be_byte_identical_to_immutable_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            builder.add_contract(executable_contract())
            revision_path = builder.root / "contracts/revisions/T1-r1.contract.json"
            immutable = json.loads(revision_path.read_text(encoding="utf-8"))
            immutable["objective"] = "Different immutable body."
            builder.write_json("contracts/revisions/T1-r1.contract.json", immutable)

            self.assertIn("CURRENT_REVISION_MISMATCH", self.finding_codes(builder.root))

    def test_observed_child_route_cannot_be_unattested(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            builder.add_contract(executable_contract())
            malformed = child_route()
            malformed["capability_attested"] = False
            malformed["attestation_source"] = "none"
            builder.write_json("routes/T1.route.json", malformed)

            self.assertIn("ROUTE_ILLEGAL_STATE", self.finding_codes(builder.root))

    def test_normal_child_route_requires_the_complete_route_decision_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            builder.add_contract(executable_contract())
            malformed = child_route()
            del malformed["profile"]
            del malformed["selected_model"]
            builder.write_json("routes/T1.route.json", malformed)

            details = self.finding_details(builder.root, "ROUTE_MISSING_FIELD")
            self.assertIn("profile", details)
            self.assertIn("selected_model", details)

    def test_child_route_validates_container_scalar_and_enum_types(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            builder.add_contract(executable_contract())
            malformed = child_route()
            malformed["profile"] = "reckless"
            malformed["preferred_capability"] = 7
            malformed["route_reason_codes"] = "not-a-list"
            malformed["fallback_chain"] = [7]
            malformed["selected_model"] = ""
            builder.write_json("routes/T1.route.json", malformed)

            codes = self.finding_codes(builder.root)
            self.assertIn("ROUTE_INVALID_ENUM", codes)
            self.assertIn("ROUTE_INVALID_TYPE", codes)

    def test_child_route_rejects_nonstandard_profile_values(self) -> None:
        for profile in ("thorough", "reckless"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as temporary_directory:
                builder = ContextBuilder(Path(temporary_directory))
                builder.add_contract(executable_contract())
                malformed = child_route()
                malformed["profile"] = profile
                builder.write_json("routes/T1.route.json", malformed)

                self.assertIn("ROUTE_INVALID_ENUM", self.finding_codes(builder.root))

    def test_root_execution_record_requires_complete_typed_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            builder.add_contract(executable_contract())
            malformed = root_record()
            del malformed["reason"]
            malformed["execution_target"] = 7
            malformed["exact_root_model_attested"] = "false"
            builder.write_json("routes/T1-root.route.json", malformed)

            codes = self.finding_codes(builder.root)
            self.assertIn("ROUTE_MISSING_FIELD", codes)
            self.assertIn("ROUTE_INVALID_TYPE", codes)

    def test_root_execution_record_rejects_invalid_state_types(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            builder.add_contract(executable_contract())
            malformed = root_record()
            malformed["execution_status"] = 7
            malformed["route_status"] = 7
            builder.write_json("routes/T1-root.route.json", malformed)

            codes = self.finding_codes(builder.root)
            self.assertIn("ROUTE_INVALID_TYPE", codes)
            self.assertIn("ROUTE_ILLEGAL_STATE", codes)

    def test_receipt_revision_must_resolve_to_declared_contract_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            builder.add_contract(executable_contract())
            builder.write_json("receipts/T1-r2.json", receipt(revision=2))

            self.assertIn("RECEIPT_REVISION_MISMATCH", self.finding_codes(builder.root))

    def test_receipt_summary_and_recommended_next_must_be_nonempty_strings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            builder.add_contract(executable_contract())
            malformed = receipt()
            malformed["summary"] = 7
            malformed["recommended_next"] = ""
            builder.write_json("receipts/T1-r1.json", malformed)

            details = self.finding_details(builder.root, "RECEIPT_INVALID_TYPE")
            self.assertIn("summary", details)
            self.assertIn("recommended_next", details)

    def test_receipt_claims_require_typed_claim_confidence_and_evidence(self) -> None:
        malformed_claims = (
            "not-an-object",
            {"claim": "Missing fields."},
            {"claim": 7, "confidence": "high", "evidence": ["evidence"]},
            {"claim": "Claim.", "confidence": "certain", "evidence": ["evidence"]},
            {"claim": "Claim.", "confidence": "high", "evidence": [7]},
        )
        for claim in malformed_claims:
            with self.subTest(claim=claim), tempfile.TemporaryDirectory() as temporary_directory:
                builder = ContextBuilder(Path(temporary_directory))
                builder.add_contract(executable_contract())
                malformed = receipt()
                malformed["claims"] = [claim]
                builder.write_json("receipts/T1-r1.json", malformed)

                codes = self.finding_codes(builder.root)
                self.assertTrue(
                    {"RECEIPT_MISSING_FIELD", "RECEIPT_INVALID_TYPE", "RECEIPT_INVALID_ENUM"}
                    .intersection(codes)
                )

    def test_receipt_checks_require_typed_check_and_known_result(self) -> None:
        malformed_checks = (
            "not-an-object",
            {"check": "Missing result."},
            {"check": 7, "result": "pass"},
            {"check": "Unknown result.", "result": "maybe"},
        )
        for check in malformed_checks:
            with self.subTest(check=check), tempfile.TemporaryDirectory() as temporary_directory:
                builder = ContextBuilder(Path(temporary_directory))
                builder.add_contract(executable_contract())
                malformed = receipt()
                malformed["checks"] = [check]
                builder.write_json("receipts/T1-r1.json", malformed)

                codes = self.finding_codes(builder.root)
                self.assertTrue(
                    {"RECEIPT_MISSING_FIELD", "RECEIPT_INVALID_TYPE", "RECEIPT_INVALID_ENUM"}
                    .intersection(codes)
                )

    def test_receipt_list_containers_validate_their_elements(self) -> None:
        malformed_fields = {
            "uncertainty": [7],
            "artifacts_or_changes": [7],
            "resources_accessed": [{}],
            "external_calls": [None],
            "contradictions": [["nested"]],
        }
        for field, value in malformed_fields.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary_directory:
                builder = ContextBuilder(Path(temporary_directory))
                builder.add_contract(executable_contract())
                malformed = receipt()
                malformed[field] = value
                builder.write_json("receipts/T1-r1.json", malformed)

                self.assertIn(field, self.finding_details(builder.root, "RECEIPT_INVALID_TYPE"))

    def test_receipt_status_and_identity_require_scalar_types(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            builder.add_contract(executable_contract())
            malformed = receipt()
            malformed["status"] = 7
            malformed["task_id"] = 7
            malformed["task_revision"] = True
            builder.write_json("receipts/T1-r1.json", malformed)

            self.assertIn("RECEIPT_INVALID_TYPE", self.finding_codes(builder.root))

    def test_done_receipt_rejects_a_nonpassing_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            builder.add_contract(executable_contract())
            malformed = receipt()
            malformed["checks"] = [{"check": "required oracle", "result": "fail"}]
            builder.write_json("receipts/T1-r1.json", malformed)

            self.assertIn("RECEIPT_STATUS_CHECK_CONFLICT", self.finding_codes(builder.root))

    def test_non_done_lifecycle_receipts_may_carry_failed_checks(self) -> None:
        for status in ("BLOCKED", "NEEDS_CONTEXT", "DONE_WITH_CONCERNS"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temporary_directory:
                builder = ContextBuilder(Path(temporary_directory))
                builder.add_contract(executable_contract())
                lifecycle_receipt = receipt()
                lifecycle_receipt["status"] = status
                lifecycle_receipt["checks"] = [{"check": "required oracle", "result": "fail"}]
                builder.write_json("receipts/T1-r1.json", lifecycle_receipt)

                self.assertNotIn(
                    "RECEIPT_STATUS_CHECK_CONFLICT", self.finding_codes(builder.root)
                )

    def test_unknown_contract_kind_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            unknown = executable_contract()
            unknown["record_kind"] = "future_contract_kind"
            builder.add_contract(unknown)

            self.assertIn("RECORD_UNKNOWN_KIND", self.finding_codes(builder.root))

    def test_cli_emits_json_findings_and_exits_one(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            builder = ContextBuilder(Path(temporary_directory))
            malformed = executable_contract()
            malformed["mode"] = "mutate"
            builder.add_contract(malformed)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(FIXTURE_ROOT / "tools" / "validate_evidence.py"),
                    "--context-root",
                    str(builder.root),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            findings = [json.loads(line) for line in completed.stdout.splitlines()]

            self.assertEqual(completed.returncode, 1)
            self.assertIn("CONTRACT_INVALID_ENUM", [finding["code"] for finding in findings])
            self.assertTrue(all(set(finding) == {"code", "detail", "path"} for finding in findings))

    def test_completed_v0_2_package_is_accepted_with_declared_historical_boundaries(self) -> None:
        context_root = PROJECT_ROOT / "docs/context/adaptive-task-orchestrator-v0.2"

        self.assertEqual(validate_context(context_root), [])

    def test_current_v0_3_package_accepts_the_exact_rejected_review_history(self) -> None:
        context_root = PROJECT_ROOT / "docs/context/adaptive-task-orchestrator-v0.3"

        self.assertEqual(validate_context(context_root), [])


if __name__ == "__main__":
    unittest.main()
