#!/usr/bin/env python3
"""P19H-3i — Claim task dashboard + always-return H5 entry deploy smoke."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

SMOKE_EXT_PREFIX = "wm_p19h3i_smoke_"
SUBMIT_INTENT = "p19h3i-smoke-0000-4000-8000-000000000001"
STATUS_COMMANDS = ("进度", "补资料", "链接", "事故资料", "继续填写", "上传照片")


def _utc_suffix() -> str:
    return datetime.now(timezone.utc).strftime("3i_smoke_%H%M%S")


def _evidence_path(suffix: str) -> Path:
    return REPO / "docs" / "evidence" / f"p19h3i_claim_task_dashboard_smoke_{suffix}.json"


def _load_cloudrun_env() -> None:
    env_file = REPO / ".env.cloudrun"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _ensure_h5_token_secret_for_deploy() -> None:
    if (os.getenv("H5_TASK_TOKEN_SECRET") or "").strip():
        return
    project = (os.getenv("PROJECT_ID") or "optimal-disk-472305-e2").strip()
    secret_name = (os.getenv("CLOUD_RUN_SECRET_H5_TASK_TOKEN") or "fiqa-h5-task-token-secret").strip()
    try:
        import subprocess

        proc = subprocess.run(
            [
                "gcloud",
                "secrets",
                "versions",
                "access",
                "latest",
                f"--secret={secret_name}",
                f"--project={project}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            os.environ["H5_TASK_TOKEN_SECRET"] = proc.stdout.strip()
    except Exception:
        pass


def _api_headers() -> dict[str, str]:
    key = (os.getenv("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()
    return {"X-Unified-Intake-Api-Key": key} if key else {}


def _http_json(method: str, base_url: str, path: str, body: dict | None = None) -> tuple[int, dict[str, Any]]:
    url = f"{base_url.rstrip('/')}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", **_api_headers()}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"detail": raw}
        return exc.code, payload


def _triage_stub() -> dict[str, Any]:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Collect claim basics via H5.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "claim_phase": "accident_basics_in_progress",
    }


def _seed_claim_case(ext: str) -> tuple[str, str]:
    from services.fiqa_api.inbox_triage.case_store import bind_case_channel_identity, save_case, update_case_workbench_flags
    from services.fiqa_api.inbox_triage.h5_task_token import issue_h5_intake_form_token
    from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

    saved = save_case("我要理赔", _triage_stub(), service_lane=SERVICE_LANE_CLAIM)
    case_id = str(saved.get("case_id") or "")
    bind_case_channel_identity(case_id, wecom_external_userid=ext)
    update_case_workbench_flags(case_id, is_test=True)
    token = issue_h5_intake_form_token(case_id=case_id, external_userid=ext)
    return case_id, token


def _patch_and_submit(base_url: str, token: str) -> dict[str, Any]:
    steps = [
        ("injury", {"anyone_injured": "no"}),
        ("time_location", {"accident_datetime": "今天上午10点", "accident_location": "Irvine Blvd"}),
        ("story", {"accident_description": "我停在红灯前，后车追尾撞上我的车。"}),
        ("vehicle_other_party", {"own_vehicle_info": "2020 Toyota Camry"}),
    ]
    checks: dict[str, Any] = {}
    for step, fields in steps:
        status, body = _http_json("PATCH", base_url, f"/api/h5/tasks/{token}/fields", {"step": step, "fields": fields})
        if status != 200:
            checks["patch_failed"] = {"step": step, "status": status, "body": body}
            return checks
    checks["patch_all_fields"] = True

    status, submit_body = _http_json(
        "POST",
        base_url,
        f"/api/h5/tasks/{token}/submit",
        {"submit_intent_id": SUBMIT_INTENT},
    )
    checks["submit_status"] = status
    checks["submitted"] = submit_body.get("submitted") is True
    checks["broker_done_false"] = submit_body.get("phase") != "broker_done"
    checks["completion_summary_present"] = bool(submit_body.get("completion_summary"))
    return checks


def _dashboard_checks(body: dict[str, Any], *, submitted: bool) -> dict[str, Any]:
    dashboard = body.get("dashboard_summary") or {}
    return {
        "has_dashboard_summary": bool(dashboard),
        "dashboard_title": dashboard.get("title") == "我的事故资料",
        "has_status": bool(dashboard.get("status")),
        "has_received": isinstance(dashboard.get("received"), list),
        "has_missing": isinstance(dashboard.get("missing"), list),
        "has_next_action": bool(dashboard.get("next_action")),
        "has_primary_cta": bool(dashboard.get("primary_cta")),
        "submitted_supplement_allowed": dashboard.get("submitted_supplement_allowed") is True if submitted else True,
        "submitted_status_label": dashboard.get("status") == "已提交给陈总审核" if submitted else dashboard.get("status") == "资料收集中",
    }


def _status_command_checks(case_id: str, ext: str, *, suffix: str) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
    from services.fiqa_api.inbox_triage.h5_task_link import mint_h5_claim_intake_form_link
    from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message, ingest_claim_status_request
    from services.fiqa_api.wecom.intent import classify_wecom_intent
    from services.fiqa_api.wecom.normalize import normalize_text_message

    before_count = len(list_all_cases_for_read())
    h5_url = mint_h5_claim_intake_form_link(case_id=case_id, external_userid=ext)
    results: dict[str, Any] = {"expected_h5_url": h5_url}

    for idx, text in enumerate(STATUS_COMMANDS):
        norm = normalize_text_message(
            {
                "msgid": f"m_3i_status_{suffix}_{idx}",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": text},
            }
        )
        result = ingest_claim_status_request(norm, classify_wecom_intent(text))
        reply = result.get("reply_text") or ""
        results[f"status_{text}_outcome"] = result.get("active_case_outcome")
        results[f"status_{text}_has_continue_supplement"] = "继续补充事故资料" in reply
        results[f"status_{text}_has_h5_link"] = "/task/claim/" in reply
        results[f"status_{text}_no_new_case"] = result.get("case_created") is False

    after_count = len(list_all_cases_for_read())
    results["status_no_duplicate_cases"] = after_count == before_count

    sup_norm = normalize_text_message(
        {
            "msgid": f"m_3i_sup_ins_{suffix}",
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "text": {"content": "对方保险是 State Farm"},
        }
    )
    sup_result = ingest_claim_basics_message(sup_norm, classify_wecom_intent("对方保险是 State Farm"))
    sup_reply = sup_result.get("reply_text") or ""
    results["supplement_outcome"] = sup_result.get("active_case_outcome")
    results["supplement_has_h5_link"] = "/task/claim/" in sup_reply
    results["supplement_ack_recorded"] = "已记录到您当前的事故记录里" in sup_reply
    results["supplement_customer_text_note"] = "客户文字补充" in sup_reply

    add_norm = normalize_text_message(
        {
            "msgid": f"m_3i_add_car_{suffix}",
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "text": {"content": "我要加车"},
        }
    )
    add_result = ingest_claim_basics_message(add_norm, classify_wecom_intent("我要加车"))
    results["add_car_intent"] = classify_wecom_intent("我要加车").intent
    results["add_car_not_supplement"] = add_result.get("active_case_outcome") != "claim_supplement_appended"

    return results


def _workbench_provenance_checks(case_id: str) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
    from services.fiqa_api.inbox_triage.claim_workbench_display import enrich_claim_for_workbench

    case = get_case_for_read(case_id) or {}
    enriched = enrich_claim_for_workbench(case)
    brief = enriched.get("claim_case_brief") or {}
    key_facts = brief.get("key_facts") or {}
    timeline = enriched.get("claim_timeline") or []
    provenance = case.get("known_fact_provenance") or {}

    return {
        "workbench_visible": enriched.get("workbench_visible") is True,
        "other_party_info_label": "客户文字补充" in str(key_facts.get("other_party_info") or ""),
        "timeline_has_state_farm": any("State Farm" in str(e.get("text") or "") for e in timeline),
        "provenance_wecom_customer_text": provenance.get("other_party_info", {}).get("source") == "wecom_customer_text",
        "broker_done_false": enriched.get("workflow_phase") != "broker_done",
    }


def run_smoke(base_url: str, *, use_qa_db: bool) -> dict[str, Any]:
    if use_qa_db:
        _load_cloudrun_env()
        _ensure_h5_token_secret_for_deploy()
        os.environ["ENV"] = "prod"
        from scripts.demo_db_resolve import apply_qa_postgres_env

        apply_qa_postgres_env(for_write=True)

    suffix = _utc_suffix()
    ext = f"{SMOKE_EXT_PREFIX}{suffix}"
    case_id, token = _seed_claim_case(ext)

    status_pre, pre_body = _http_json("GET", base_url, f"/api/h5/tasks/{token}/intake")
    pre_dashboard = _dashboard_checks(pre_body, submitted=False)
    pre_dashboard["get_intake_status"] = status_pre == 200

    submit_checks = _patch_and_submit(base_url, token)

    status_post, post_body = _http_json("GET", base_url, f"/api/h5/tasks/{token}/intake")
    post_dashboard = _dashboard_checks(post_body, submitted=True)
    post_dashboard["get_intake_after_submit"] = status_post == 200

    wecom_checks = _status_command_checks(case_id, ext, suffix=suffix)
    wb_checks = _workbench_provenance_checks(case_id)

    checks = {
        **pre_dashboard,
        **submit_checks,
        **post_dashboard,
        **wecom_checks,
        **wb_checks,
    }

    required = [
        "get_intake_status",
        "has_dashboard_summary",
        "dashboard_title",
        "patch_all_fields",
        "submitted",
        "get_intake_after_submit",
        "submitted_supplement_allowed",
        "submitted_status_label",
        "status_no_duplicate_cases",
        "supplement_has_h5_link",
        "supplement_ack_recorded",
        "workbench_visible",
        "timeline_has_state_farm",
        "broker_done_false",
    ]
    for text in STATUS_COMMANDS:
        required.extend(
            [
                f"status_{text}_has_continue_supplement",
                f"status_{text}_has_h5_link",
            ]
        )

    passed = all(checks.get(k) for k in required if k in checks) and (
        checks.get("other_party_info_label") or checks.get("timeline_has_state_farm")
    )

    return {
        "mode": "http",
        "base_url": base_url,
        "case_id": case_id,
        "external_userid": ext,
        "token_prefix": token[:24] + "...",
        "checks": checks,
        "pass": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="P19H-3i Claim task dashboard deploy smoke")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--use-qa-db", action="store_true")
    args = parser.parse_args()

    suffix = _utc_suffix()
    report = {
        "script": "p19h3i_claim_task_dashboard_smoke.py",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "suffix": suffix,
        "result": run_smoke(args.base_url, use_qa_db=args.use_qa_db),
    }
    out_path = _evidence_path(suffix)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nEvidence: {out_path}")
    return 0 if report["result"].get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
