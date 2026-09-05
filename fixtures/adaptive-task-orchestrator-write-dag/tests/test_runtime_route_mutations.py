"""Controlled in-memory mutations prove selected test oracles reject regressions."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import test_runtime_routes as routes
import test_runtime_routes_hardening as hardening
import validate_runtime_routes as checker


class RuntimeRouteMutationTests(unittest.TestCase):
    def assert_oracle_rejects(self, method, replacement, case):
        result = unittest.TestResult()
        with patch.object(checker._RouteChecks, method, replacement):
            case.run(result)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(result.errors, [], "Mutation must fail assertions, not crash the test")
        self.assertGreater(len(result.failures), 0, "Oracle did not detect the controlled regression")

    def test_selected_floor_oracle_rejects_disabled_planned_checks(self):
        self.assert_oracle_rejects("planned", lambda *args: 0,
            hardening.RuntimeRouteHardeningTests("test_selected_capability_cartesian_floor_matrix"))

    def test_effective_oracle_rejects_disabled_attestation_checks(self):
        self.assert_oracle_rejects("effective", lambda *args: None,
            routes.RuntimeRouteTests("test_high_risk_dispatch_requires_effective_evidence"))

    def test_fallback_oracle_rejects_disabled_fallback_checks(self):
        self.assert_oracle_rejects("fallback", lambda *args: None,
            routes.RuntimeRouteTests("test_fallback_starts_at_selected_pair_and_never_downgrades"))

    def test_review_oracle_rejects_disabled_review_comparison(self):
        self.assert_oracle_rejects("review", lambda *args: None,
            hardening.RuntimeRouteHardeningTests("test_review_capability_uses_selected_or_both_effective_models"))

    def test_cycle_oracle_rejects_disabled_cycle_check(self):
        self.assert_oracle_rejects("review_cycles", lambda *args: None,
            hardening.RuntimeRouteHardeningTests("test_review_graph_long_chain_and_cycle_do_not_recurse"))

    def test_complete_diagnostic_oracle_rejects_correct_code_with_wrong_detail(self):
        original = checker._RouteChecks.add
        def corrupted(instance, code, path, detail):
            original(instance, code, path, detail + " corrupted")
        self.assert_oracle_rejects("add", corrupted,
            hardening.RuntimeRouteHardeningTests("test_literal_complete_diagnostics_and_escaped_json_pointer"))


if __name__ == "__main__":
    unittest.main()
