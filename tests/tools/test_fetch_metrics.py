import json
import tempfile
import unittest
from pathlib import Path

import csv

from tools.fetch_metrics import MetricsAggregationError, aggregate_metrics, write_fail_topn_csv


class FetchMetricsTests(unittest.TestCase):
    def _write_metrics(self, directory: Path, job_id: str, payload: dict) -> Path:
        job_dir = directory / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        path = job_dir / "metrics.json"
        with path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp)
        return path

    def test_aggregate_single_metrics_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            payload = {
                "job_id": "job123",
                "status": "ok",
                "metrics": {"recall_at_10": 0.6, "p95_ms": 110.0, "cost_per_query": 0.01, "count": 50},
            }
            path = self._write_metrics(base, "job123", payload)

            summary = aggregate_metrics(path)

            self.assertEqual(summary["jobs"], ["job123"])
            self.assertAlmostEqual(summary["recall_at_10"], 0.6)
            self.assertAlmostEqual(summary["p95_ms"], 110.0)
            self.assertAlmostEqual(summary["cost"], 0.5)  # 0.01 * 50
            self.assertEqual(summary["count"], 50)

    def test_aggregate_multiple_metrics_weighted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_metrics(
                base,
                "jobA",
                {
                    "job_id": "jobA",
                    "status": "ok",
                    "metrics": {"recall_at_10": 0.5, "p95_ms": 150.0, "cost_per_query": 0.02, "count": 40},
                },
            )
            self._write_metrics(
                base,
                "jobB",
                {
                    "job_id": "jobB",
                    "status": "ok",
                    "metrics": {"recall_at_10": 0.7, "p95_ms": 90.0, "cost_per_query": 0.015, "count": 60},
                },
            )

            pattern = base / "*" / "metrics.json"
            summary = aggregate_metrics(str(pattern))

            self.assertCountEqual(summary["jobs"], ["jobA", "jobB"])
            self.assertAlmostEqual(summary["count"], 100)
            expected_recall = (0.5 * 40 + 0.7 * 60) / 100
            self.assertAlmostEqual(summary["recall_at_10"], expected_recall)
            expected_p95 = (150.0 * 40 + 90.0 * 60) / 100
            self.assertAlmostEqual(summary["p95_ms"], expected_p95)
            expected_cost = 0.02 * 40 + 0.015 * 60
            self.assertAlmostEqual(summary["cost"], expected_cost)

    def test_missing_source_raises(self) -> None:
        with self.assertRaises(MetricsAggregationError):
            aggregate_metrics("nonexistent/metrics.json")

    def test_write_fail_topn_csv(self) -> None:
        failures = [
            {"status": "error", "error": "timeout"},
            {"status": "error", "error": "timeout"},
            {"status": "failed", "error": "5xx"},
            {"status": "ok"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fail_topn.csv"
            csv_path = write_fail_topn_csv(failures, path, top_n=2)
            self.assertTrue(csv_path.exists())
            with csv_path.open("r", encoding="utf-8") as fp:
                rows = list(csv.reader(fp))
            self.assertEqual(rows[0], ["reason", "count"])
            self.assertEqual(rows[1], ["timeout", "2"])
            self.assertEqual(rows[2], ["5xx", "1"])


if __name__ == "__main__":
    unittest.main()

