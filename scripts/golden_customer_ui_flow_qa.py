#!/usr/bin/env python3
"""P26H-UI QA mode — ephemeral fixture + Mini Program bootstrap/render contracts.

Uses the authorized fixture runner for a clean case, then validates Task Home
destination contracts and the Empty Page Gate (blank insurance regression).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.p26h_fixture_client import FixtureClientError, open_fixture_client  # noqa: E402


def _fail(step: str, **fields: Any) -> int:
    print("FAIL")
    print(f"Step: {step}")
    for key, value in fields.items():
        print(f"{key}: {value}")
    return 1


def main() -> int:
    harness_run_id = ""
    cleanup_result = "SKIPPED"
    client = None
    try:
        try:
            client, transport = open_fixture_client()
        except FixtureClientError as exc:
            return _fail(
                "Fixture preflight",
                **{
                    "Task": "fixture_transport",
                    "Source": "system_default",
                    "Expected": "configured QA fixture transport",
                    "Actual": str(exc),
                    "Owning layer": exc.layer,
                    "Smallest probable repair area": "Fixture Runner env / deploy",
                    "Detail": exc.detail,
                    "Cleanup": cleanup_result,
                },
            )

        status = client.status()
        if not status.get("enabled"):
            return _fail(
                "Fixture preflight",
                **{
                    "Task": "fixture_enabled",
                    "Source": "system_default",
                    "Expected": "enabled=true",
                    "Actual": status,
                    "Owning layer": "Fixture Runner",
                    "Cleanup": cleanup_result,
                    "Detail": transport.notes,
                },
            )

        run = client.create_run()
        harness_run_id = str(run.get("harness_run_id") or "")
        fresh = client.create_case(harness_run_id, suffix="ui_fresh")
        case_id = str(fresh.get("case_id") or "")
        inspect = client.inspect(harness_run_id, case_id)
        follow = client.create_case(harness_run_id, suffix="ui_follow")
        case_f = str(follow.get("case_id") or "")
        client.broker_followup(harness_run_id, case_f)
        inspect_f = client.inspect(harness_run_id, case_f)

        fixture = {
            "harness_run_id": harness_run_id,
            "fresh": {
                "case_id": case_id,
                "constitution_projection": inspect.get("constitution_projection"),
                "claim_phase": inspect.get("claim_phase"),
            },
            "broker_followup": {
                "case_id": case_f,
                "constitution_projection": inspect_f.get("constitution_projection"),
            },
            # Permanent blank-page regression inputs (system_default insurance).
            "blank_page_regression": {
                "loading": False,
                "waitingForBroker": False,
                "inputMode": "evidence",
                "nextAction": None,
                "nextActionTitle": "",
                "showWorkSurface": True,
                "showFooterCta": True,
                "pageError": None,
            },
            "legacy_blank_shape": {
                "loading": False,
                "waitingForBroker": False,
                "inputMode": "evidence",
                "nextAction": None,
                "nextActionTitle": "",
                # intentionally omit showWorkSurface — legacy WXML nextAction-only
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(fixture, tmp, ensure_ascii=False)
            fixture_path = tmp.name

        env = os.environ.copy()
        env["P26H_UI_FIXTURE_JSON"] = fixture_path
        node = subprocess.run(
            ["node", "--import", "tsx", "--test", "tests/goldenUiJourneyQa.test.ts"],
            cwd=str(ROOT / "miniapp"),
            env=env,
            capture_output=True,
            text=True,
        )
        print(node.stdout, end="")
        if node.stderr:
            print(node.stderr, end="", file=sys.stderr)
        if node.returncode != 0:
            # Still attempt insurance upload state update via API contract
            cleanup_result = "PENDING"
            raise RuntimeError("ui_journey_node_failed")

        # Complete insurance through real QA fixture evidence contract; re-inspect Task Home.
        client.register_evidence(harness_run_id, case_id, "policy_or_insurance_card")
        after = client.inspect(harness_run_id, case_id)
        tasks = {
            str(t.get("task_id") or ""): t
            for t in ((after.get("constitution_projection") or {}).get("customer") or {}).get(
                "tasks"
            )
            or []
            if isinstance(t, dict)
        }
        if (tasks.get("insurance_card") or {}).get("state") != "completed":
            return _fail(
                "Insurance Task Home update",
                **{
                    "harness_run_id": harness_run_id,
                    "case_id": case_id,
                    "Task": "insurance_card",
                    "Source": "system_default",
                    "Expected": "completed after fixture evidence",
                    "Actual": (tasks.get("insurance_card") or {}).get("state"),
                    "Owning layer": "Upload State Machine",
                    "Cleanup": cleanup_result,
                },
            )

        print("PASS")
        print(f"harness_run_id: {harness_run_id}")
        print(f"case_id: {case_id}")
        print("Golden UI Journey QA: Task Home → insurance/photos/story/broker + blank-page regression")
        return 0
    except Exception as exc:  # noqa: BLE001
        code = _fail(
            "QA UI harness",
            **{
                "harness_run_id": harness_run_id or "n/a",
                "Task": "ui_qa",
                "Source": "system_default",
                "Expected": "no exception",
                "Actual": type(exc).__name__,
                "Owning layer": "Page Bootstrap",
                "Detail": str(exc)[:400],
                "Cleanup": cleanup_result,
            },
        )
        return code
    finally:
        if client is not None and harness_run_id:
            try:
                cleaned = client.cleanup(harness_run_id)
                cleanup_result = str(
                    cleaned.get("cleanup") or ("PASS" if cleaned.get("ok") else "FAIL")
                )
                print(f"Cleanup: {cleanup_result}")
            except Exception as cleanup_exc:  # noqa: BLE001
                print(f"Cleanup: FAIL:{type(cleanup_exc).__name__}")


if __name__ == "__main__":
    raise SystemExit(main())
