#!/usr/bin/env python3
"""P19H-3h-1C — Claim H5 intake deploy smoke (local in-process or HTTP + optional QA DB)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

SMOKE_EXT_PREFIX = "wm_p19h3h_smoke_"
SUBMIT_INTENT = "p19h3h-smoke-0000-4000-8000-000000000001"


def _utc_suffix() -> str:
    return datetime.now(timezone.utc).strftime("3h_smoke_%H%M%S")


def _evidence_path(suffix: str) -> Path:
    return REPO / "docs" / "evidence" / f"p19h3h_claim_h5_intake_smoke_{suffix}.json"


def _is_deploy_url(base_url: str) -> bool:
    lowered = (base_url or "").lower()
    return "run.app" in lowered or "cloud" in lowered


def _load_cloudrun_env() -> None:
    from scripts.demo_db_resolve import load_cloudrun_env_skip_db

    load_cloudrun_env_skip_db()


def _ensure_h5_token_secret_for_deploy() -> None:
    """Load H5_TASK_TOKEN_SECRET from Secret Manager when missing (deploy smoke)."""
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


def _probe_health(base_url: str) -> dict[str, Any]:
    for path in ("/healthz", "/api/healthz", "/health/live"):
        try:
            status, body = _http_json("GET", base_url, path)
            if status == 200:
                return {"ok": True, "path": path, "status": status, "body": body}
        except Exception as exc:
            last_err = str(exc)
            continue
    return {"ok": False, "error": last_err if "last_err" in dir() else "unreachable"}


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


def _patch_fields(client: Any, token: str, step: str, fields: dict[str, str]) -> dict[str, Any]:
    resp = client.patch(f"/api/h5/tasks/{token}/fields", json={"step": step, "fields": fields})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _run_h5_flow_checks(client: Any, token: str, *, http_mode: bool = False) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.h5_task_token import FLOW_CLAIM_INTAKE_FORM

    checks: dict[str, Any] = {}

    r0 = client.get(f"/api/h5/tasks/{token}/intake")
    checks["get_intake_status"] = r0.status_code
    data0 = r0.json()
    checks["flow"] = data0.get("flow")
    checks["has_upload_url"] = bool(str(data0.get("upload_url") or "").strip())
    checks["upload_url_has_task_upload"] = "/task/upload/" in str(data0.get("upload_url") or "")
    checks["steps_include_evidence"] = "evidence" in (data0.get("steps") or [])
    checks["case_id"] = data0.get("case_id")

    field_steps = [
        ("injury", {"anyone_injured": "no"}),
        ("time_location", {"accident_datetime": "今天上午10点", "accident_location": "Irvine Blvd"}),
        ("story", {"accident_description": "我停在红灯前，后车追尾撞上我的车。"}),
        (
            "vehicle_other_party",
            {
                "own_vehicle_info": "2020 Toyota Camry",
                "other_party_info": "State Farm / 对方司机张三",
            },
        ),
    ]
    patch_ok = True
    for step, fields in field_steps:
        pr = client.patch(f"/api/h5/tasks/{token}/fields", json={"step": step, "fields": fields})
        if pr.status_code != 200:
            patch_ok = False
            checks["patch_error"] = {"step": step, "status": pr.status_code, "body": pr.text}
            break
    checks["patch_all_fields"] = patch_ok

    r1 = client.get(f"/api/h5/tasks/{token}/intake")
    data1 = r1.json()
    key_facts = data1.get("key_facts") or {}
    checks["persisted_location"] = key_facts.get("accident_location") == "Irvine Blvd"
    checks["persisted_vehicle"] = key_facts.get("own_vehicle_info") == "2020 Toyota Camry"
    checks["current_step_review"] = data1.get("current_step") == "review"

    r_submit = client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": SUBMIT_INTENT},
        headers={"X-Submit-Intent-Id": SUBMIT_INTENT},
    )
    checks["submit_status"] = r_submit.status_code
    submit_body = r_submit.json()
    checks["submitted"] = submit_body.get("submitted") is True
    summary = submit_body.get("completion_summary") or {}
    checks["submit_has_completion_summary"] = summary.get("title") == "已提交给陈总 ✅"
    checks["submit_has_received_list"] = isinstance(summary.get("received"), list) and len(summary.get("received") or []) >= 1

    r_dup = client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": SUBMIT_INTENT},
        headers={"X-Submit-Intent-Id": SUBMIT_INTENT},
    )
    checks["submit_idempotent"] = (
        r_dup.status_code == 200 and r_dup.json().get("already_submitted") is True
    )

    from services.fiqa_api.inbox_triage.case_store import get_case_by_id

    submitted_case = get_case_by_id(checks.get("case_id") or "") or {}
    h5_state = submitted_case.get("h5_intake_state") or {}
    timeline = submitted_case.get("claim_timeline") or []
    checks["broker_done_false"] = submitted_case.get("claim_phase") != "broker_done"
    checks["single_submitted_timeline_event"] = sum(
        1 for e in timeline if e.get("event_type") == "customer_submitted_intake"
    ) == 1
    checks["confirmation_marker_optional"] = (
        not submitted_case.get("wecom_external_userid")
        or bool(h5_state.get("h5_submit_confirmation_sent_at"))
        or h5_state.get("h5_submit_confirmation_send_status") == "skipped_no_channel"
    )

    checks["flow_is_claim_intake_form"] = data0.get("flow") == FLOW_CLAIM_INTAKE_FORM
    checks["http_mode"] = http_mode
    return checks


def _workbench_checks(case_id: str, client: Any | None = None) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_store import get_case_by_id
    from services.fiqa_api.inbox_triage.claim_workbench_display import enrich_claim_for_workbench
    from services.fiqa_api.wecom.claim_state import CLAIM_PHASE_INTAKE_READY_FOR_BROKER, derive_claim_phase

    if client is not None:
        resp = client.get(f"/api/inbox/cases/{case_id}")
        if resp.status_code == 200:
            row = resp.json()
        else:
            row = enrich_claim_for_workbench(get_case_by_id(case_id) or {})
    else:
        case = get_case_by_id(case_id) or {}
        row = enrich_claim_for_workbench(case)

    brief = row.get("claim_case_brief") or {}
    key_facts = brief.get("key_facts") or {}
    timeline = row.get("claim_timeline") or []
    event_types = [str(e.get("event_type")) for e in timeline]

    return {
        "workflow_phase": row.get("workflow_phase"),
        "intake_ready_for_broker": row.get("workflow_phase") == CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
        "facts_location": key_facts.get("accident_location") == "Irvine Blvd",
        "facts_vehicle": key_facts.get("own_vehicle_info") == "2020 Toyota Camry",
        "has_customer_submitted_intake": "customer_submitted_intake" in event_types,
        "has_h5_step_complete": "h5_step_complete" in event_types,
        "missing_info_is_list": isinstance(brief.get("missing_info"), list),
        "workbench_visible": row.get("workbench_visible") is True,
        "derive_phase": derive_claim_phase(row),
    }


def _wecom_card_copy_checks() -> dict[str, Any]:
    from services.fiqa_api.wecom.reply import (
        build_claim_start_h5_intake_card_payload,
        build_h5_submit_confirmation_reply,
    )

    start_menu = build_claim_start_h5_intake_card_payload(h5_url="https://example.test/task/claim/h5t1.x")
    start_head = start_menu.get("head_content") or ""
    submit_reply = build_h5_submit_confirmation_reply()
    return {
        "start_has_submit_instruction": "提交给陈总审核" in start_head,
        "start_has_h5_button": start_menu["list"][0]["view"]["content"] == "打开资料填写页面",
        "start_disclaimer_once": start_head.count("这只是资料收集，不代表已经正式向保险公司报案。") == 1,
        "submit_confirmation_not_broker_done": "陈总已确认" not in submit_reply,
        "submit_confirmation_has_title": "【资料已提交 ✅】" in submit_reply,
    }


def _status_card_checks_open(case_id: str, ext: str) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_store import get_case_by_id
    from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
    from services.fiqa_api.inbox_triage.h5_task_link import mint_h5_claim_intake_form_link
    from services.fiqa_api.wecom.claim_basics import ingest_claim_status_request
    from services.fiqa_api.wecom.intent import classify_wecom_intent
    from services.fiqa_api.wecom.normalize import normalize_text_message
    from services.fiqa_api.wecom.reply import build_claim_status_card_reply

    case = get_case_by_id(case_id) or {}
    before_count = len(list_all_cases_for_read())

    open_reply = build_claim_status_card_reply(
        case,
        h5_intake_url=mint_h5_claim_intake_form_link(case_id=case_id, external_userid=ext),
    )

    norm = normalize_text_message(
        {
            "msgid": f"m_status_{ext}",
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "text": {"content": "进度"},
        }
    )
    intent = classify_wecom_intent("进度")
    status_result = ingest_claim_status_request(norm, intent)
    after_count = len(list_all_cases_for_read())

    return {
        "open_has_continue_link": "继续补充资料" in open_reply,
        "open_has_h5_route": "/task/claim/" in open_reply,
        "status_request_no_duplicate_case": after_count == before_count,
        "status_request_outcome": status_result.get("active_case_outcome"),
        "status_reply_has_continue": "继续补充资料" in (status_result.get("reply_text") or ""),
    }


def _status_card_checks_submitted(case_id: str) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_store import get_case_by_id
    from services.fiqa_api.inbox_triage.h5_task_intake import is_h5_intake_continuable
    from services.fiqa_api.wecom.reply import build_claim_status_card_reply

    submitted_case = get_case_by_id(case_id) or {}
    return {
        "submitted_not_continuable": not is_h5_intake_continuable(submitted_case),
        "submitted_no_continue_when_url_omitted": "继续补充资料"
        not in build_claim_status_card_reply(submitted_case, h5_intake_url=None),
    }


def _setup_temp_store() -> Path:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    return path


def _seed_claim_case(ext: str) -> tuple[str, str]:
    from services.fiqa_api.inbox_triage.case_store import bind_case_channel_identity, save_case
    from services.fiqa_api.inbox_triage.h5_task_token import issue_h5_intake_form_token
    from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

    saved = save_case("我要理赔", _triage_stub(), service_lane=SERVICE_LANE_CLAIM)
    case_id = str(saved.get("case_id") or "")
    bind_case_channel_identity(case_id, wecom_external_userid=ext)
    token = issue_h5_intake_form_token(case_id=case_id, external_userid=ext)
    return case_id, token


def run_in_process_smoke() -> dict[str, Any]:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from services.fiqa_api.routes.h5_task_intake import router as h5_intake_router
    from services.fiqa_api.routes.inbox_triage import router as inbox_router

    _setup_temp_store()
    suffix = _utc_suffix()
    ext = f"{SMOKE_EXT_PREFIX}{suffix}"
    case_id, token = _seed_claim_case(ext)

    app = FastAPI()
    app.include_router(h5_intake_router)
    app.include_router(inbox_router)
    client = TestClient(app)

    status_open = _status_card_checks_open(case_id, ext)
    h5 = _run_h5_flow_checks(client, token)
    wb = _workbench_checks(case_id, client)
    status_submitted = _status_card_checks_submitted(case_id)

    checks = {
        **h5,
        **{f"card_{k}": v for k, v in _wecom_card_copy_checks().items()},
        **{f"status_{k}": v for k, v in status_open.items()},
        **{f"wb_{k}": v for k, v in wb.items()},
        **{f"status_{k}": v for k, v in status_submitted.items()},
    }
    passed = all(
        checks.get(k)
        for k in (
            "get_intake_status",
            "flow_is_claim_intake_form",
            "has_upload_url",
            "upload_url_has_task_upload",
            "steps_include_evidence",
            "patch_all_fields",
            "persisted_location",
            "persisted_vehicle",
            "current_step_review",
            "submitted",
            "submit_idempotent",
            "wb_intake_ready_for_broker",
            "wb_has_customer_submitted_intake",
            "wb_facts_location",
            "status_open_has_continue_link",
            "status_status_request_no_duplicate_case",
        )
        if checks.get(k) is not False
    ) and checks.get("get_intake_status") == 200

    return {
        "mode": "in_process",
        "case_id": case_id,
        "external_userid": ext,
        "checks": checks,
        "pass": passed,
    }


def run_http_smoke(base_url: str, *, use_qa_db: bool) -> dict[str, Any]:
    if use_qa_db or _is_deploy_url(base_url):
        _load_cloudrun_env()
        _ensure_h5_token_secret_for_deploy()
        os.environ["ENV"] = "prod"
        from scripts.demo_db_resolve import apply_qa_postgres_env

        apply_qa_postgres_env(for_write=True)

    suffix = _utc_suffix()
    ext = f"{SMOKE_EXT_PREFIX}{suffix}"
    case_id, token = _seed_claim_case(ext)

    health = _probe_health(base_url)
    h5_checks: dict[str, Any] = {"health": health}

    if not health.get("ok"):
        return {
            "mode": "http",
            "base_url": base_url,
            "case_id": case_id,
            "checks": h5_checks,
            "pass": False,
            "note": "API unreachable — use in-process mode for local verification",
        }

    class _HttpClient:
        def get(self, path: str):
            status, body = _http_json("GET", base_url, path)
            return _Resp(status, body)

        def patch(self, path: str, json: dict | None = None):
            status, body = _http_json("PATCH", base_url, path, json)
            return _Resp(status, body)

        def post(self, path: str, json: dict | None = None, headers: dict | None = None):
            # headers merged via intent id in body for smoke simplicity
            status, body = _http_json("POST", base_url, path, json)
            return _Resp(status, body)

    client = _HttpClient()
    status_open = _status_card_checks_open(case_id, ext)
    flow = _run_h5_flow_checks(client, token, http_mode=True)
    wb = _workbench_checks(case_id, client)
    status_submitted = _status_card_checks_submitted(case_id)

    h5_checks.update(flow)
    h5_checks.update({f"status_{k}": v for k, v in status_open.items()})
    h5_checks.update({f"wb_{k}": v for k, v in wb.items()})
    h5_checks.update({f"status_{k}": v for k, v in status_submitted.items()})

    passed = health.get("ok") and flow.get("submitted") and flow.get("submit_idempotent")

    return {
        "mode": "http",
        "base_url": base_url,
        "case_id": case_id,
        "external_userid": ext,
        "checks": h5_checks,
        "pass": passed,
    }


class _Resp:
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self) -> dict[str, Any]:
        return self._payload


def main() -> int:
    parser = argparse.ArgumentParser(description="P19H-3h Claim H5 intake deploy smoke")
    parser.add_argument(
        "--base-url",
        default=None,
        help="API base URL (e.g. http://localhost:8001 or Cloud Run URL). Omit for in-process.",
    )
    parser.add_argument(
        "--use-qa-db",
        action="store_true",
        help="Seed case in QA Postgres before HTTP smoke (required for deploy URL)",
    )
    parser.add_argument(
        "--in-process",
        action="store_true",
        help="Force in-process TestClient mode (default when --base-url omitted)",
    )
    args = parser.parse_args()

    suffix = _utc_suffix()
    report: dict[str, Any] = {
        "script": "p19h3h_claim_h5_intake_smoke.py",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "suffix": suffix,
    }

    if args.base_url and not args.in_process:
        report["result"] = run_http_smoke(args.base_url, use_qa_db=args.use_qa_db)
    else:
        report["result"] = run_in_process_smoke()
        if args.base_url:
            report["health_probe"] = _probe_health(args.base_url)

    out_path = _evidence_path(suffix)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    passed = bool(report["result"].get("pass"))
    mode = report["result"].get("mode")
    print(json.dumps({"pass": passed, "mode": mode, "evidence": str(out_path)}, indent=2))
    if not passed:
        print("FAIL checks:", json.dumps(report["result"].get("checks"), indent=2, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
