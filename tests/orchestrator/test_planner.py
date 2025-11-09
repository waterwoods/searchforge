import unittest

from agents.orchestrator.flow import ExperimentPlan
from agents.orchestrator import planner


class PlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = {
            "grid": {
                "sample": 100,
                "top_k": [10, 20],
                "mmr": [False, 0.2],
                "ef_search": [32, 64],
                "concurrency": 2,
            }
        }

    def test_make_grid_generates_deterministic_batches(self) -> None:
        plan = ExperimentPlan(
            dataset="fiqa_para_50k",
            sample_size=100,
            search_space={"top_k": [20, 10], "mmr": [0.2, False], "ef_search": [64, 32]},
        )

        batches = planner.make_grid(plan, self.cfg)
        self.assertEqual(len(batches), 4)  # 4 combinations, concurrency 2 -> 4/2 = 2 batches
        self.assertEqual(batches[0].batch_id, "grid-batch-01")
        self.assertEqual(batches[0].concurrency, 2)
        first_task = batches[0].tasks[0]
        self.assertTrue(first_task.config_id.startswith("fiqa_para_50k-k10"))
        params = first_task.parameters
        self.assertEqual(params["top_k"], 10)
        self.assertEqual(params["ef_search"], 32)
        self.assertFalse(params["mmr"])

    def test_make_grid_invalid_concurrency(self) -> None:
        plan = ExperimentPlan(
            dataset="fiqa_para_50k",
            sample_size=100,
            search_space={"top_k": [10], "mmr": [False], "ef_search": [32]},
            concurrency=0,
        )
        with self.assertRaises(ValueError):
            planner.make_grid(plan, self.cfg)

    def test_make_grid_requires_search_values(self) -> None:
        plan = ExperimentPlan(dataset="fiqa_para_50k", sample_size=100, search_space={})
        bad_cfg = {"grid": {"sample": 100, "mmr": [False], "ef_search": [32], "concurrency": 2}}
        with self.assertRaises(ValueError):
            planner.make_grid(plan, bad_cfg)


if __name__ == "__main__":
    unittest.main()

