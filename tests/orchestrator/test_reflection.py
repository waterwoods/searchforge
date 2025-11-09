import unittest

from agents.orchestrator.reflection import post_phase_reflect


class ReflectionTests(unittest.TestCase):
    def test_reflection_keep_when_metrics_stable(self) -> None:
        stats = {
            "run_id": "orch-1",
            "stage": "GRID",
            "results": [
                {"status": "ok", "metrics": {"recall_at_10": 0.6}},
                {"status": "ok", "metrics": {"recall_at_10": 0.61}},
            ],
            "thresholds": {"failure_rate": 0.3, "recall_variance": 0.02},
        }
        decision = post_phase_reflect(stats)
        self.assertEqual(decision["action"], "keep")

    def test_reflection_early_stop_on_failure_rate(self) -> None:
        stats = {
            "run_id": "orch-2",
            "stage": "GRID",
            "results": [
                {"status": "ok", "metrics": {"recall_at_10": 0.6}},
                {"status": "error", "metrics": {"recall_at_10": 0.61}},
                {"status": "error", "metrics": {"recall_at_10": 0.62}},
            ],
            "thresholds": {"failure_rate": 0.5, "recall_variance": 0.02},
        }
        decision = post_phase_reflect(stats)
        self.assertEqual(decision["action"], "early_stop")
        self.assertIn("failure_rate", decision["reason"])


if __name__ == "__main__":
    unittest.main()

