import unittest
from unittest import mock

from fastapi.testclient import TestClient

from services.fiqa_api.app_main import app


class StatusEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_status_missing_run_returns_404(self) -> None:
        with mock.patch("services.orchestrate_router._orchestrator_flow") as mock_flow:
            mock_flow.get_status.side_effect = KeyError("missing")
            resp = self.client.get("/orchestrate/status", params={"run_id": "missing"})
        self.assertEqual(resp.status_code, 404)

    def test_status_returns_payload(self) -> None:
        payload = {
            "run_id": "orch-123",
            "stage": "SMOKE",
            "status": "completed",
            "progress": {"current_stage": "SMOKE", "completed": 1, "total": 5, "status": "completed"},
            "latest_metrics": {"recall_at_10": 0.6},
            "recent_events": [],
            "reflections": [],
        }
        with mock.patch("services.orchestrate_router._orchestrator_flow") as mock_flow:
            mock_flow.get_status.return_value = payload
            resp = self.client.get("/orchestrate/status", params={"run_id": "orch-123"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["run_id"], "orch-123")
        self.assertEqual(resp.json()["stage"], "SMOKE")

    def test_status_detail_lite(self) -> None:
        payload = {
            "run_id": "orch-123",
            "stage": "SMOKE",
            "status": "completed",
            "progress": {"current_stage": "SMOKE", "completed": 1, "total": 5, "status": "completed"},
            "latest_metrics": {"recall_at_10": 0.6},
            "recent_events": [],
            "reflections": [],
        }
        with mock.patch("services.orchestrate_router._orchestrator_flow") as mock_flow:
            mock_flow.get_status.return_value = payload
            resp = self.client.get("/orchestrate/status", params={"run_id": "orch-123", "detail": "lite"})
        self.assertEqual(resp.status_code, 200)
        mock_flow.get_status.assert_called_once_with("orch-123", detail="lite")


if __name__ == "__main__":
    unittest.main()

