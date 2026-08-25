from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import subprocess
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path


DIRTY_MARKER = "\nUSER-OWNED-DIRTY-EDIT: preserve this exact line.\n"
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


@dataclass(frozen=True)
class MaterializeReceipt:
    run_id: str
    run_root: str
    baseline_commit: str
    dirty_sha256: str
    git_status: list[str]


def validate_run_id(value: str) -> str:
    if not RUN_ID_PATTERN.fullmatch(value) or value in {".", ".."}:
        raise ValueError(f"invalid run id: {value!r}")
    return value


def _run_git(run_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(run_root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.rstrip()


def _remove_owned_tree(root: Path) -> None:
    def clear_readonly_and_retry(function, path, exception_info) -> None:
        if not isinstance(exception_info[1], PermissionError):
            raise exception_info[1]
        Path(path).chmod(stat.S_IWRITE)
        function(path)

    shutil.rmtree(root, onerror=clear_readonly_and_retry)


def materialize_run(template_root: Path, runs_root: Path, run_id: str) -> MaterializeReceipt:
    validated_run_id = validate_run_id(run_id)
    template_root = template_root.resolve(strict=True)
    runs_root = runs_root.resolve()
    if runs_root == template_root or template_root in runs_root.parents:
        raise ValueError(f"runs root must be outside template root: {runs_root}")
    run_root = runs_root / validated_run_id
    record_path = runs_root / f"{validated_run_id}.baseline.json"
    lock_path = runs_root / f".{validated_run_id}.materialize.lock"
    staging_root = runs_root / f".{validated_run_id}.staging-{uuid.uuid4().hex}"

    if (
        run_root.exists()
        or run_root.is_symlink()
        or record_path.exists()
        or record_path.is_symlink()
    ):
        raise FileExistsError(f"refusing to overwrite existing run: {run_root}")
    if not (template_root / "user-notes.md").is_file():
        raise FileNotFoundError(f"template is missing user-notes.md: {template_root}")

    runs_root.mkdir(parents=True, exist_ok=True)
    lock_file = None
    owns_lock = False
    owns_staging = False
    owns_promoted_run = False
    owns_receipt = False
    lock_token = uuid.uuid4().hex
    try:
        lock_file = lock_path.open("x", encoding="utf-8", newline="\n")
        owns_lock = True
        lock_file.write(lock_token + "\n")
        lock_file.flush()

        if (
            run_root.exists()
            or run_root.is_symlink()
            or record_path.exists()
            or record_path.is_symlink()
        ):
            raise FileExistsError(f"refusing to overwrite existing run: {run_root}")

        staging_root.mkdir()
        owns_staging = True
        shutil.copytree(template_root, staging_root, dirs_exist_ok=True)

        _run_git(staging_root, "init", "-b", "main")
        _run_git(staging_root, "config", "user.name", "Codex Fixture")
        _run_git(staging_root, "config", "user.email", "fixture@example.invalid")
        _run_git(staging_root, "add", ".")
        _run_git(staging_root, "commit", "-m", "fixture: record clean baseline")
        baseline_commit = _run_git(staging_root, "rev-parse", "HEAD")

        user_notes_path = staging_root / "user-notes.md"
        with user_notes_path.open("a", encoding="utf-8", newline="\n") as user_notes:
            user_notes.write(DIRTY_MARKER)

        dirty_sha256 = hashlib.sha256(user_notes_path.read_bytes()).hexdigest().upper()
        git_status = _run_git(staging_root, "status", "--short").splitlines()
        expected_status = [" M user-notes.md"]
        if git_status != expected_status:
            raise RuntimeError(f"unexpected initial dirty state: {git_status!r}")

        receipt = MaterializeReceipt(
            run_id=validated_run_id,
            run_root=str(run_root),
            baseline_commit=baseline_commit,
            dirty_sha256=dirty_sha256,
            git_status=git_status,
        )
        receipt_json = json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n"

        if (
            run_root.exists()
            or run_root.is_symlink()
            or record_path.exists()
            or record_path.is_symlink()
        ):
            raise FileExistsError(f"refusing to overwrite existing run: {run_root}")
        staging_root.rename(run_root)
        owns_staging = False
        owns_promoted_run = True
        record_file = record_path.open("x", encoding="utf-8", newline="\n")
        owns_receipt = True
        with record_file:
            record_file.write(receipt_json)
        owns_receipt = False
        owns_promoted_run = False
        return receipt
    finally:
        try:
            if owns_staging and staging_root.exists():
                _remove_owned_tree(staging_root)
            if owns_receipt and (record_path.exists() or record_path.is_symlink()):
                record_path.unlink()
            if owns_promoted_run and run_root.is_dir():
                _remove_owned_tree(run_root)
        finally:
            try:
                if lock_file is not None:
                    lock_file.close()
            finally:
                if owns_lock:
                    lock_path.unlink(missing_ok=True)


def main() -> int:
    fixture_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Create a non-overwriting write-DAG fixture run.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--template-root", type=Path, default=fixture_root / "template")
    parser.add_argument("--runs-root", type=Path, default=fixture_root / "runs")
    arguments = parser.parse_args()

    receipt = materialize_run(arguments.template_root, arguments.runs_root, arguments.run_id)
    print(json.dumps(asdict(receipt), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
