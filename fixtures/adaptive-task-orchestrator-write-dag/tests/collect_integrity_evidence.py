"""Run temporary-package tests and emit observations, without writing a report file.

This is an opt-in test runner, not a read-only production verifier: tests create
automatically cleaned temporary fixtures. JSON is stdout; unittest logs are stderr.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import unittest
from pathlib import Path

from test_verify_integrity import VerifyIntegrityTests


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(VerifyIntegrityTests)
    VerifyIntegrityTests.observations = []
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(suite)
    fixture = Path(__file__).resolve().parents[1]
    files = [
        fixture / "tools/verify_integrity.py",
        fixture / "tests/test_verify_integrity.py",
        Path(__file__).resolve(),
    ]
    report = {
        "record_kind": "integrity_test_observations",
        "schema_version": 1,
        "python": platform.python_version(),
        "platform": sys.platform,
        "sources": {path.relative_to(fixture).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest().upper() for path in files},
        "discovered": result.testsRun,
        "skipped": [{"test": test.id(), "reason": reason} for test, reason in result.skipped],
        "failure_records": len(result.failures),
        "error_records": len(result.errors),
        "passed": result.testsRun - len(result.skipped) if result.wasSuccessful() else None,
        "exit_code": 0 if result.wasSuccessful() else 1,
        "observations": VerifyIntegrityTests.observations,
        "scope": "Only recorded cases have complete two-run function and optional native-CLI observations; mock I/O is function-only. Skipped tests did not execute their assertions.",
    }
    sys.stdout.buffer.write((json.dumps(report, sort_keys=True, indent=2) + "\n").encode("ascii"))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
