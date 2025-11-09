import json
import tempfile
import unittest
from pathlib import Path

from observe.logging import EventLogger


class EventLoggerTests(unittest.TestCase):
    def test_stage_events_logged_with_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            logger = EventLogger(base_dir=Path(tmp))
            run_id = "orch-test"
            logger.initialize(run_id)

            logger.log_event(run_id, "RUN_STARTED", {"stage": "INIT"})
            logger.log_stage_event(
                run_id,
                stage="SMOKE",
                status="started",
                payload={"stage": "SMOKE", "timestamp": "2025-11-08T00:00:00Z"},
            )
            logger.log_stage_event(
                run_id,
                stage="SMOKE",
                status="done",
                payload={
                    "stage": "SMOKE",
                    "duration_ms": 1234,
                    "metrics": {"recall_at_10": 0.51, "p95_ms": 110.0},
                },
            )

            events_path = Path(tmp) / f"{run_id}.jsonl"
            with events_path.open("r", encoding="utf-8") as fp:
                lines = [json.loads(line) for line in fp]

            self.assertEqual(len(lines), 3)
            smoke_done = lines[-1]
            self.assertEqual(smoke_done["event_type"], "SMOKE_DONE")
            self.assertIn("duration_ms", smoke_done["payload"])
            self.assertIn("metrics", smoke_done["payload"])

    def test_read_events_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            logger = EventLogger(base_dir=Path(tmp))
            run_id = "orch-test"
            logger.initialize(run_id)
            for idx in range(5):
                logger.log_event(run_id, f"EVENT_{idx}", {"index": idx})

            recent = logger.read_events(run_id, limit=2)
            self.assertEqual(len(recent), 2)
            self.assertEqual(recent[0]["event_type"], "EVENT_3")
            self.assertEqual(recent[1]["event_type"], "EVENT_4")


if __name__ == "__main__":
    unittest.main()

