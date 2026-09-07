from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import validate_runtime_routes as checker

CANDIDATES = REPOSITORY / "docs/context/adaptive-task-orchestrator-v0.5/candidates"


class RegistryCandidateTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((CANDIDATES / "model-registry.json").read_text(encoding="utf-8"))
        self.bundle = json.loads((CANDIDATES / "planned-astra-bundle.json").read_text(encoding="utf-8"))

    def codes(self, data):
        return [item.code for item in checker.validate_runtime_routes(self.registry, data)]

    def test_planned_example_does_not_prove_completed_high_risk_execution(self):
        self.assertEqual(self.codes(self.bundle), [])
        changed = copy.deepcopy(self.bundle)
        changed["routes"][0]["dispatch_status"] = "completed"
        self.assertEqual(self.codes(changed), ["EFFECTIVE_ROUTE_UNATTESTED"])
        self.assertIsNone(changed["routes"][0]["effective_route"])
        self.assertFalse(changed["runtime"]["effective_config_reporting"])

    def test_every_profile_default_meets_its_declared_capability(self):
        for profile, defaults in self.registry["defaults"].items():
            for capability, models in defaults.items():
                for model in models:
                    with self.subTest(profile=profile, capability=capability, model=model):
                        data = copy.deepcopy(self.bundle)
                        data["requirements"][0].update(minimum_capability=capability, assurance="deterministic")
                        data["routes"][0].update(profile=profile, requested_capability=capability,
                            selected_model=model, selected_effort="high")
                        self.assertEqual(self.codes(data), [])

    def test_astra_ultra_is_native_only_in_candidate_registry(self):
        data = copy.deepcopy(self.bundle)
        data["routes"][0]["selected_effort"] = "ultra"
        self.assertEqual(self.codes(data), [])
        data["runtime"]["surface"] = "openai.responses"
        self.assertEqual(self.codes(data), ["EFFORT_UNAVAILABLE"])
        data["routes"][0]["selected_effort"] = "max"
        self.assertEqual(self.codes(data), [])

    def test_extra_host_model_is_not_implicitly_an_eligible_candidate(self):
        self.assertIn("gpt-5.5", self.bundle["runtime"]["models"])
        data = copy.deepcopy(self.bundle)
        data["routes"][0]["selected_model"] = "gpt-5.5"
        self.assertEqual(self.codes(data), ["MODEL_UNAVAILABLE"])

    def test_pinned_example_disallows_even_an_upward_effort_fallback(self):
        data = copy.deepcopy(self.bundle)
        data["routes"][0]["fallback_chain"] = [{"model": "gpt-6-astra", "effort": "max"}]
        self.assertEqual(self.codes(data), ["PIN_VIOLATION"])


if __name__ == "__main__":
    unittest.main()
