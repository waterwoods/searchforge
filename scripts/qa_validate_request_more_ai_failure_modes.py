#!/usr/bin/env python3
"""Cloud QA live failure-mode proof for AI Request More drafting.

Flips Request More assistant kill switches on the QA Cloud Run service only,
proves the broker is never blocked when the model path is broken or off, then
restores the QA posture. Never touches Production.

Usage:
  set -a && source .env.cloudrun.qa && set +a
  PYTHONPATH=. python3 scripts/qa_validate_request_more_ai_failure_modes.py
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.qa_validate_request_more_ai_drafting import (  # noqa: E402
    ACCIDENT_FACTS,
    QA_BASE,
    VEHICLE_FACTS,
    Checks,
    Client,
    _requestable,
    assist,
    confirm_fact,
    create_case,
)

QA_SERVICE = "fiqa-api-qa"
QA_REGION = "us-west1"
QA_PROJECT = "optimal-disk-472305-e2"


def _gcloud_env(update: dict[str, str] | None = None, remove: list[str] | None = None) -> str:
    cmd = [
        "gcloud", "run", "services", "update", QA_SERVICE,
        "--region", QA_REGION, "--project", QA_PROJECT, "--quiet",
        "--format", "value(status.latestReadyRevisionName)",
    ]
    if update:
        cmd += ["--update-env-vars", ",".join(f"{k}={v}" for k, v in update.items())]
    if remove:
        cmd += ["--remove-env-vars", ",".join(remove)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"gcloud update failed: {proc.stderr[-600:]}")
    return proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""


def _flags(client: Client) -> dict[str, Any]:
    manifest = client.get("/api/inbox/support/deployment-manifest", support=True)
    return manifest.get("request_more_assistant") or {}


def _wait_for_flag(client: Client, key: str, expected: Any, timeout_s: int = 120) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _flags(client).get(key) == expected:
            return True
        time.sleep(5)
    return False


def _gap_case(client: Client, title: str) -> str:
    """Synthetic case whose deterministic missing set is VIN only."""
    case_id, ver, _ = create_case(
        client, title=title,
        known_facts={**VEHICLE_FACTS, **ACCIDENT_FACTS, "policy_number": "QA-SYNTH-POLICY"},
    )
    checklist: list[dict] = []
    for field in (
        "vehicle_information", "policy_or_insurance_card", "accident_description",
        "accident_datetime", "accident_location", "injury_status",
    ):
        ver, checklist = confirm_fact(client, case_id, ver, field)
    assert _requestable(checklist) == ["vin"], _requestable(checklist)
    return case_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("QA_BASE_URL", QA_BASE))
    parser.add_argument("--out", default="/tmp/qa_request_more_ai_failure_modes.json")
    args = parser.parse_args()

    intake_key = (os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()
    support_key = (os.environ.get("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip()
    if not intake_key or not support_key:
        print("UNIFIED_INTAKE_INTAKE_API_KEY and UNIFIED_INTAKE_SUPPORT_API_KEY required", file=sys.stderr)
        return 2

    client = Client(args.base_url, intake_key, support_key)
    checks = Checks()
    evidence: dict[str, Any] = {"base_url": args.base_url, "scenarios": {}}
    baseline_flags = _flags(client)
    print(f"Baseline QA flags: {json.dumps(baseline_flags)}")

    case_id = _gap_case(client, "AI RM QA — failure-mode VIN gap")
    print(f"Synthetic VIN-gap case: {case_id}")

    try:
        # --- Scenario 1: provider error (model name that cannot resolve) ---
        print("\nSCENARIO 1 — real provider failure")
        _gcloud_env(update={"REQUEST_MORE_ASSISTANT_MODEL": "qa-nonexistent-model-fallback-probe"})
        checks.expect("provider-error: QA revision picked up the broken model",
                      _wait_for_flag(client, "llm_drafting_enabled", True))
        broken, latency = assist(client, case_id)
        evidence["scenarios"]["provider_error"] = {"draft": broken, "client_latency_ms": latency}
        print(json.dumps(broken, ensure_ascii=False, indent=2)[:700])
        checks.expect("provider-error: request still succeeds", broken.get("ok") is True)
        checks.expect("provider-error: fell back to office template",
                      broken.get("used_fallback") is True
                      and broken.get("authority") == "office_template",
                      broken.get("fallback_reason"))
        checks.expect("provider-error: reason is a model failure",
                      str(broken.get("fallback_reason") or "").startswith(
                          ("provider_error", "llm_error", "timeout")),
                      broken.get("fallback_reason"))
        checks.expect("provider-error: deterministic missing set intact",
                      [i["field_key"] for i in broken.get("items") or []] == ["vin"])
        checks.expect("provider-error: broker still has sendable Chinese copy",
                      "VIN" in str(broken.get("draft_text") or "").upper())
        checks.expect("provider-error: broker is not blocked",
                      broken.get("drafting_available") is True)

        # --- Scenario 2: assistant kill switch off ---
        print("\nSCENARIO 2 — assistant kill switch OFF")
        _gcloud_env(update={"REQUEST_MORE_ASSISTANT_ENABLED": "0"},
                    remove=["REQUEST_MORE_ASSISTANT_MODEL"])
        checks.expect("kill-switch: QA reports assistant disabled",
                      _wait_for_flag(client, "assistant_enabled", False))
        disabled, _ = assist(client, case_id)
        evidence["scenarios"]["assistant_disabled"] = {"draft": disabled}
        print(json.dumps(disabled, ensure_ascii=False, indent=2)[:700])
        checks.expect("kill-switch: deterministic template returned",
                      disabled.get("authority") == "office_template"
                      and disabled.get("draft_used_ai") is False)
        checks.expect("kill-switch: reason assistant_disabled",
                      disabled.get("fallback_reason") == "assistant_disabled",
                      disabled.get("fallback_reason"))
        checks.expect("kill-switch: Request More still usable",
                      [i["field_key"] for i in disabled.get("items") or []] == ["vin"]
                      and "VIN" in str(disabled.get("draft_text") or "").upper())

        # --- Scenario 3: LLM off, assistant on ---
        print("\nSCENARIO 3 — assistant ON, LLM OFF")
        _gcloud_env(update={"REQUEST_MORE_ASSISTANT_ENABLED": "1", "REQUEST_MORE_ASSISTANT_LLM": "0"})
        checks.expect("llm-off: QA reports llm drafting disabled",
                      _wait_for_flag(client, "llm_drafting_enabled", False))
        llm_off, _ = assist(client, case_id)
        evidence["scenarios"]["llm_disabled"] = {"draft": llm_off}
        checks.expect("llm-off: template path, reason llm_disabled",
                      llm_off.get("fallback_reason") == "llm_disabled"
                      and llm_off.get("authority") == "office_template",
                      llm_off.get("fallback_reason"))
        checks.expect("llm-off: broker still gets sendable copy",
                      "VIN" in str(llm_off.get("draft_text") or "").upper())
    finally:
        print("\nRESTORE — returning QA to validated posture")
        _gcloud_env(
            update={"REQUEST_MORE_ASSISTANT_ENABLED": "1", "REQUEST_MORE_ASSISTANT_LLM": "1"},
            remove=["REQUEST_MORE_ASSISTANT_MODEL"],
        )
        restored = _wait_for_flag(client, "llm_drafting_enabled", True)
        final_flags = _flags(client)
        evidence["restored_flags"] = final_flags
        checks.expect("restore: QA back on the real LLM path", restored, json.dumps(final_flags))

    healthy, _ = assist(client, case_id)
    evidence["scenarios"]["after_restore"] = {"draft": healthy}
    checks.expect("restore: real AI drafting works again",
                  healthy.get("draft_used_ai") is True and healthy.get("used_fallback") is False,
                  healthy.get("fallback_reason"))

    evidence["checks"] = checks.rows
    evidence["pass_count"] = len([r for r in checks.rows if r["pass"]])
    evidence["fail_count"] = len(checks.failed)
    Path(args.out).write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nPASS {evidence['pass_count']} / FAIL {evidence['fail_count']}")
    print(f"Evidence: {args.out}")
    for row in checks.failed:
        print(f"  FAILED: {row['check']} — {row['detail']}")
    return 1 if checks.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
