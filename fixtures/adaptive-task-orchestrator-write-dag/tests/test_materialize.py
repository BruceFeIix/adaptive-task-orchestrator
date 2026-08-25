from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


FIXTURE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FIXTURE_ROOT / "tools"))

from materialize import DIRTY_MARKER, materialize_run, validate_run_id


class ValidateRunIdTests(unittest.TestCase):
    def test_accepts_a_bounded_portable_identifier(self) -> None:
        self.assertEqual(validate_run_id("20260824-v0.2.0"), "20260824-v0.2.0")

    def test_rejects_paths_and_parent_segments(self) -> None:
        for value in ("", ".", "..", "../escape", "nested/run", "nested\\run"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_run_id(value)


class MaterializeRunTests(unittest.TestCase):
    def test_project_template_materializes_and_passes_its_baseline_suite(self) -> None:
        required_paths = (
            "contract/openapi.json",
            "generated/user_fields.py",
            "consumers/server/user_adapter.py",
            "consumers/client/user_adapter.py",
            "tests/test_baseline.py",
            "user-notes.md",
        )
        template_root = FIXTURE_ROOT / "template"
        for relative_path in required_paths:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((template_root / relative_path).is_file())

        with tempfile.TemporaryDirectory() as temporary_directory:
            runs_root = Path(temporary_directory) / "runs"
            receipt = materialize_run(template_root, runs_root, "template-test")
            completed = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                cwd=receipt.run_root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_creates_a_git_baseline_then_exactly_one_dirty_user_edit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            template_root = temporary_root / "template"
            runs_root = temporary_root / "runs"
            template_root.mkdir()
            (template_root / "user-notes.md").write_text(
                "# User notes\n\nKeep this baseline.\n", encoding="utf-8"
            )
            (template_root / "contract.json").write_text("{}\n", encoding="utf-8")

            receipt = materialize_run(template_root, runs_root, "test-run")

            run_root = runs_root / "test-run"
            status = subprocess.run(
                ["git", "-C", str(run_root), "status", "--short"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
            dirty_bytes = (run_root / "user-notes.md").read_bytes()
            record = json.loads((runs_root / "test-run.baseline.json").read_text(encoding="utf-8"))

            self.assertEqual(status, [" M user-notes.md"])
            self.assertTrue(dirty_bytes.endswith(DIRTY_MARKER.encode("utf-8")))
            self.assertEqual(receipt.dirty_sha256, hashlib.sha256(dirty_bytes).hexdigest().upper())
            self.assertEqual(record["dirty_sha256"], receipt.dirty_sha256)
            self.assertEqual(record["git_status"], [" M user-notes.md"])
            self.assertEqual(len(record["baseline_commit"]), 40)

    def test_git_failure_cleans_owned_artifacts_and_allows_same_id_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            template_root = temporary_root / "template"
            runs_root = temporary_root / "runs"
            template_root.mkdir()
            (template_root / "user-notes.md").write_text("baseline\n", encoding="utf-8")

            with mock.patch(
                "materialize._run_git",
                side_effect=subprocess.CalledProcessError(1, ["git"]),
            ):
                with self.assertRaises(subprocess.CalledProcessError):
                    materialize_run(template_root, runs_root, "test-run")

            self.assertEqual(list(runs_root.iterdir()), [])

            receipt = materialize_run(template_root, runs_root, "test-run")

            self.assertEqual(receipt.run_id, "test-run")
            self.assertTrue((runs_root / "test-run").is_dir())
            self.assertTrue((runs_root / "test-run.baseline.json").is_file())
            self.assertEqual(
                sorted(path.name for path in runs_root.iterdir()),
                ["test-run", "test-run.baseline.json"],
            )

    def test_lock_token_write_or_flush_failure_cleans_and_allows_same_id_retry(self) -> None:
        class FailingLockFile:
            def __init__(self, wrapped_file, failing_method: str) -> None:
                self._wrapped_file = wrapped_file
                self._failing_method = failing_method

            def write(self, value: str) -> int:
                if self._failing_method == "write":
                    raise OSError("injected lock token write failure")
                return self._wrapped_file.write(value)

            def flush(self) -> None:
                if self._failing_method == "flush":
                    raise OSError("injected lock token flush failure")
                self._wrapped_file.flush()

            def close(self) -> None:
                self._wrapped_file.close()

        for failing_method in ("write", "flush"):
            with self.subTest(failing_method=failing_method):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    temporary_root = Path(temporary_directory)
                    template_root = temporary_root / "template"
                    runs_root = temporary_root / "runs"
                    template_root.mkdir()
                    (template_root / "user-notes.md").write_text(
                        "baseline\n", encoding="utf-8"
                    )
                    lock_path = runs_root / ".test-run.materialize.lock"
                    original_open = Path.open

                    def open_with_lock_failure(path: Path, *args: object, **kwargs: object):
                        opened_file = original_open(path, *args, **kwargs)
                        if path == lock_path and args and args[0] == "x":
                            return FailingLockFile(opened_file, failing_method)
                        return opened_file

                    with mock.patch.object(
                        Path,
                        "open",
                        autospec=True,
                        side_effect=open_with_lock_failure,
                    ):
                        with self.assertRaisesRegex(
                            OSError,
                            f"injected lock token {failing_method} failure",
                        ):
                            materialize_run(template_root, runs_root, "test-run")

                    self.assertEqual(list(runs_root.iterdir()), [])

                    receipt = materialize_run(template_root, runs_root, "test-run")

                    self.assertEqual(receipt.run_id, "test-run")
                    self.assertEqual(
                        sorted(path.name for path in runs_root.iterdir()),
                        ["test-run", "test-run.baseline.json"],
                    )

    def test_rejects_runs_root_at_or_below_template_before_copy(self) -> None:
        for topology in ("equal", "contained"):
            with self.subTest(topology=topology):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    template_root = Path(temporary_directory) / "template"
                    template_root.mkdir()
                    (template_root / "user-notes.md").write_text(
                        "baseline\n", encoding="utf-8"
                    )
                    runs_root = template_root if topology == "equal" else template_root / "runs"
                    lock_path = runs_root / ".test-run.materialize.lock"
                    record_path = runs_root / "test-run.baseline.json"
                    run_root = runs_root / "test-run"

                    try:
                        with mock.patch(
                            "materialize.shutil.copytree",
                            side_effect=AssertionError("recursive copy was attempted"),
                        ) as copytree:
                            with self.assertRaisesRegex(
                                ValueError,
                                "runs root must be outside template root",
                            ):
                                materialize_run(template_root, runs_root, "test-run")
                            copytree.assert_not_called()
                    finally:
                        self.assertFalse(lock_path.exists())
                        self.assertFalse(record_path.exists())
                        self.assertFalse(run_root.exists())
                        self.assertEqual(list(runs_root.glob(".test-run.staging-*")), [])
                        if topology == "contained":
                            self.assertFalse(runs_root.exists())

    def test_receipt_failure_after_promotion_rolls_back_and_allows_same_id_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            template_root = temporary_root / "template"
            runs_root = temporary_root / "runs"
            template_root.mkdir()
            (template_root / "user-notes.md").write_text("baseline\n", encoding="utf-8")
            record_path = runs_root / "test-run.baseline.json"
            original_open = Path.open
            promoted_state_at_failure = []

            def fail_receipt_publication(path: Path, *args: object, **kwargs: object):
                if path == record_path:
                    promoted_state_at_failure.append((runs_root / "test-run").is_dir())
                    raise OSError("injected receipt publication failure")
                return original_open(path, *args, **kwargs)

            with mock.patch.object(Path, "open", autospec=True, side_effect=fail_receipt_publication):
                with self.assertRaisesRegex(OSError, "injected receipt publication failure"):
                    materialize_run(template_root, runs_root, "test-run")

            self.assertEqual(promoted_state_at_failure, [True])
            self.assertEqual(list(runs_root.iterdir()), [])

            receipt = materialize_run(template_root, runs_root, "test-run")

            self.assertEqual(receipt.run_id, "test-run")
            self.assertEqual(
                sorted(path.name for path in runs_root.iterdir()),
                ["test-run", "test-run.baseline.json"],
            )

    def test_refuses_to_overwrite_an_existing_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            template_root = temporary_root / "template"
            runs_root = temporary_root / "runs"
            template_root.mkdir()
            (template_root / "user-notes.md").write_text("baseline\n", encoding="utf-8")

            materialize_run(template_root, runs_root, "test-run")

            with self.assertRaises(FileExistsError):
                materialize_run(template_root, runs_root, "test-run")


if __name__ == "__main__":
    unittest.main()
