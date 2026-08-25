from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Sequence


SCHEMA_VERSION = 1
EVENTS = frozenset({"started", "finished"})
RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "task_id",
        "task_revision",
        "span_id",
        "event",
        "timestamp_utc",
        "timestamp_ns",
    }
)


class EventLogError(ValueError):
    def __init__(self, code: str, path: Path | str, detail: str) -> None:
        self.code = code
        self.path = str(path)
        self.detail = detail
        super().__init__(f"{code}: {self.path}: {detail}")

    def diagnostic(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "detail": self.detail}


def _fail(code: str, path: Path | str, detail: str) -> None:
    raise EventLogError(code, path, detail)


def _timestamp_utc(timestamp_ns: int, path: Path | str = "timestamp_ns") -> str:
    if isinstance(timestamp_ns, bool) or not isinstance(timestamp_ns, int) or timestamp_ns < 0:
        _fail("INVALID_TIMESTAMP", path, "timestamp_ns must be a non-negative integer")
    seconds, nanoseconds = divmod(timestamp_ns, 1_000_000_000)
    try:
        date_time = datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError) as error:
        _fail("INVALID_TIMESTAMP", path, str(error))
    return f"{date_time:%Y-%m-%dT%H:%M:%S}.{nanoseconds:09d}Z"


def _validate_identity(task_id: object, task_revision: object, span_id: object, path: Path | str) -> None:
    if not isinstance(task_id, str) or not task_id:
        _fail("INVALID_TASK_ID", path, "task_id must be a non-empty string")
    if isinstance(task_revision, bool) or not isinstance(task_revision, int) or task_revision < 1:
        _fail("INVALID_TASK_REVISION", path, "task_revision must be a positive integer")
    if not isinstance(span_id, str) or not span_id:
        _fail("INVALID_SPAN_ID", path, "span_id must be a non-empty string")


def _validate_record(record: object, path: Path, line_number: int) -> dict[str, object]:
    location = f"{path}:{line_number}"
    if not isinstance(record, dict):
        _fail("INVALID_RECORD", location, "record must be a JSON object")
    fields = frozenset(record)
    if fields != RECORD_FIELDS:
        missing = sorted(RECORD_FIELDS - fields)
        unknown = sorted(fields - RECORD_FIELDS)
        _fail("INVALID_RECORD_FIELDS", location, f"missing={missing!r}; unknown={unknown!r}")
    if record["schema_version"] != SCHEMA_VERSION:
        _fail("UNKNOWN_SCHEMA_VERSION", location, repr(record["schema_version"]))
    _validate_identity(record["task_id"], record["task_revision"], record["span_id"], location)
    event = record["event"]
    if not isinstance(event, str) or event not in EVENTS:
        _fail("UNKNOWN_EVENT", location, repr(event))
    timestamp_ns = record["timestamp_ns"]
    expected_utc = _timestamp_utc(timestamp_ns, location)
    if record["timestamp_utc"] != expected_utc:
        _fail(
            "TIMESTAMP_MISMATCH",
            location,
            f"timestamp_utc must be {expected_utc!r}",
        )
    return record


def _validate_transitions(
    records: Sequence[dict[str, object]],
    path: Path,
    *,
    require_complete: bool,
) -> list[dict[str, object]]:
    owner: tuple[str, int] | None = None
    spans: dict[str, dict[str, object]] = {}
    for line_number, record in enumerate(records, start=1):
        record_owner = (str(record["task_id"]), int(record["task_revision"]))
        if owner is None:
            owner = record_owner
        elif record_owner != owner:
            _fail(
                "OWNER_MISMATCH",
                f"{path}:{line_number}",
                f"expected {owner[0]}/r{owner[1]}, received {record_owner[0]}/r{record_owner[1]}",
            )

        span_id = str(record["span_id"])
        event = str(record["event"])
        span = spans.get(span_id)
        if event == "started":
            if span is not None:
                _fail("DUPLICATE_TRANSITION", f"{path}:{line_number}", f"duplicate started for {span_id}")
            spans[span_id] = {"started": record, "finished": None}
            continue

        if span is None:
            _fail(
                "OUT_OF_ORDER_TRANSITION",
                f"{path}:{line_number}",
                f"finished precedes started for {span_id}",
            )
        if span["finished"] is not None:
            _fail("DUPLICATE_TRANSITION", f"{path}:{line_number}", f"duplicate finished for {span_id}")
        started = span["started"]
        assert isinstance(started, dict)
        if int(record["timestamp_ns"]) < int(started["timestamp_ns"]):
            _fail(
                "FINISH_BEFORE_START",
                f"{path}:{line_number}",
                f"finish timestamp precedes start for {span_id}",
            )
        span["finished"] = record

    if require_complete:
        for span_id in sorted(spans):
            if spans[span_id]["finished"] is None:
                _fail("INCOMPLETE_SPAN", path, f"missing finished event for {span_id}")
    return [spans[span_id] for span_id in sorted(spans)]


def _read_stream(path: Path, *, require_complete: bool) -> list[dict[str, object]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        _fail("STREAM_READ_ERROR", path, str(error))
    if not lines:
        _fail("EMPTY_STREAM", path, "event stream contains no records")

    records: list[dict[str, object]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line:
            _fail("INVALID_JSON", f"{path}:{line_number}", "blank JSONL record")
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as error:
            _fail("INVALID_JSON", f"{path}:{line_number}", error.msg)
        records.append(_validate_record(parsed, path, line_number))
    _validate_transitions(records, path, require_complete=require_complete)
    return records


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def record_event(
    output: Path,
    task_id: str,
    task_revision: int,
    span_id: str,
    event: str,
    *,
    timestamp_ns: int | None = None,
) -> dict[str, object]:
    output = Path(output)
    _validate_identity(task_id, task_revision, span_id, output)
    if not isinstance(event, str) or event not in EVENTS:
        _fail("UNKNOWN_EVENT", output, repr(event))
    current_timestamp_ns = time.time_ns() if timestamp_ns is None else timestamp_ns
    record: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id,
        "task_revision": task_revision,
        "span_id": span_id,
        "event": event,
        "timestamp_utc": _timestamp_utc(current_timestamp_ns, output),
        "timestamp_ns": current_timestamp_ns,
    }

    existing: list[dict[str, object]] = []
    if output.exists():
        existing = _read_stream(output, require_complete=False)
        first = existing[0]
        existing_owner = (first["task_id"], first["task_revision"])
        requested_owner = (task_id, task_revision)
        if requested_owner != existing_owner:
            _fail(
                "OWNER_MISMATCH",
                output,
                f"expected {existing_owner[0]}/r{existing_owner[1]}, received {task_id}/r{task_revision}",
            )

    _validate_transitions([*existing, record], output, require_complete=False)
    mode = "a" if existing else "x"
    try:
        with output.open(mode, encoding="utf-8", newline="\n") as event_stream:
            event_stream.write(_canonical_json(record) + "\n")
            event_stream.flush()
    except FileExistsError:
        _fail("STREAM_EXISTS", output, "stream appeared while claiming first ownership")
    except OSError as error:
        _fail("STREAM_WRITE_ERROR", output, str(error))
    return record


def summarize_streams(stream_paths: Sequence[Path]) -> dict[str, object]:
    if not stream_paths:
        _fail("NO_STREAMS", "streams", "at least one stream is required")

    intervals: list[dict[str, object]] = []
    owners: dict[tuple[str, int], Path] = {}
    identities: set[str] = set()
    for stream_path in stream_paths:
        path = Path(stream_path)
        records = _read_stream(path, require_complete=True)
        owner = (str(records[0]["task_id"]), int(records[0]["task_revision"]))
        if owner in owners:
            _fail(
                "DUPLICATE_OWNER_STREAM",
                path,
                f"owner {owner[0]}/r{owner[1]} already appears in {owners[owner]}",
            )
        owners[owner] = path
        for span in _validate_transitions(records, path, require_complete=True):
            started = span["started"]
            finished = span["finished"]
            assert isinstance(started, dict) and isinstance(finished, dict)
            identity = f"{owner[0]}/r{owner[1]}/{started['span_id']}"
            if identity in identities:
                _fail("DUPLICATE_SPAN", path, identity)
            identities.add(identity)
            intervals.append(
                {
                    "identity": identity,
                    "task_id": owner[0],
                    "task_revision": owner[1],
                    "span_id": started["span_id"],
                    "start_utc": started["timestamp_utc"],
                    "start_ns": started["timestamp_ns"],
                    "finish_utc": finished["timestamp_utc"],
                    "finish_ns": finished["timestamp_ns"],
                }
            )

    intervals.sort(key=lambda interval: str(interval["identity"]))
    pairs: list[dict[str, object]] = []
    for left, right in combinations(intervals, 2):
        overlap_start = max(int(left["start_ns"]), int(right["start_ns"]))
        overlap_finish = min(int(left["finish_ns"]), int(right["finish_ns"]))
        overlaps = overlap_start <= overlap_finish
        pairs.append(
            {
                "left": left["identity"],
                "right": right["identity"],
                "overlap": overlaps,
                "overlap_start_ns": overlap_start if overlaps else None,
                "overlap_finish_ns": overlap_finish if overlaps else None,
            }
        )
    overlap_count = sum(pair["overlap"] is True for pair in pairs)
    return {
        "schema_version": SCHEMA_VERSION,
        "intervals": intervals,
        "pairs": pairs,
        "overlap_count": overlap_count,
        "non_overlap_count": len(pairs) - overlap_count,
    }


def _write_summary(output: Path, summary: dict[str, object]) -> None:
    try:
        with output.open("x", encoding="utf-8", newline="\n") as summary_file:
            summary_file.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    except FileExistsError:
        _fail("OUTPUT_EXISTS", output, "refusing to overwrite an accepted summary")
    except OSError as error:
        _fail("OUTPUT_WRITE_ERROR", output, str(error))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record and summarize worker-owned event streams.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    record_parser = subparsers.add_parser("record", help="Append one event to an owned JSONL stream.")
    record_parser.add_argument("--output", type=Path, required=True)
    record_parser.add_argument("--task-id", required=True)
    record_parser.add_argument("--task-revision", type=int, required=True)
    record_parser.add_argument("--span-id", required=True)
    record_parser.add_argument("--event", required=True)

    summarize_parser = subparsers.add_parser("summarize", help="Validate streams and summarize intervals.")
    summarize_parser.add_argument("--require-overlap", action="store_true")
    summarize_parser.add_argument("--output", type=Path, required=True)
    summarize_parser.add_argument("streams", type=Path, nargs="+")
    return parser


def main() -> int:
    arguments = _build_parser().parse_args()
    try:
        if arguments.command == "record":
            record = record_event(
                arguments.output,
                arguments.task_id,
                arguments.task_revision,
                arguments.span_id,
                arguments.event,
            )
            print(_canonical_json(record))
            return 0

        summary = summarize_streams(arguments.streams)
        _write_summary(arguments.output, summary)
        print(_canonical_json(summary))
        if arguments.require_overlap and summary["overlap_count"] == 0:
            diagnostic = EventLogError(
                "OVERLAP_REQUIRED",
                arguments.output,
                "no interval pair overlaps",
            )
            print(_canonical_json(diagnostic.diagnostic()), file=sys.stderr)
            return 1
        return 0
    except EventLogError as error:
        print(_canonical_json(error.diagnostic()), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
