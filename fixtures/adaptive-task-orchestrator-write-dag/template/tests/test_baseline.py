from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from consumers.client.user_adapter import serialize_user
from consumers.server.user_adapter import normalize_user
from generated.user_fields import (
    CANONICAL_NAME_FIELD,
    FIELDS,
    LEGACY_NAME_FIELDS,
    REQUIRED_FIELDS,
)


class BaselineContractTests(unittest.TestCase):
    def test_generated_metadata_matches_the_legacy_contract(self) -> None:
        contract = json.loads(
            (PROJECT_ROOT / "contract" / "openapi.json").read_text(encoding="utf-8")
        )
        user_schema = contract["components"]["schemas"]["User"]

        self.assertEqual(FIELDS, tuple(user_schema["properties"]))
        self.assertEqual(REQUIRED_FIELDS, tuple(user_schema["required"]))
        self.assertEqual(CANONICAL_NAME_FIELD, "name")
        self.assertEqual(LEGACY_NAME_FIELDS, ())

    def test_server_normalizes_a_legacy_payload(self) -> None:
        self.assertEqual(
            normalize_user({"id": "user-1", "name": "Ada"}),
            {"id": "user-1", "name": "Ada"},
        )

    def test_client_serializes_a_legacy_user(self) -> None:
        self.assertEqual(
            serialize_user({"id": "user-1", "name": "Ada"}),
            {"id": "user-1", "name": "Ada"},
        )


if __name__ == "__main__":
    unittest.main()
