from __future__ import annotations

import hashlib
import importlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, asdict
from pathlib import Path
from unittest import mock


FIXTURE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = FIXTURE_ROOT.parents[1]
TOOLS_ROOT = FIXTURE_ROOT / "tools"
MANIFEST_NAME = "integrity.sha256"
TITLE = "# Portable integrity test package"
HEADER_LINES = (
    TITLE,
    "# Algorithm: SHA-256",
    "# Paths are relative to this directory.",
    "# Ordering: case-sensitive ordinal relative path.",
    "# integrity.sha256 is intentionally self-excluded.",
)

# Independent expected messages, never obtained from the implementation under test.
DETAILS = {
    "CONTEXT_ROOT_NOT_FOUND": "context root does not exist",
    "CONTEXT_ROOT_NOT_DIRECTORY": "context root is not a directory",
    "INVENTORY_READ_ERROR": "package inventory could not be read",
    "MANIFEST_NOT_FOUND": "manifest does not exist",
    "MANIFEST_NOT_REGULAR": "manifest is not a regular file",
    "MANIFEST_READ_ERROR": "manifest could not be read",
    "MANIFEST_INVALID_UTF8": "manifest is not valid UTF-8",
    "MANIFEST_FINAL_NEWLINE_MISSING": "manifest must end with LF",
    "MANIFEST_HEADER_INVALID": "manifest header does not match the canonical six-line header",
    "MANIFEST_ENTRY_INVALID": "manifest entry does not match the canonical entry grammar",
    "MANIFEST_PATH_UNSAFE": "manifest path is not a safe canonical package-relative path",
    "MANIFEST_SELF_INCLUDED": "manifest must exclude itself",
    "MANIFEST_DUPLICATE_PATH": "manifest path appears more than once",
    "MANIFEST_ORDER_INVALID": "manifest paths are not strictly increasing by ASCII bytes",
    "MANIFEST_FILE_MISSING": "listed file does not exist",
    "MANIFEST_FILE_NOT_REGULAR": "listed path is not a regular file",
    "MANIFEST_FILE_READ_ERROR": "listed file could not be read",
    "MANIFEST_UNLISTED_FILE": "regular package file is not listed in the manifest",
    "MANIFEST_UNSUPPORTED_OBJECT": "package contains a symlink or unsupported filesystem object",
}
ExpectedFinding = tuple[str, str] | tuple[str, str, str]


def expected_records(expected: list[ExpectedFinding]) -> list[dict[str, str]]:
    records = [
        {"code": item[0], "path": item[1], "detail": item[2] if len(item) == 3 else DETAILS[item[0]]}
        for item in expected
    ]
    return sorted(records, key=lambda item: (item["code"], item["path"], item["detail"]))


def canonical_output(records: list[dict[str, str]]) -> bytes:
    return b"".join(
        (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
        for record in records
    )

if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def manifest_bytes(
    entries: list[tuple[str, bytes]], *, count: int | None = None, raw_entries: list[str] | None = None
) -> bytes:
    declared_count = len(entries) if count is None else count
    lines = [*HEADER_LINES, f"# Entries: {declared_count}"]
    if raw_entries is None:
        lines.extend(f"{digest(contents)} *{path}" for path, contents in entries)
    else:
        lines.extend(raw_entries)
    return ("\n".join(lines) + "\n").encode("utf-8")


def snapshot(root: Path) -> dict[str, tuple[str, str]]:
    """Capture every temporary-package entry without following symlinks."""
    result: dict[str, tuple[str, str]] = {}
    if root.is_file() and not root.is_symlink():
        return {"": ("file", digest(root.read_bytes()))}
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in sorted([*directory_names, *file_names]):
            path = base / name
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                result[relative] = ("symlink", os.readlink(path))
            elif stat.S_ISREG(mode):
                result[relative] = ("file", digest(path.read_bytes()))
            elif stat.S_ISDIR(mode):
                result[relative] = ("directory", "")
            else:
                result[relative] = ("other", str(mode))
    return result


class VerifyIntegrityTests(unittest.TestCase):
    observations: list[dict[str, object]] | None = None

    def verifier(self):
        """Delay the import so every discovered RED test fails for the missing tool."""
        module = importlib.import_module("verify_integrity")
        return module.verify_integrity

    def make_package(
        self,
        root: Path,
        entries: list[tuple[str, bytes]],
        *,
        count: int | None = None,
        raw_manifest: bytes | None = None,
    ) -> None:
        for path, contents in entries:
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(contents)
        (root / MANIFEST_NAME).write_bytes(
            manifest_bytes(entries, count=count) if raw_manifest is None else raw_manifest
        )

    def finding_records(self, root: Path) -> list[dict[str, str]]:
        return [asdict(finding) for finding in self.verifier()(root)]

    def assert_findings(
        self, root: Path, expected: list[ExpectedFinding]
    ) -> None:
        self.assert_repeatable_and_read_only(root, expected)

    def assert_cli(self, root: Path, expected: list[ExpectedFinding]) -> list[dict[str, object]]:
        expected_bytes = canonical_output(expected_records(expected))
        runs = []
        for _ in range(2):
            completed = subprocess.run(
                [sys.executable, "-B", str(TOOLS_ROOT / "verify_integrity.py"), "--context-root", str(root)],
                check=False, capture_output=True,
            )
            self.assertEqual(completed.returncode, 1 if expected else 0, completed.stderr)
            self.assertEqual(completed.stderr, b"")
            self.assertEqual(completed.stdout, expected_bytes)
            runs.append({"exit_code": completed.returncode, "stdout_sha256": digest(completed.stdout), "stderr": ""})
        return runs

    def assert_record_runs(
        self, root: Path, first: list[dict[str, str]], second: list[dict[str, str]],
        expected: list[ExpectedFinding], before: dict[str, tuple[str, str]], *, cli: bool,
    ) -> None:
        expected_values = expected_records(expected)
        expected_bytes = canonical_output(expected_values)
        self.assertEqual(first, expected_values)
        self.assertEqual(second, first)
        self.assertEqual(canonical_output(first), expected_bytes)
        self.assertEqual(canonical_output(second), expected_bytes)
        cli_runs = self.assert_cli(root, expected) if cli else []
        after = snapshot(root)
        self.assertEqual(after, before)
        if self.observations is not None:
            self.observations.append({
                "case": self._subtest.id() if self._subtest is not None else self.id(),
                "expected": expected_values,
                "actual": first,
                "expected_jsonl_sha256": digest(expected_bytes),
                "actual_jsonl_sha256": [digest(canonical_output(first)), digest(canonical_output(second))],
                "input_inventory_sha256": digest(json.dumps(before, sort_keys=True, separators=(",", ":")).encode("ascii")),
                "output_inventory_sha256": digest(json.dumps(after, sort_keys=True, separators=(",", ":")).encode("ascii")),
                "function_runs": 2,
                "cli_runs": cli_runs,
                "cli_state": "PASS" if cli else "NOT_RUN_IN_PROCESS_IO_INJECTION",
            })

    def assert_repeatable_and_read_only(
        self, root: Path, expected: list[ExpectedFinding], *, cli: bool = True
    ) -> None:
        before = snapshot(root)
        first = self.finding_records(root)
        second = self.finding_records(root)
        self.assert_record_runs(root, first, second, expected, before, cli=cli)

    def test_minimal_valid_self_excluding_package_has_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.make_package(root, [("evidence/result.json", b'{"ok":true}\n')])

            self.assert_repeatable_and_read_only(root, [])

    def test_completed_v0_2_and_v0_3_packages_have_no_findings(self) -> None:
        for version, entry_count in (("v0.2", 100), ("v0.3", 65)):
            with self.subTest(version=version, entry_count=entry_count):
                root = PROJECT_ROOT / "docs/context" / f"adaptive-task-orchestrator-{version}"
                before = snapshot(root)
                first = self.finding_records(root)
                second = self.finding_records(root)

                self.assert_record_runs(root, first, second, [], before, cli=True)
                self.assertEqual(
                    int((root / MANIFEST_NAME).read_text(encoding="utf-8").splitlines()[5][11:]),
                    entry_count,
                )

    def test_digest_mismatch_missing_file_and_unlisted_file_are_exact_and_read_only(self) -> None:
        expected_digest = digest(b"original\n")
        actual_digest = digest(b"changed\n")
        cases = (
            ("digest", [("evidence/result.json", b"changed\n")], [("MANIFEST_DIGEST_MISMATCH", "evidence/result.json", f"expected {expected_digest}; actual {actual_digest}")]),
            ("missing", [], [("MANIFEST_FILE_MISSING", "evidence/result.json")]),
            ("unlisted", [("extra.txt", b"extra\n")], [("MANIFEST_UNLISTED_FILE", "extra.txt")]),
        )
        for name, actual_entries, expected in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                listed = [("evidence/result.json", b"original\n")]
                self.make_package(root, listed)
                if name == "digest":
                    (root / "evidence/result.json").write_bytes(actual_entries[0][1])
                elif name == "missing":
                    (root / "evidence/result.json").unlink()
                else:
                    (root / "extra.txt").write_bytes(actual_entries[0][1])

                self.assert_repeatable_and_read_only(root, expected)

    def test_duplicate_case_collision_order_and_count_mutations_have_complete_sets(self) -> None:
        cases = (
            (
                "duplicate",
                [("a.txt", b"a\n"), ("a.txt", b"a\n")],
                [("MANIFEST_DUPLICATE_PATH", "a.txt"), ("MANIFEST_ORDER_INVALID", "a.txt")],
            ),
            (
                "case_collision",
                [("A.txt", b"a\n"), ("a.txt", b"a\n")],
                [("MANIFEST_CASE_COLLISION", "a.txt", "case-collides with A.txt")],
            ),
            (
                "order",
                [("b.txt", b"b\n"), ("a.txt", b"a\n")],
                [("MANIFEST_ORDER_INVALID", "a.txt")],
            ),
            (
                "count",
                [("a.txt", b"a\n")],
                [("MANIFEST_ENTRY_COUNT_MISMATCH", MANIFEST_NAME, "declared 2; parsed 1")],
            ),
            (
                "self",
                [(MANIFEST_NAME, b"ignored\n")],
                [("MANIFEST_SELF_INCLUDED", MANIFEST_NAME)],
            ),
        )
        for name, entries, expected in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                count = 2 if name == "count" else None
                self.make_package(root, entries, count=count)
                if name == "self":
                    # The manifest entry is textual only; never overwrite the real manifest.
                    (root / MANIFEST_NAME).write_bytes(manifest_bytes(entries))

                self.assert_repeatable_and_read_only(root, expected)

    def test_unsafe_paths_are_rejected_before_any_out_of_root_target_read(self) -> None:
        unsafe_paths = (
            "",
            "/absolute.txt",
            "C:/drive.txt",
            "http:thing",
            "dir\\file.txt",
            "a//b.txt",
            "./file.txt",
            "../outside.txt",
            "a/../b.txt",
            "directory/file name.txt",
            "naïve.txt",
            "control\x01.txt",
        )
        for unsafe_path in unsafe_paths:
            with self.subTest(unsafe_path=unsafe_path), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory) / "package"
                root.mkdir()
                outside = Path(temporary_directory) / "outside.txt"
                outside.write_bytes(b"must not be read\n")
                raw = manifest_bytes(
                    [], count=1, raw_entries=[f"{digest(b'x')} *{unsafe_path}"]
                )
                self.make_package(root, [], raw_manifest=raw)
                original_open = Path.open
                resolved_root = root.resolve()

                def reject_any_out_of_package_open(path: Path, *args: object, **kwargs: object):
                    try:
                        path.resolve().relative_to(resolved_root)
                    except ValueError as error:
                        raise AssertionError(
                            f"unsafe manifest attempted an out-of-package open: {path}"
                        ) from error
                    return original_open(path, *args, **kwargs)

                with mock.patch.object(
                    Path, "open", autospec=True, side_effect=reject_any_out_of_package_open
                ):
                    self.assert_repeatable_and_read_only(
                        root, [("MANIFEST_PATH_UNSAFE", unsafe_path)]
                    )

    def test_invalid_headers_and_manifest_encodings_fail_closed(self) -> None:
        valid = manifest_bytes([])
        invalid_manifests = {
            "empty_title": valid.replace(TITLE.encode(), b"# ", 1),
            "title_start": valid.replace(TITLE.encode(), b"# -invalid", 1),
            "title_invalid_character": valid.replace(TITLE.encode(), b"# invalid!", 1),
            "title_too_long": valid.replace(TITLE.encode(), b"# " + b"A" * 129, 1),
            "algorithm": valid.replace(b"# Algorithm: SHA-256", b"# Algorithm: SHA256", 1),
            "trailing_space": valid.replace(b"# Paths are relative to this directory.", b"# Paths are relative to this directory. ", 1),
            "missing_header": valid.replace(b"# Ordering: case-sensitive ordinal relative path.\n", b"", 1),
            "reordered_headers": valid.replace(
                b"# Algorithm: SHA-256\n# Paths are relative to this directory.\n",
                b"# Paths are relative to this directory.\n# Algorithm: SHA-256\n",
                1,
            ),
            "extra_header": valid.replace(b"# Entries: 0\n", b"# Entries: 0\n# Extra: forbidden\n", 1),
            "blank_line": valid.replace(b"# Entries: 0\n", b"# Entries: 0\n\n", 1),
            "crlf": valid.replace(b"\n", b"\r\n"),
            "bom": b"\xef\xbb\xbf" + valid,
        }
        for name, raw in invalid_manifests.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                self.make_package(root, [], raw_manifest=raw)
                detail = (
                    "manifest contains a blank line or extra comment"
                    if name in {"extra_header", "blank_line"}
                    else DETAILS["MANIFEST_HEADER_INVALID"]
                )
                self.assert_repeatable_and_read_only(root, [("MANIFEST_HEADER_INVALID", MANIFEST_NAME, detail)])

        for invalid_count in ("+1", "-1", "01"):
            with self.subTest(invalid_count=invalid_count), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                raw = valid.replace(b"# Entries: 0", f"# Entries: {invalid_count}".encode(), 1)
                self.make_package(root, [], raw_manifest=raw)
                self.assert_repeatable_and_read_only(
                    root, [("MANIFEST_HEADER_INVALID", MANIFEST_NAME)]
                )

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.make_package(root, [], raw_manifest=b"\xff\xfe")
            self.assert_repeatable_and_read_only(root, [("MANIFEST_INVALID_UTF8", MANIFEST_NAME)])

    def test_invalid_entries_and_missing_final_newline_have_exact_findings(self) -> None:
        invalid_entries = (
            f"{digest(b'x').lower()} *file.txt",
            f"{'G' * 64} *file.txt",
            f"{digest(b'x')} file.txt",
            f"{digest(b'x')} *file.txt ",
            f"{digest(b'x')} *file.txt # comment",
            "",
        )
        for entry in invalid_entries:
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                self.make_package(root, [], raw_manifest=manifest_bytes([], count=1, raw_entries=[entry]))
                expected = (
                    [("MANIFEST_HEADER_INVALID", MANIFEST_NAME, "manifest contains a blank line or extra comment")]
                    if entry == "" else [("MANIFEST_ENTRY_INVALID", MANIFEST_NAME)]
                )
                self.assert_repeatable_and_read_only(root, expected)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.make_package(root, [], raw_manifest=manifest_bytes([]).rstrip(b"\n"))
            self.assert_repeatable_and_read_only(root, [("MANIFEST_FINAL_NEWLINE_MISSING", MANIFEST_NAME)])

    def test_returned_findings_are_immutable_and_ordered(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.make_package(root, [("a.txt", b"a\n"), ("a.txt", b"a\n")])

            findings = self.verifier()(root)
            self.assert_findings(root, [("MANIFEST_DUPLICATE_PATH", "a.txt"), ("MANIFEST_ORDER_INVALID", "a.txt")])
            self.assertEqual(
                [(finding.code, finding.path) for finding in findings],
                [
                    ("MANIFEST_DUPLICATE_PATH", "a.txt"),
                    ("MANIFEST_ORDER_INVALID", "a.txt"),
                ],
            )
            self.assertEqual(
                [(finding.code, finding.path, finding.detail) for finding in findings],
                sorted((finding.code, finding.path, finding.detail) for finding in findings),
            )
            with self.assertRaises((AttributeError, FrozenInstanceError, TypeError)):
                findings[0].code = "MUTATED"

    def test_missing_and_nonregular_context_roots_and_manifests_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            self.assert_findings(
                temporary_root / "missing", [("CONTEXT_ROOT_NOT_FOUND", "")]
            )
            root_file = temporary_root / "root-file"
            root_file.write_bytes(b"file\n")
            self.assert_findings(root_file, [("CONTEXT_ROOT_NOT_DIRECTORY", "")])
            root = temporary_root / "package"
            root.mkdir()
            self.assert_repeatable_and_read_only(root, [("MANIFEST_NOT_FOUND", MANIFEST_NAME)])
            (root / MANIFEST_NAME).mkdir()
            self.assert_repeatable_and_read_only(root, [("MANIFEST_NOT_REGULAR", MANIFEST_NAME)])

    def test_manifest_and_listed_file_read_errors_are_stable_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            # Keep the input aliased, but match the canonical paths used for I/O.
            (Path(temporary_directory) / "alias").mkdir()
            root = Path(temporary_directory) / "alias" / ".."
            self.make_package(root, [])
            manifest = (root / MANIFEST_NAME).resolve()
            original_open = Path.open

            def fail_manifest_read(path: Path, *args: object, **kwargs: object):
                if path == manifest:
                    raise OSError("injected manifest read failure")
                return original_open(path, *args, **kwargs)

            before = snapshot(root)
            with mock.patch.object(Path, "open", autospec=True, side_effect=fail_manifest_read):
                first = self.finding_records(root)
                second = self.finding_records(root)
            self.assert_record_runs(root, first, second, [("MANIFEST_READ_ERROR", MANIFEST_NAME)], before, cli=False)

        with tempfile.TemporaryDirectory() as temporary_directory:
            (Path(temporary_directory) / "alias").mkdir()
            root = Path(temporary_directory) / "alias" / ".."
            self.make_package(root, [("file.txt", b"file\n")])
            listed = (root / "file.txt").resolve()
            original_open = Path.open

            def fail_listed_read(path: Path, *args: object, **kwargs: object):
                if path == listed:
                    raise OSError("injected listed-file read failure")
                return original_open(path, *args, **kwargs)

            before = snapshot(root)
            with mock.patch.object(Path, "open", autospec=True, side_effect=fail_listed_read):
                first = self.finding_records(root)
                second = self.finding_records(root)
            self.assert_record_runs(root, first, second, [("MANIFEST_FILE_READ_ERROR", "file.txt")], before, cli=False)

    def test_inventory_error_and_read_boundary_replacement_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            (Path(temporary_directory) / "alias").mkdir()
            root = Path(temporary_directory) / "alias" / ".."
            self.make_package(root, [])
            canonical_root = root.resolve()
            original_iterdir = Path.iterdir

            def fail_inventory(path: Path):
                if path == canonical_root:
                    raise OSError("injected inventory failure")
                return original_iterdir(path)

            with mock.patch.object(Path, "iterdir", autospec=True, side_effect=fail_inventory):
                self.assert_repeatable_and_read_only(root, [("INVENTORY_READ_ERROR", "")], cli=False)

        with tempfile.TemporaryDirectory() as temporary_directory:
            (Path(temporary_directory) / "alias").mkdir()
            root = Path(temporary_directory) / "alias" / ".."
            self.make_package(root, [("file.txt", b"file\n")])
            listed = (root / "file.txt").resolve()
            original_open = Path.open

            def replaced_at_read_boundary(path: Path, *args: object, **kwargs: object):
                if path == listed:
                    raise FileNotFoundError("injected replacement at the read boundary")
                return original_open(path, *args, **kwargs)

            before = snapshot(root)
            with mock.patch.object(Path, "open", autospec=True, side_effect=replaced_at_read_boundary):
                first = self.finding_records(root)
                second = self.finding_records(root)
            self.assert_record_runs(root, first, second, [("MANIFEST_FILE_READ_ERROR", "file.txt")], before, cli=False)

    def test_listed_directory_is_not_a_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.make_package(root, [])
            (root / "directory").mkdir()
            raw = manifest_bytes([], count=1, raw_entries=[f"{digest(b'x')} *directory"])
            (root / MANIFEST_NAME).write_bytes(raw)

            self.assert_repeatable_and_read_only(root, [("MANIFEST_FILE_NOT_REGULAR", "directory")])

    def test_manifest_symlink_is_rejected_without_following_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "package"
            root.mkdir()
            target = Path(temporary_directory) / "manifest-target"
            target.write_bytes(manifest_bytes([]))
            try:
                os.symlink(target, root / MANIFEST_NAME)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: errno={error.errno}, winerror={getattr(error, 'winerror', None)}")

            self.assert_repeatable_and_read_only(
                root,
                [
                    ("MANIFEST_NOT_REGULAR", MANIFEST_NAME),
                    ("MANIFEST_UNSUPPORTED_OBJECT", MANIFEST_NAME),
                ],
            )

    def test_listed_symlink_is_rejected_without_following_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "package"
            root.mkdir()
            target = Path(temporary_directory) / "target.txt"
            target.write_bytes(b"target\n")
            link = root / "listed-link.txt"
            try:
                os.symlink(target, link)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: errno={error.errno}, winerror={getattr(error, 'winerror', None)}")
            target_digest = digest(b"target\n")
            raw = manifest_bytes([], count=1, raw_entries=[f"{target_digest} *listed-link.txt"])
            self.make_package(root, [], raw_manifest=raw)

            self.assert_repeatable_and_read_only(
                root,
                [
                    ("MANIFEST_FILE_NOT_REGULAR", "listed-link.txt"),
                    ("MANIFEST_UNSUPPORTED_OBJECT", "listed-link.txt"),
                ],
            )

    def test_directory_symlink_is_rejected_without_following_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "package"
            root.mkdir()
            target_directory = Path(temporary_directory) / "target-directory"
            target_directory.mkdir()
            try:
                os.symlink(target_directory, root / "linked-directory", target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlink creation unavailable: errno={error.errno}, winerror={getattr(error, 'winerror', None)}")
            self.make_package(root, [])

            self.assert_repeatable_and_read_only(
                root, [("MANIFEST_UNSUPPORTED_OBJECT", "linked-directory")]
            )

    def test_cli_emits_canonical_json_lines_and_exit_statuses(self) -> None:
        # Import first: while this tool is absent, RED is unambiguously an implementation failure.
        self.verifier()
        usage = subprocess.run(
            [sys.executable, "-B", str(TOOLS_ROOT / "verify_integrity.py")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(usage.returncode, 2, usage.stdout + usage.stderr)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.make_package(root, [])
            completed = subprocess.run(
                [sys.executable, "-B", str(TOOLS_ROOT / "verify_integrity.py"), "--context-root", str(root)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(completed.stdout, "")

            (root / "extra.txt").write_bytes(b"extra\n")
            completed = subprocess.run(
                [sys.executable, "-B", str(TOOLS_ROOT / "verify_integrity.py"), "--context-root", str(root)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            emitted = [json.loads(line) for line in completed.stdout.splitlines()]
            self.assertEqual(emitted, expected_records([("MANIFEST_UNLISTED_FILE", "extra.txt")]))
            self.assertEqual(set(emitted[0]), {"code", "path", "detail"})
            repeated = subprocess.run(
                [sys.executable, "-B", str(TOOLS_ROOT / "verify_integrity.py"), "--context-root", str(root)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(repeated.returncode, 1, repeated.stdout + repeated.stderr)
            self.assertEqual(repeated.stdout, completed.stdout)

    def test_zero_count_with_valid_entry_reports_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.make_package(root, [("a.txt", b"a\n")], count=0)
            self.assert_repeatable_and_read_only(root, [
                ("MANIFEST_ENTRY_COUNT_MISMATCH", MANIFEST_NAME, "declared 0; parsed 1")
            ])

    def test_zero_count_with_invalid_entry_reports_entry_grammar(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.make_package(root, [], raw_manifest=manifest_bytes([], raw_entries=["invalid"]))
            self.assert_repeatable_and_read_only(root, [("MANIFEST_ENTRY_INVALID", MANIFEST_NAME)])

    def test_unbounded_decimal_count_has_exact_cross_runtime_output(self) -> None:
        count = "9" * 5000
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            raw = manifest_bytes([]).replace(b"# Entries: 0", ("# Entries: " + count).encode("ascii"))
            self.make_package(root, [], raw_manifest=raw)
            self.assert_repeatable_and_read_only(root, [
                ("MANIFEST_ENTRY_COUNT_MISMATCH", MANIFEST_NAME, f"declared {count}; parsed 0")
            ])


if __name__ == "__main__":
    unittest.main()
