import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from typing import Dict
from unittest import mock

from agents.orchestrator import planner
from agents.orchestrator.flow import (
    ExperimentPlan,
    OrchestratorFlow,
    PIPELINE_STAGES,
    generate_run_id,
)
from agents.orchestrator.memory import RunMemory
from observe.logging import EventLogger
from tools.run_eval import RunEvalResult


class ExperimentFlowTests(unittest.TestCase):
    def test_experiment_plan_serialization(self) -> None:
        payload: Dict[str, object] = {
            "dataset": "fiqa_para_50k",
            "sample_size": 50,
            "search_space": {"top_k": [10, 20], "mmr": [False, 0.3]},
            "budget": {"max_time_minutes": 30},
            "concurrency": 4,
            "baseline_id": "baseline_v1",
            "metadata": {"initiator": "unit-test"},
        }

        plan = ExperimentPlan.from_dict(payload)
        serialized = plan.to_dict()

        self.assertEqual(serialized["dataset"], payload["dataset"])
        self.assertEqual(serialized["sample_size"], payload["sample_size"])
        self.assertEqual(serialized["search_space"], payload["search_space"])
        self.assertEqual(serialized["budget"], payload["budget"])
        self.assertEqual(serialized["concurrency"], payload["concurrency"])
        self.assertEqual(serialized["baseline_id"], payload["baseline_id"])
        self.assertEqual(serialized["metadata"], payload["metadata"])

    def test_generate_run_id_format(self) -> None:
        run_id = generate_run_id()
        self.assertTrue(run_id.startswith("orch-"))
        parts = run_id.split("-")
        self.assertEqual(len(parts), 3)
        self.assertEqual(len(parts[2]), 12)

    def test_start_creates_events_and_metadata(self) -> None:
        policies_tmp = Path(tempfile.gettempdir()) / f"orchestrator_policies_{os.getpid()}_{id(self)}.json"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                events_dir = base / "events"
                memory_dir = base / "memory"
                memory_dir.mkdir(parents=True, exist_ok=True)
                logger = EventLogger(base_dir=events_dir)
                run_memory = RunMemory(base_dir=memory_dir)
                (memory_dir / "runs.jsonl").touch()
                policies_path = base / "policies.json"
                policies_path.write_text(
                    json.dumps(
                        {
                            "policies": {
                                "baseline_v1": {
                                    "collection": "fiqa_para_50k",
                                    "top_k": 10,
                                    "mmr": False,
                                    "mmr_lambda": 0.0,
                                    "ef_search": 32,
                                }
                            }
                        }
                    ),
                    encoding="utf-8",
                )
                shutil.copyfile(policies_path, policies_tmp)

                config = {
                    "reports_dir": str(base / "reports"),
                    "runs_dir": str(base / ".runs"),
                    "base_url": "http://localhost:8000",
                    "allowed_hosts": ["localhost:8000"],
                    "smoke": {
                        "sample": 5,
                        "top_k": 5,
                        "mmr": False,
                        "concurrency": 1,
                        "timeout_s": 5,
                        "max_retries": 1,
                        "backoff_s": 0.1,
                        "rate_limit_per_sec": 10,
                    },
                    "executor_workers": 1,
                    "grid": {"concurrency": 1},
                    "ab": {"sample": 80, "concurrency": 1},
                    "winners_source": str(base / "reports" / "winners.final.json"),
                    "policies_path": str(policies_tmp),
                    "baseline_policy": "baseline_v1",
                }
                flow = OrchestratorFlow(logger=logger, run_memory=run_memory, config=config)

                plan = ExperimentPlan(
                    dataset="fiqa_para_50k",
                    sample_size=50,
                    search_space={"top_k": [10]},
                    baseline_id="baseline_v1",
                )
                self.assertEqual(plan.baseline_id, "baseline_v1")

                fake_metrics_dir = Path(config["runs_dir"]) / "fake-job"
                fake_metrics_path = fake_metrics_dir / "metrics.json"
                fake_metrics_dir.mkdir(parents=True, exist_ok=True)
                with fake_metrics_path.open("w", encoding="utf-8") as fp:
                    json.dump({"job_id": "fake-job", "status": "ok", "metrics": {}}, fp)

                grid_batch = planner.GridBatch(
                    batch_id="grid-batch-01",
                    concurrency=1,
                    tasks=[
                        planner.GridTask(
                            config_id="fiqa_para_50k-k10-ef32-nommr",
                            parameters={
                                "dataset": "fiqa_para_50k",
                                "sample": 100,
                                "top_k": 10,
                                "mmr": False,
                                "mmr_lambda": 0.0,
                                "ef_search": 32,
                                "concurrency": 1,
                            },
                        )
                    ],
                )

                def _aggregate_side_effect(*args, **kwargs):
                    return {"recall_at_10": 0.6, "p95_ms": 110, "cost": 0.1}

                def _fake_reflection(stats, logger=None):
                    if logger is not None:
                        logger.log_event(
                            stats.get("run_id", "unknown"),
                            "REFLECTION_DECISION",
                            {
                                "stage": stats.get("stage"),
                                "action": "keep",
                                "reason": "ok",
                            },
                        )
                    return {"action": "keep", "reason": "ok"}

                def _fake_run_ab(baseline_cfg, challenger_cfg, sample_n, ab_cfg):
                    run_dir = Path(ab_cfg.get("reports_dir")) / ab_cfg.get("run_id")
                    run_dir.mkdir(parents=True, exist_ok=True)
                    chart = run_dir / "ab_diff.png"
                    chart.touch()
                    csv_path = run_dir / "ab_diff.csv"
                    with csv_path.open("w", encoding="utf-8") as fp:
                        fp.write("metric,baseline,challenger,delta\n")
                    return {
                        "diff_table": {"recall_at_10": 0.05, "p95_ms": -5.0, "cost": 0.001},
                        "chart_path": chart,
                        "csv_path": csv_path,
                        "baseline_metrics": {"recall_at_10": 0.6, "p95_ms": 120.0, "cost": 0.01},
                        "challenger_metrics": {"recall_at_10": 0.65, "p95_ms": 115.0, "cost": 0.015},
                        "baseline_job_id": "job-base",
                        "challenger_job_id": "job-candidate",
                    }

                with mock.patch("agents.orchestrator.flow.run_smoke") as mock_run_smoke, mock.patch(
                    "agents.orchestrator.flow.aggregate_metrics", side_effect=_aggregate_side_effect
                ), mock.patch(
                    "agents.orchestrator.flow.planner.make_grid", return_value=[grid_batch]
                ), mock.patch(
                    "agents.orchestrator.flow.run_grid_task"
                ) as mock_run_grid, mock.patch(
                    "agents.orchestrator.flow.reflection.post_phase_reflect", side_effect=_fake_reflection
                ), mock.patch(
                    "agents.orchestrator.flow.run_ab", side_effect=_fake_run_ab
                ), mock.patch(
                    "agents.orchestrator.flow.render_pareto_chart",
                    side_effect=lambda rows, path: Path(path).touch() or path,
                ), mock.patch(
                    "agents.orchestrator.flow.write_fail_topn_csv",
                    side_effect=lambda results, output_path, top_n=10: Path(output_path).touch() or Path(output_path),
                ):
                    mock_run_smoke.return_value = RunEvalResult(
                        job_id="fake-job",
                        metrics_path=fake_metrics_path,
                        summary={},
                    )
                    mock_run_grid.return_value = RunEvalResult(
                        job_id="grid-job",
                        metrics_path=fake_metrics_path,
                        summary={"metrics": {"recall_at_10": 0.6}},
                    )
                    run_id = flow.start(plan)
                    # wait for background execution
                    deadline = time.time() + 2
                    while time.time() < deadline:
                        future = flow._futures.get(run_id)  # pylint: disable=protected-access
                        if future is None or future.done():
                            break
                        time.sleep(0.01)

                event_path = events_dir / f"{run_id}.jsonl"
                self.assertTrue(event_path.exists())
                with event_path.open("r", encoding="utf-8") as fp:
                    events = [json.loads(line) for line in fp]

                event_types = [event["event_type"] for event in events]
                if "RUN_FAILED" in event_types:
                    last_error = next(
                        (event.get("payload", {}).get("error") for event in events if event.get("event_type") == "RUN_FAILED"),
                        "unknown",
                    )
                    self.fail(f"Pipeline failed unexpectedly: {last_error}")
                self.assertIn("RUN_STARTED", event_types)
                self.assertIn("SMOKE_STARTED", event_types)
                self.assertIn("SMOKE_DONE", event_types)
                self.assertIn("GRID_STARTED", event_types)
                self.assertIn("GRID_DONE", event_types)
                self.assertIn("REFLECTION_DECISION", event_types)
                self.assertIn("AB_STARTED", event_types)
                self.assertIn("AB_DONE", event_types)
                self.assertIn("SELECT_STARTED", event_types)
                self.assertIn("SELECT_DONE", event_types)
                self.assertIn("PUBLISH_STARTED", event_types)
                self.assertIn("PUBLISH_DONE", event_types)
                self.assertIn("RUN_COMPLETED", event_types)

                record = run_memory.get(run_id)
                self.assertIsNotNone(record)
                assert record is not None  # for mypy
                self.assertEqual(record.plan["dataset"], plan.dataset)
                self.assertIn("smoke", record.metadata)
                self.assertIn("grid", record.metadata)
                self.assertIn("ab", record.metadata)
                self.assertIn("winner", record.metadata)
        finally:
            if policies_tmp.exists():
                policies_tmp.unlink()

    def test_get_status_returns_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            events_dir = base / "events"
            memory_dir = base / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            logger = EventLogger(base_dir=events_dir)
            run_memory = RunMemory(base_dir=memory_dir)
            (memory_dir / "runs.jsonl").touch()
            config = {
                "reports_dir": str(base / "reports"),
                "runs_dir": str(base / ".runs"),
                "base_url": "http://localhost:8000",
                "allowed_hosts": ["localhost:8000"],
                "smoke": {
                    "sample": 5,
                    "top_k": 5,
                    "mmr": False,
                    "concurrency": 1,
                    "timeout_s": 5,
                    "max_retries": 1,
                    "backoff_s": 0.1,
                    "rate_limit_per_sec": 10,
                },
                "executor_workers": 1,
            }
            flow = OrchestratorFlow(logger=logger, run_memory=run_memory, config=config)
            run_id = "orch-status-test"
            logger.initialize(run_id)
            logger.log_event(run_id, "RUN_STARTED", {"stage": "INIT"})
            logger.log_stage_event(run_id, "SMOKE", "done", {"stage": "SMOKE", "metrics": {"recall_at_10": 0.5}})
            logger.log_stage_event(run_id, "GRID", "done", {"stage": "GRID", "metrics": {"recall_at_10": 0.55}})
            logger.log_event(run_id, "RUN_COMPLETED", {"stage": "GRID"})

            status = flow.get_status(run_id)
            self.assertEqual(status["stage"], "GRID")
            self.assertEqual(status["status"], "completed")
            self.assertEqual(status["progress"]["total"], len(PIPELINE_STAGES))
            self.assertEqual(status["latest_metrics"]["recall_at_10"], 0.55)

    def test_select_winner_prefers_high_recall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            events_dir = base / "events"
            memory_dir = base / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            logger = EventLogger(base_dir=events_dir)
            run_memory = RunMemory(base_dir=memory_dir)
            (memory_dir / "runs.jsonl").touch()
            config = {
                "reports_dir": str(base / "reports"),
                "runs_dir": str(base / ".runs"),
                "base_url": "http://localhost:8000",
                "allowed_hosts": ["localhost:8000"],
                "smoke": {},
                "grid": {},
            }
            flow = OrchestratorFlow(logger=logger, run_memory=run_memory, config=config)
            run_id = "orch-select"
            logger.initialize(run_id)

            tasks = [
                {
                    "config_id": "cfg-a",
                    "status": "ok",
                    "metrics": {"recall_at_10": 0.62, "p95_ms": 120.0, "cost": 0.02},
                    "parameters": {"dataset": "fiqa_para_50k", "top_k": 20, "ef_search": 64},
                },
                {
                    "config_id": "cfg-b",
                    "status": "ok",
                    "metrics": {"recall_at_10": 0.60, "p95_ms": 110.0, "cost": 0.015},
                    "parameters": {"dataset": "fiqa_para_50k", "top_k": 10, "ef_search": 32},
                },
            ]
            plan = ExperimentPlan(
                dataset="fiqa_para_50k",
                sample_size=50,
                search_space={"top_k": [10]},
                baseline_id="baseline_v1",
            )
            winner = flow._select_winner(run_id, plan, {"tasks": tasks})
            self.assertEqual(winner["config_id"], "cfg-a")


if __name__ == "__main__":
    unittest.main()

