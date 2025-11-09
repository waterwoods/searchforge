import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agents.orchestrator.flow import ExperimentPlan
from tools.run_eval import RunEvalError, run_grid_task, run_smoke


class RunEvalSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.base_cfg = {
            "base_url": "http://localhost:8000",
            "allowed_hosts": ["localhost:8000"],
            "runs_dir": str(Path(self.tmpdir.name) / ".runs"),
            "smoke": {
                "sample": 50,
                "top_k": 10,
                "mmr": False,
                "concurrency": 2,
                "timeout_s": 5,
                "max_retries": 2,
                "backoff_s": 0.1,
                "rate_limit_per_sec": 10,
            },
        }
        self.health_patch = mock.patch("tools.run_eval.check_backend_health", return_value=None)
        self.health_patch.start()
        self.addCleanup(self.health_patch.stop)

    def test_run_smoke_success(self) -> None:
        plan = ExperimentPlan(
            dataset="fiqa_para_50k",
            sample_size=50,
            search_space={"top_k": [10]},
        )

        def _fake_run(cmd, check, timeout, env):  # type: ignore[override]
            metrics_path = Path(env["RUNS_DIR"]) / env["JOB_ID"] / "metrics.json"
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "job_id": env["JOB_ID"],
                "status": "ok",
                "metrics": {"recall_at_10": 0.42, "p95_ms": 123.4, "cost_per_query": 0.005},
                "latency_breakdown_ms": {"search": 80.0},
            }
            with metrics_path.open("w", encoding="utf-8") as fp:
                json.dump(payload, fp)
            return subprocess.CompletedProcess(cmd, 0)

        with mock.patch("tools.run_eval.subprocess.run", side_effect=_fake_run), mock.patch("time.sleep", return_value=None):
            result = run_smoke(plan, self.base_cfg)

        self.assertTrue(result.metrics_path.exists())
        self.assertEqual(result.summary["status"], "ok")
        self.assertAlmostEqual(result.summary["metrics"]["recall_at_10"], 0.42)

    def test_run_smoke_retry_then_success(self) -> None:
        plan = ExperimentPlan(
            dataset="fiqa_para_50k",
            sample_size=50,
            search_space={"top_k": [10]},
        )

        call_state = {"count": 0}

        def _side_effect(cmd, check, timeout, env):  # type: ignore[override]
            call_state["count"] += 1
            if call_state["count"] == 1:
                raise subprocess.CalledProcessError(returncode=1, cmd=cmd)
            metrics_path = Path(env["RUNS_DIR"]) / env["JOB_ID"] / "metrics.json"
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            with metrics_path.open("w", encoding="utf-8") as fp:
                json.dump({"job_id": env["JOB_ID"], "status": "ok", "metrics": {}}, fp)
            return subprocess.CompletedProcess(cmd, 0)

        with mock.patch("tools.run_eval.subprocess.run", side_effect=_side_effect), mock.patch("time.sleep", return_value=None):
            result = run_smoke(plan, self.base_cfg)

        self.assertEqual(call_state["count"], 2)
        self.assertEqual(result.summary["status"], "ok")

    def test_run_smoke_disallowed_host(self) -> None:
        plan = ExperimentPlan(
            dataset="fiqa_para_50k",
            sample_size=50,
            search_space={"top_k": [10]},
        )
        cfg = dict(self.base_cfg)
        cfg["base_url"] = "http://example.com:8000"
        with self.assertRaises(RunEvalError):
            run_smoke(plan, cfg)

    def test_run_grid_task_success(self) -> None:
        params = {
            "dataset": "fiqa_para_50k",
            "sample": 80,
            "top_k": 20,
            "mmr": True,
            "mmr_lambda": 0.2,
            "ef_search": 64,
            "concurrency": 2,
        }
        cfg = dict(self.base_cfg)
        cfg["grid"] = {
            "sample": 80,
            "concurrency": 2,
            "timeout_s": 5,
            "max_retries": 1,
            "backoff_s": 0.1,
            "rate_limit_per_sec": 10,
        }

        def _fake_run(cmd, check, timeout, env):  # type: ignore[override]
            metrics_path = Path(env["RUNS_DIR"]) / env["JOB_ID"] / "metrics.json"
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"job_id": env["JOB_ID"], "status": "ok", "metrics": {"recall_at_10": 0.55}}
            with metrics_path.open("w", encoding="utf-8") as fp:
                json.dump(payload, fp)
            return subprocess.CompletedProcess(cmd, 0)

        with mock.patch("tools.run_eval.subprocess.run", side_effect=_fake_run):
            result = run_grid_task(params, cfg)

        self.assertTrue(result.metrics_path.exists())
        self.assertEqual(result.summary["status"], "ok")


if __name__ == "__main__":
    unittest.main()

