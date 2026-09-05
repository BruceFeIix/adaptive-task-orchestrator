from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


MANIFEST_NAME = "integrity.sha256"
FIXED_HEADERS = (
    "# Algorithm: SHA-256",
    "# Paths are relative to this directory.",
    "# Ordering: case-sensitive ordinal relative path.",
    "# integrity.sha256 is intentionally self-excluded.",
)
TITLE_PATTERN = re.compile(r"# [A-Za-z0-9][A-Za-z0-9 ._-]{0,127}\Z")
COUNT_PATTERN = re.compile(r"# Entries: (0|[1-9][0-9]*)\Z")
ENTRY_PATTERN = re.compile(r"([0-9A-F]{64}) \*(.*)\Z")
PATH_PATTERN = re.compile(r"[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*\Z")


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    path: str
    detail: str


@dataclass(frozen=True)
class ManifestEntry:
    digest: str
    path: str


def _finding(code: str, path: str, detail: str) -> Finding:
    return Finding(code=code, path=path, detail=detail)


def _sorted_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(set(findings))


def _safe_manifest_path(value: str) -> bool:
    if PATH_PATTERN.fullmatch(value) is None:
        return False
    return all(segment not in {".", ".."} for segment in value.split("/"))


def _is_reparse_point(file_info: object) -> bool:
    attributes = getattr(file_info, "st_file_attributes", 0)
    marker = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(marker and attributes & marker)


def _parse_manifest(data: bytes) -> tuple[list[ManifestEntry] | None, list[Finding]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None, [
            _finding(
                "MANIFEST_INVALID_UTF8",
                MANIFEST_NAME,
                "manifest is not valid UTF-8",
            )
        ]

    if not text.endswith("\n"):
        return None, [
            _finding(
                "MANIFEST_FINAL_NEWLINE_MISSING",
                MANIFEST_NAME,
                "manifest must end with LF",
            )
        ]

    lines = text[:-1].split("\n")
    if (
        "\r" in text
        or len(lines) < 6
        or TITLE_PATTERN.fullmatch(lines[0]) is None
        or tuple(lines[1:5]) != FIXED_HEADERS
        or COUNT_PATTERN.fullmatch(lines[5]) is None
    ):
        return None, [
            _finding(
                "MANIFEST_HEADER_INVALID",
                MANIFEST_NAME,
                "manifest header does not match the canonical six-line header",
            )
        ]

    count_match = COUNT_PATTERN.fullmatch(lines[5])
    assert count_match is not None
    # The grammar is unbounded; int() has version-dependent digit limits.
    declared_count = count_match.group(1)
    raw_entries = lines[6:]
    if any(not line or line.startswith("#") for line in raw_entries):
        return None, [
            _finding(
                "MANIFEST_HEADER_INVALID",
                MANIFEST_NAME,
                "manifest contains a blank line or extra comment",
            )
        ]

    entries: list[ManifestEntry] = []
    findings: list[Finding] = []
    for line in raw_entries:
        match = ENTRY_PATTERN.fullmatch(line)
        if match is None or line.endswith(" ") or " # " in line:
            return None, [
                _finding(
                    "MANIFEST_ENTRY_INVALID",
                    MANIFEST_NAME,
                    "manifest entry does not match the canonical entry grammar",
                )
            ]
        digest, relative_path = match.groups()
        if not _safe_manifest_path(relative_path):
            findings.append(
                _finding(
                    "MANIFEST_PATH_UNSAFE",
                    relative_path,
                    "manifest path is not a safe canonical package-relative path",
                )
            )
        entries.append(ManifestEntry(digest=digest, path=relative_path))

    if str(len(entries)) != declared_count:
        findings.append(
            _finding(
                "MANIFEST_ENTRY_COUNT_MISMATCH",
                MANIFEST_NAME,
                f"declared {declared_count}; parsed {len(entries)}",
            )
        )

    previous_path: bytes | None = None
    seen_paths: set[str] = set()
    collision_paths: dict[str, str] = {}
    for entry in entries:
        path_bytes = entry.path.encode("ascii") if entry.path.isascii() else b""
        if entry.path in seen_paths:
            findings.append(
                _finding(
                    "MANIFEST_DUPLICATE_PATH",
                    entry.path,
                    "manifest path appears more than once",
                )
            )
        seen_paths.add(entry.path)

        collision_key = "".join(
            chr(ord(character) + 32) if "A" <= character <= "Z" else character
            for character in entry.path
        )
        prior_collision_path = collision_paths.get(collision_key)
        if prior_collision_path is not None and prior_collision_path != entry.path:
            findings.append(
                _finding(
                    "MANIFEST_CASE_COLLISION",
                    entry.path,
                    f"case-collides with {prior_collision_path}",
                )
            )
        else:
            collision_paths[collision_key] = entry.path

        if previous_path is not None and path_bytes <= previous_path:
            findings.append(
                _finding(
                    "MANIFEST_ORDER_INVALID",
                    entry.path,
                    "manifest paths are not strictly increasing by ASCII bytes",
                )
            )
        previous_path = path_bytes

        if entry.path == MANIFEST_NAME:
            findings.append(
                _finding(
                    "MANIFEST_SELF_INCLUDED",
                    MANIFEST_NAME,
                    "manifest must exclude itself",
                )
            )

    return entries, findings


def _inventory(root: Path) -> tuple[set[str] | None, list[Finding]]:
    regular_files: set[str] = set()
    findings: list[Finding] = []
    pending = [root]

    while pending:
        directory = pending.pop()
        try:
            children = sorted(directory.iterdir(), key=lambda path: path.name)
        except OSError:
            return None, [
                _finding(
                    "INVENTORY_READ_ERROR",
                    "",
                    "package inventory could not be read",
                )
            ]
        for child in children:
            relative_path = child.relative_to(root).as_posix()
            try:
                file_info = child.lstat()
            except OSError:
                return None, [
                    _finding(
                        "INVENTORY_READ_ERROR",
                        relative_path,
                        "package inventory entry could not be inspected",
                    )
                ]
            if _is_reparse_point(file_info):
                findings.append(
                    _finding(
                        "MANIFEST_UNSUPPORTED_OBJECT",
                        relative_path,
                        "package contains a symlink or unsupported filesystem object",
                    )
                )
            elif stat.S_ISREG(file_info.st_mode):
                regular_files.add(relative_path)
            elif stat.S_ISDIR(file_info.st_mode):
                pending.append(child)
            else:
                findings.append(
                    _finding(
                        "MANIFEST_UNSUPPORTED_OBJECT",
                        relative_path,
                        "package contains a symlink or unsupported filesystem object",
                    )
                )

    return regular_files, findings


def _read_manifest(root: Path) -> tuple[bytes | None, list[Finding]]:
    manifest_path = root / MANIFEST_NAME
    try:
        file_info = manifest_path.lstat()
    except FileNotFoundError:
        return None, [
            _finding(
                "MANIFEST_NOT_FOUND",
                MANIFEST_NAME,
                "manifest does not exist",
            )
        ]
    except OSError:
        return None, [
            _finding(
                "MANIFEST_READ_ERROR",
                MANIFEST_NAME,
                "manifest could not be inspected",
            )
        ]

    if _is_reparse_point(file_info) or not stat.S_ISREG(file_info.st_mode):
        return None, [
            _finding(
                "MANIFEST_NOT_REGULAR",
                MANIFEST_NAME,
                "manifest is not a regular file",
            )
        ]
    try:
        with manifest_path.open("rb") as stream:
            return stream.read(), []
    except OSError:
        return None, [
            _finding(
                "MANIFEST_READ_ERROR",
                MANIFEST_NAME,
                "manifest could not be read",
            )
        ]


def _contained_target(root: Path, relative_path: str) -> Path | None:
    target = root.joinpath(*relative_path.split("/"))
    try:
        target.resolve(strict=False).relative_to(root)
    except (OSError, ValueError):
        return None
    return target


def _inspect_listed_target(
    root: Path, relative_path: str
) -> tuple[Path | None, Finding | None]:
    target = root
    segments = relative_path.split("/")
    for index, segment in enumerate(segments):
        try:
            target = next(
                (child for child in target.iterdir() if child.name == segment),
                None,
            )
        except OSError:
            return None, _finding(
                "MANIFEST_FILE_READ_ERROR",
                relative_path,
                "listed file could not be inspected",
            )
        if target is None:
            return None, _finding(
                "MANIFEST_FILE_MISSING",
                relative_path,
                "listed file does not exist",
            )
        try:
            file_info = target.lstat()
        except FileNotFoundError:
            return None, _finding(
                "MANIFEST_FILE_MISSING",
                relative_path,
                "listed file does not exist",
            )
        except OSError:
            return None, _finding(
                "MANIFEST_FILE_READ_ERROR",
                relative_path,
                "listed file could not be inspected",
            )

        is_last_segment = index == len(segments) - 1
        if _is_reparse_point(file_info) or (
            is_last_segment
            and not stat.S_ISREG(file_info.st_mode)
        ) or (
            not is_last_segment
            and not stat.S_ISDIR(file_info.st_mode)
        ):
            return None, _finding(
                "MANIFEST_FILE_NOT_REGULAR",
                relative_path,
                "listed path is not a regular file",
            )

    contained_target = _contained_target(root, relative_path)
    if contained_target is None:
        return None, _finding(
            "MANIFEST_PATH_UNSAFE",
            relative_path,
            "manifest target resolves outside the package",
        )
    return contained_target, None


def _digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _verify_files(
    root: Path,
    entries: list[ManifestEntry],
    regular_files: set[str],
) -> list[Finding]:
    findings: list[Finding] = []
    listed_paths = {entry.path for entry in entries if _safe_manifest_path(entry.path)}

    for entry in entries:
        if not _safe_manifest_path(entry.path) or entry.path == MANIFEST_NAME:
            continue
        target, inspection_finding = _inspect_listed_target(root, entry.path)
        if inspection_finding is not None:
            findings.append(inspection_finding)
            continue
        assert target is not None
        try:
            actual_digest = _digest_file(target)
        except OSError:
            findings.append(
                _finding(
                    "MANIFEST_FILE_READ_ERROR",
                    entry.path,
                    "listed file could not be read",
                )
            )
            continue
        if actual_digest != entry.digest:
            findings.append(
                _finding(
                    "MANIFEST_DIGEST_MISMATCH",
                    entry.path,
                    f"expected {entry.digest}; actual {actual_digest}",
                )
            )

    for relative_path in regular_files.difference({MANIFEST_NAME}, listed_paths):
        findings.append(
            _finding(
                "MANIFEST_UNLISTED_FILE",
                relative_path,
                "regular package file is not listed in the manifest",
            )
        )
    return findings


def verify_integrity(context_root: Path) -> list[Finding]:
    root = Path(context_root)
    try:
        file_info = root.lstat()
    except FileNotFoundError:
        return [
            _finding(
                "CONTEXT_ROOT_NOT_FOUND",
                "",
                "context root does not exist",
            )
        ]
    except OSError:
        return [
            _finding(
                "INVENTORY_READ_ERROR",
                "",
                "context root could not be inspected",
            )
        ]
    if _is_reparse_point(file_info) or not stat.S_ISDIR(file_info.st_mode):
        return [
            _finding(
                "CONTEXT_ROOT_NOT_DIRECTORY",
                "",
                "context root is not a directory",
            )
        ]

    try:
        root = root.resolve(strict=True)
    except OSError:
        return [
            _finding(
                "INVENTORY_READ_ERROR",
                "",
                "context root could not be resolved",
            )
        ]

    regular_files, findings = _inventory(root)
    if regular_files is None:
        return _sorted_findings(findings)

    manifest_data, manifest_findings = _read_manifest(root)
    findings.extend(manifest_findings)
    if manifest_data is None:
        return _sorted_findings(findings)

    entries, parse_findings = _parse_manifest(manifest_data)
    findings.extend(parse_findings)
    if entries is None:
        return _sorted_findings(findings)
    if parse_findings:
        return _sorted_findings(findings)

    findings.extend(_verify_files(root, entries, regular_files))
    return _sorted_findings(findings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a self-excluding SHA-256 evidence manifest."
    )
    parser.add_argument("--context-root", required=True, type=Path)
    arguments = parser.parse_args(argv)

    findings = verify_integrity(arguments.context_root)
    for finding in findings:
        line = json.dumps(asdict(finding), sort_keys=True, separators=(",", ":"))
        # Bypass Windows text newline translation: the CLI contract is LF JSONL.
        sys.stdout.buffer.write((line + "\n").encode("ascii"))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
