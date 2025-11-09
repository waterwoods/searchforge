import unittest
from unittest import mock

from fastapi.testclient import TestClient

from services.fiqa_api.app_main import app


class ReportEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_report_missing_run(self) -> None:
        with mock.patch("services.orchestrate_router._orchestrator_flow") as orchestrator:
            orchestrator.get_report_artifacts.side_effect = FileNotFoundError("missing")
            response = self.client.get("/orchestrate/report", params={"run_id": "missing"})
        self.assertEqual(response.status_code, 404)

    def test_report_returns_artifacts(self) -> None:
        artifacts = {
            "winners_json": "reports/run-1/winners.json",
            "winners_md": "reports/run-1/winners.md",
            "pareto_png": "reports/run-1/pareto.png",
            "ab_diff_png": "reports/run-1/ab_diff.png",
            "fail_topn_csv": "reports/run-1/failTopN.csv",
            "events_jsonl": "reports/events/run-1.jsonl",
        }
        with mock.patch("services.orchestrate_router._orchestrator_flow") as orchestrator:
            orchestrator.get_report_artifacts.return_value = artifacts
            response = self.client.get("/orchestrate/report", params={"run_id": "run-1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["artifacts"], artifacts)


if __name__ == "__main__":
    unittest.main()

