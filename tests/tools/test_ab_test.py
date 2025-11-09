import csv
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.ab_test import run_ab
from tools.run_eval import RunEvalResult


class AbTestUtilitiesTests(unittest.TestCase):
    def test_run_ab_creates_artifacts(self) -> None:
        baseline_cfg = {
            "collection": "fiqa_para_50k",
            "top_k": 10,
            "mmr": False,
            "mmr_lambda": 0.0,
            "ef_search": 32,
        }
        challenger_cfg = {
            "collection": "fiqa_para_50k",
            "top_k": 20,
            "mmr": True,
            "mmr_lambda": 0.2,
            "ef_search": 64,
        }

        with tempfile.TemporaryDirectory() as tmp:
            base_metrics_path = Path(tmp) / "base.json"
            candidate_metrics_path = Path(tmp) / "candidate.json"
            cfg = {"reports_dir": tmp, "run_id": "orch-test", "ab": {"concurrency": 2}}

            with mock.patch(
                "tools.ab_test.run_ab_task",
                side_effect=[
                    RunEvalResult("job-base", base_metrics_path, {}),
                    RunEvalResult("job-candidate", candidate_metrics_path, {}),
                ],
            ), mock.patch(
                "tools.ab_test.aggregate_metrics",
                side_effect=[
                    {"recall_at_10": 0.6, "p95_ms": 120.0, "cost": 0.01},
                    {"recall_at_10": 0.65, "p95_ms": 115.0, "cost": 0.015},
                ],
            ):
                result = run_ab(baseline_cfg, challenger_cfg, sample_n=80, cfg=cfg)

            chart_path = Path(result["chart_path"])
            csv_path = Path(result["csv_path"])
            self.assertTrue(chart_path.exists())
            self.assertTrue(csv_path.exists())
            self.assertAlmostEqual(result["diff_table"]["recall_at_10"], 0.05)

            with csv_path.open("r", encoding="utf-8") as fp:
                rows = list(csv.reader(fp))
            self.assertEqual(rows[0], ["metric", "baseline", "challenger", "delta"])
            self.assertEqual(len(rows), 4)


if __name__ == "__main__":
    unittest.main()
