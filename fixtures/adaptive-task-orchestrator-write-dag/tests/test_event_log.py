from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


FIXTURE_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = FIXTURE_ROOT / "tools"
EVENT_LOG_CLI = TOOLS_ROOT / "event_log.py"
sys.path.insert(0, str(TOOLS_ROOT))

from event_log import EventLogError, record_event, summarize_streams


class RecordEventTests(unittest.TestCase):
    def test_records_stable_utc_and_epoch_nanosecond_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "worker.jsonl"

            record = record_event(
                output,
                task_id="V3-T3-event-log",
                task_revision=1,
                span_id="V3-T3-event-log-r1",
                event="started",
                timestamp_ns=1_000_000_001,
            )

            self.assertEqual(
                record,
                {
                    "schema_version": 1,
                    "task_id": "V3-T3-event-log",
                    "task_revision": 1,
                    "span_id": "V3-T3-event-log-r1",
                    "event": "started",
                    "timestamp_utc": "1970-01-01T00:00:01.000000001Z",
                    "timestamp_ns": 1_000_000_001,
                },
            )
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n",
            )

    def test_appends_a_finish_without_rewriting_the_same_owner_stream(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "worker.jsonl"
            record_event(output, "task-a", 1, "task-a-r1", "started", timestamp_ns=10)
            started_bytes = output.read_bytes()

            record_event(output, "task-a", 1, "task-a-r1", "finished", timestamp_ns=20)

            self.assertTrue(output.read_bytes().startswith(started_bytes))
            records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([record["event"] for record in records], ["started", "finished"])

    def test_rejects_an_owner_mismatch_without_appending(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "worker.jsonl"
            record_event(output, "task-a", 1, "task-a-r1", "started", timestamp_ns=10)
            original_bytes = output.read_bytes()

            with self.assertRaisesRegex(EventLogError, "OWNER_MISMATCH"):
                record_event(output, "task-b", 1, "task-b-r1", "started", timestamp_ns=11)

            self.assertEqual(output.read_bytes(), original_bytes)

    def test_rejects_unknown_duplicate_and_out_of_order_transitions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)

            with self.assertRaisesRegex(EventLogError, "UNKNOWN_EVENT"):
                record_event(
                    temporary_root / "unknown.jsonl",
                    "task-a",
                    1,
                    "task-a-r1",
                    "paused",
                    timestamp_ns=10,
                )

            duplicate = temporary_root / "duplicate.jsonl"
            record_event(duplicate, "task-a", 1, "task-a-r1", "started", timestamp_ns=10)
            with self.assertRaisesRegex(EventLogError, "DUPLICATE_TRANSITION"):
                record_event(duplicate, "task-a", 1, "task-a-r1", "started", timestamp_ns=11)

            with self.assertRaisesRegex(EventLogError, "OUT_OF_ORDER_TRANSITION"):
                record_event(
                    temporary_root / "out-of-order.jsonl",
                    "task-a",
                    1,
                    "task-a-r1",
                    "finished",
                    timestamp_ns=10,
                )

    def test_rejects_a_finish_timestamp_before_its_start(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "worker.jsonl"
            record_event(output, "task-a", 1, "task-a-r1", "started", timestamp_ns=20)

            with self.assertRaisesRegex(EventLogError, "FINISH_BEFORE_START"):
                record_event(output, "task-a", 1, "task-a-r1", "finished", timestamp_ns=19)


class SummarizeStreamsTests(unittest.TestCase):
    def _write_interval(
        self,
        root: Path,
        task_id: str,
        start_ns: int,
        finish_ns: int,
    ) -> Path:
        output = root / f"{task_id}.jsonl"
        span_id = f"{task_id}-r1"
        record_event(output, task_id, 1, span_id, "started", timestamp_ns=start_ns)
        record_event(output, task_id, 1, span_id, "finished", timestamp_ns=finish_ns)
        return output

    def test_rejects_an_incomplete_span(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "worker.jsonl"
            record_event(output, "task-a", 1, "task-a-r1", "started", timestamp_ns=10)

            with self.assertRaisesRegex(EventLogError, "INCOMPLETE_SPAN"):
                summarize_streams([output])

    def test_rejects_a_non_string_event_with_the_stable_unknown_event_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "worker.jsonl"
            output.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "task_id": "task-a",
                        "task_revision": 1,
                        "span_id": "task-a-r1",
                        "event": ["started"],
                        "timestamp_utc": "1970-01-01T00:00:00.000000010Z",
                        "timestamp_ns": 10,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )

            with self.assertRaisesRegex(EventLogError, "UNKNOWN_EVENT"):
                summarize_streams([output])

    def test_classifies_closed_interval_overlap_and_non_overlap_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            task_a = self._write_interval(temporary_root, "task-a", 10, 20)
            task_b = self._write_interval(temporary_root, "task-b", 20, 30)
            task_c = self._write_interval(temporary_root, "task-c", 31, 40)

            summary = summarize_streams([task_c, task_a, task_b])

            self.assertEqual(
                [(item["task_id"], item["start_ns"], item["finish_ns"]) for item in summary["intervals"]],
                [("task-a", 10, 20), ("task-b", 20, 30), ("task-c", 31, 40)],
            )
            self.assertEqual(
                summary["pairs"],
                [
                    {
                        "left": "task-a/r1/task-a-r1",
                        "right": "task-b/r1/task-b-r1",
                        "overlap": True,
                        "overlap_start_ns": 20,
                        "overlap_finish_ns": 20,
                    },
                    {
                        "left": "task-a/r1/task-a-r1",
                        "right": "task-c/r1/task-c-r1",
                        "overlap": False,
                        "overlap_start_ns": None,
                        "overlap_finish_ns": None,
                    },
                    {
                        "left": "task-b/r1/task-b-r1",
                        "right": "task-c/r1/task-c-r1",
                        "overlap": False,
                        "overlap_start_ns": None,
                        "overlap_finish_ns": None,
                    },
                ],
            )
            self.assertEqual(summary["overlap_count"], 1)
            self.assertEqual(summary["non_overlap_count"], 2)

    def test_require_overlap_cli_fails_when_no_pair_overlaps(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            task_a = self._write_interval(temporary_root, "task-a", 10, 20)
            task_b = self._write_interval(temporary_root, "task-b", 21, 30)
            output = temporary_root / "summary.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(EVENT_LOG_CLI),
                    "summarize",
                    "--require-overlap",
                    "--output",
                    str(output),
                    str(task_b),
                    str(task_a),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertIn('"code":"OVERLAP_REQUIRED"', completed.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["overlap_count"], 0)

    def test_summary_cli_writes_stable_json_and_refuses_to_overwrite_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            task_a = self._write_interval(temporary_root, "task-a", 10, 20)
            task_b = self._write_interval(temporary_root, "task-b", 15, 30)
            output = temporary_root / "summary.json"
            command = [
                sys.executable,
                "-B",
                str(EVENT_LOG_CLI),
                "summarize",
                "--output",
                str(output),
                str(task_a),
                str(task_b),
            ]

            first = subprocess.run(command, check=False, capture_output=True, text=True)
            accepted_bytes = output.read_bytes()
            second = subprocess.run(command, check=False, capture_output=True, text=True)

            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertTrue(accepted_bytes.endswith(b"\n"))
            self.assertEqual(second.returncode, 1, second.stdout + second.stderr)
            self.assertIn('"code":"OUTPUT_EXISTS"', second.stderr)
            self.assertEqual(output.read_bytes(), accepted_bytes)


if __name__ == "__main__":
    unittest.main()
