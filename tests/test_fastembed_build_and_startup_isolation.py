"""FastEmbed build/startup isolation checks for paid-pilot intake deploys."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE_CLOUDRUN = REPO_ROOT / "services" / "fiqa_api" / "Dockerfile.cloudrun"


def _run_python(code: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _load_last_json_line(stdout: str) -> dict:
    for line in reversed((stdout or "").splitlines()):
        line = line.strip()
        if not line:
            continue
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise AssertionError(f"Could not find JSON payload in subprocess stdout:\n{stdout}")


def test_cloudrun_dockerfile_has_no_fastembed_predownload_step():
    text = DOCKERFILE_CLOUDRUN.read_text(encoding="utf-8")
    assert "Pre-downloading fastembed model" not in text
    assert "from fastembed import TextEmbedding" not in text


def test_claim_and_upload_imports_do_not_load_fastembed():
    code = """
import importlib
import json
import sys

importlib.import_module("services.fiqa_api.inbox_triage.h5_task_upload")
importlib.import_module("services.fiqa_api.routes.h5_task_upload")
importlib.import_module("services.fiqa_api.routes.inbox_triage")

print(json.dumps({"fastembed_loaded": "fastembed" in sys.modules}))
"""
    result = _run_python(code)
    assert result.returncode == 0, result.stderr
    payload = _load_last_json_line(result.stdout)
    assert payload["fastembed_loaded"] is False


def test_intake_core_startup_skips_embedding_warmup_and_readyz_stays_green():
    code = """
import json
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

tmp = Path(tempfile.mkdtemp(prefix="p20-fastembed-"))
cases = tmp / "cases.json"
cases.write_text("[]", encoding="utf-8")

os.environ["UNIFIED_INTAKE_PRODUCT_ONLY"] = "1"
os.environ["UNIFIED_INTAKE_INTAKE_CORE_READINESS"] = "1"
os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(cases)
os.environ.pop("DEMO_MODE", None)

import services.fiqa_api.clients as clients

calls = {"warmup": 0}

def _fake_start_embedding_warmup():
    calls["warmup"] += 1

clients.start_embedding_warmup = _fake_start_embedding_warmup

import services.fiqa_api.app_main as app_main

with TestClient(app_main.app) as client:
    live = client.get("/health/live")
    ready = client.get("/readyz")

print(
    json.dumps(
        {
            "warmup_calls": calls["warmup"],
            "live_code": live.status_code,
            "ready_code": ready.status_code,
            "readiness_mode": ready.json().get("readiness_mode"),
            "intake_path_ready": ready.json().get("intake_path_ready"),
        }
    )
)
"""
    result = _run_python(code)
    assert result.returncode == 0, result.stderr
    payload = _load_last_json_line(result.stdout)
    assert payload["warmup_calls"] == 0
    assert payload["live_code"] == 200
    assert payload["ready_code"] == 200
    assert payload["readiness_mode"] == "intake_core"
    assert payload["intake_path_ready"] is True
