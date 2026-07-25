#!/usr/bin/env python3
"""P19M-1A — Mini Program prototype real E2E verification (HTTP-level).

Simulates the mini program CustomerTaskApi flow against a live or in-process backend.
WeChat DevTools UI verification remains manual; this script proves API integration.

Usage:
  PYTHONPATH=. python3 scripts/p19m1a_devtools_e2e_smoke.py
  PYTHONPATH=. python3 scripts/p19m1a_devtools_e2e_smoke.py --base-url http://127.0.0.1:8001
  PYTHONPATH=. python3 scripts/p19m1a_devtools_e2e_smoke.py --base-url https://fiqa-api-g7zatxrycq-uw.a.run.app --qa-db
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

QA_LABEL_PREFIX = "P19M1A-DEVTOOLS-E2E"
QA_STORY = "测试事故：我在红灯前停车时，后方车辆低速追尾。无人受伤。"
SUBMIT_INTENT = "p19m1a-e2e-0000-4000-8000-000000000001"
SMOKE_EXT = "wm_p19m1a_e2e"


def _utc_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")


def _mask_token(token: str) -> str:
    t = (token or "").strip()
    if len(t) <= 16:
        return "h5t1_…"
    return f"{t[:8]}…{t[-6:]}"


def _tiny_jpeg() -> bytes:
    return bytes(
        [
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
            0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
            0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
            0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
            0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
            0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
            0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
            0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
            0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
            0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
            0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
            0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
            0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5, 0xDB, 0x20, 0xA8, 0xF1, 0x45, 0x00,
            0xFF, 0xD9,
        ]
    )


def _http_json(method: str, base: str, path: str, body: dict | None = None) -> tuple[int, dict[str, Any]]:
    url = f"{base.rstrip('/')}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"detail": raw}
        return exc.code, payload


def _multipart_upload(base: str, token: str, slot: str, content: bytes) -> tuple[int, dict[str, Any]]:
    boundary = "----p19m1aBoundary7MA4YWxk"
    body = BytesIO()
    for key, val in [("slot", slot)]:
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        body.write(f"{val}\r\n".encode())
    body.write(f"--{boundary}\r\n".encode())
    body.write(b'Content-Disposition: form-data; name="file"; filename="qa.jpg"\r\n')
    body.write(b"Content-Type: image/jpeg\r\n\r\n")
    body.write(content)
    body.write(f"\r\n--{boundary}--\r\n".encode())
    payload = body.getvalue()
    url = f"{base.rstrip('/')}/api/h5/tasks/{token}/upload"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"detail": raw}
        return exc.code, parsed


def _bootstrap_env(
    *,
    cloud_sql: bool,
    cases_path: Path | None,
    json_local: bool,
) -> None:
    os.environ.setdefault("UNIFIED_INTAKE_PRODUCT_ONLY", "1")
    os.environ.setdefault("UNIFIED_INTAKE_INTAKE_CORE_READINESS", "1")
    if cloud_sql:
        from scripts.demo_db_resolve import bootstrap_prototype_cloud_sql_env

        bootstrap_prototype_cloud_sql_env()
        return
    if cases_path is not None:
        os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(cases_path)
    if json_local:
        os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_READS", None)
        os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
        os.environ.setdefault("UNIFIED_INTAKE_JSON_CASE_WRITES", "1")
        os.environ.setdefault("H5_TASK_TOKEN_SECRET", "dev-prototype-secret-change-me")


def _seed_qa_case(tag: str) -> tuple[str, str]:
    from services.fiqa_api.inbox_triage.case_store import (
        bind_case_channel_identity,
        patch_case_known_facts,
        save_case,
        update_case_workbench_flags,
    )
    from services.fiqa_api.inbox_triage.h5_task_token import issue_h5_intake_form_token
    from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

    label = f"{QA_LABEL_PREFIX}-{tag}"
    saved = save_case(
        f"我要理赔 {label}",
        {
            "issue_category": "claim_intake",
            "urgency": "high",
            "manual_followup_needed": True,
            "broker_next_step": "P19M-1A mini program E2E QA.",
            "client_prep": "",
            "client_reply_draft": "",
            "handoff_ready": False,
            "claim_phase": "accident_basics_in_progress",
        },
        service_lane=SERVICE_LANE_CLAIM,
    )
    case_id = str(saved.get("case_id") or "")
    ext = f"{SMOKE_EXT}_{tag}"
    bind_case_channel_identity(case_id, wecom_external_userid=ext)
    update_case_workbench_flags(case_id, is_test=True)
    patch_case_known_facts(case_id, {"qa_label": label})
    token = issue_h5_intake_form_token(case_id=case_id, external_userid=ext, lane="claim")
    return case_id, token


def _extract_upload_token(upload_url: str) -> str:
    segment = (upload_url or "").rstrip("/").split("/")[-1]
    return segment if segment.startswith("h5t1.") else ""


def _workbench_checks(case_id: str) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
    from services.fiqa_api.inbox_triage.claim_workbench_display import enrich_claim_for_workbench
    from services.fiqa_api.wecom.claim_state import derive_claim_phase

    case = get_case_for_read(case_id) or {}
    enriched = enrich_claim_for_workbench(case)
    brief = enriched.get("claim_case_brief") or {}
    key_facts = brief.get("key_facts") or {}
    timeline = enriched.get("claim_timeline") or []
    evidence = enriched.get("claim_evidence_summary") or {}
    submit_events = [e for e in timeline if e.get("event_type") == "customer_submitted_intake"]

    return {
        "workbench_visible": enriched.get("workbench_visible") is True,
        "story_visible": QA_STORY[:12] in str(key_facts.get("accident_description") or ""),
        "photo_count": int(case.get("case_attachments") and len(case.get("case_attachments") or []) or 0),
        "evidence_received_slots": sum(
            1 for s in (evidence.get("slots") or []) if s.get("status") == "received"
        ),
        "submitted_phase": derive_claim_phase(case) in ("intake_ready_for_broker", "broker_review"),
        "broker_done_false": derive_claim_phase(case) != "broker_done",
        "submit_event_count": len(submit_events),
        "qa_label_present": QA_LABEL_PREFIX in str((case.get("known_facts") or {}).get("qa_label") or ""),
    }


def run_e2e(
    base_url: str,
    *,
    cloud_sql: bool,
    inprocess: bool,
    json_local: bool = False,
) -> dict[str, Any]:
    tag = _utc_tag()
    cases_path = None
    if inprocess:
        cases_path = Path(tempfile.mkdtemp(prefix="p19m1a_cases_")) / "cases.json"
        cases_path.write_text("[]", encoding="utf-8")
        json_local = True
    elif not cloud_sql:
        existing = (os.getenv("UNIFIED_INTAKE_CASES_PATH") or "").strip()
        if existing:
            cases_path = Path(existing)
            if not cases_path.is_absolute():
                cases_path = REPO / cases_path
        elif json_local:
            cases_path = Path(tempfile.mkdtemp(prefix="p19m1a_cases_")) / "cases.json"
            cases_path.write_text("[]", encoding="utf-8")

    _bootstrap_env(cloud_sql=cloud_sql, cases_path=cases_path, json_local=json_local)
    case_id, token = _seed_qa_case(tag)
    masked = _mask_token(token)
    checks: dict[str, Any] = {
        "qa_label": f"{QA_LABEL_PREFIX}-{tag}",
        "case_id": case_id,
        "masked_token": masked,
        "base_url": base_url,
        "mode": (
            "inprocess"
            if inprocess
            else ("cloud_sql" if cloud_sql else "json_local")
        ),
    }

    if inprocess:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from services.fiqa_api.routes.h5_task_intake import router as intake_router
        from services.fiqa_api.routes.h5_task_upload import router as upload_router
        from services.fiqa_api.wecom.media_storage import set_gcs_upload_hook_for_tests

        set_gcs_upload_hook_for_tests(
            lambda *, bucket, object_path, content, content_type: f"gs://{bucket}/{object_path}"
        )
        app = FastAPI()
        app.include_router(intake_router)
        app.include_router(upload_router)
        client = TestClient(app)

        def _get(path: str) -> tuple[int, dict]:
            r = client.get(path)
            return r.status_code, r.json()

        def _patch(path: str, body: dict) -> tuple[int, dict]:
            r = client.patch(path, json=body)
            return r.status_code, r.json()

        def _post(path: str, body: dict, headers: dict | None = None) -> tuple[int, dict]:
            r = client.post(path, json=body, headers=headers or {})
            return r.status_code, r.json()

        def _upload(upload_tok: str, slot: str) -> tuple[int, dict]:
            r = client.post(
                f"/api/h5/tasks/{upload_tok}/upload",
                data={"slot": slot},
                files={"file": ("qa.jpg", _tiny_jpeg(), "image/jpeg")},
            )
            return r.status_code, r.json()
    else:
        def _get(path: str) -> tuple[int, dict]:
            return _http_json("GET", base_url, path)

        def _patch(path: str, body: dict) -> tuple[int, dict]:
            return _http_json("PATCH", base_url, path, body)

        def _post(path: str, body: dict, headers: dict | None = None) -> tuple[int, dict]:
            url = f"{base_url.rstrip('/')}{path}"
            data = json.dumps(body).encode()
            hdrs = {"Content-Type": "application/json", **(headers or {})}
            req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    raw = resp.read().decode()
                    return resp.status, json.loads(raw) if raw else {}
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode()
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    payload = {"detail": raw}
                return exc.code, payload

        def _upload(upload_tok: str, slot: str) -> tuple[int, dict]:
            return _multipart_upload(base_url, upload_tok, slot, _tiny_jpeg())

    # Launch / Task Home
    st, intake = _get(f"/api/h5/tasks/{token}/intake")
    checks["launch_intake_status"] = st
    checks["launch_dashboard_title"] = (intake.get("dashboard_summary") or {}).get("title") == "我的报案"
    checks["launch_not_submitted"] = intake.get("submitted") is False

    # Story + basics
    for step, fields in [
        ("injury", {"anyone_injured": "no"}),
        ("time_location", {"accident_datetime": "今天上午10点", "accident_location": "QA Test Blvd"}),
        ("story", {"accident_description": QA_STORY}),
        ("vehicle_other_party", {"own_vehicle_info": "2020 QA Test Sedan"}),
    ]:
        pst, pbody = _patch(f"/api/h5/tasks/{token}/fields", {"step": step, "fields": fields})
        if pst != 200:
            checks["patch_failed"] = {"step": step, "status": pst, "body": pbody}
            checks["pass"] = False
            return checks

    st2, after_story = _get(f"/api/h5/tasks/{token}/intake")
    checks["story_saved"] = QA_STORY in str((after_story.get("key_facts") or {}).get("accident_description") or "")
    checks["review_step"] = after_story.get("current_step") == "review"

    # Photos
    upload_url = str(after_story.get("upload_url") or "")
    upload_tok = _extract_upload_token(upload_url)
    checks["upload_url_present"] = bool(upload_tok)
    for slot in ("customer_damage_photo", "other_party_vehicle_photo"):
        ust, ubody = _upload(upload_tok, slot)
        if ust != 200:
            checks["upload_failed"] = {"slot": slot, "status": ust, "body": ubody}
            checks["pass"] = False
            return checks
    st3, after_photos = _get(f"/api/h5/tasks/{token}/intake")
    checks["photo_count_gte_2"] = int(after_photos.get("photo_count") or 0) >= 2

    # Submit + idempotency
    headers = {"X-Submit-Intent-Id": SUBMIT_INTENT}
    sst, submit_body = _post(
        f"/api/h5/tasks/{token}/submit",
        {"submit_intent_id": SUBMIT_INTENT},
        headers=headers,
    )
    checks["submit_status"] = sst
    checks["submit_success"] = submit_body.get("submitted") is True
    checks["broker_done_false"] = submit_body.get("phase") != "broker_done"

    sst2, dup_body = _post(
        f"/api/h5/tasks/{token}/submit",
        {"submit_intent_id": SUBMIT_INTENT},
        headers=headers,
    )
    checks["submit_idempotent_status"] = sst2
    checks["submit_idempotent"] = dup_body.get("already_submitted") is True

    # Resume
    rst, resume_body = _get(f"/api/h5/tasks/{token}/intake")
    checks["resume_submitted"] = resume_body.get("submitted") is True
    checks["resume_step_done"] = resume_body.get("current_step") == "done"

    checks.update(_workbench_checks(case_id))
    checks["pass"] = all(
        checks.get(k) is True
        for k in (
            "launch_intake_status",
            "launch_dashboard_title",
            "story_saved",
            "photo_count_gte_2",
            "submit_success",
            "submit_idempotent",
            "resume_submitted",
            "workbench_visible",
            "story_visible",
            "submitted_phase",
            "broker_done_false",
        )
        if checks.get("launch_intake_status") == 200 or k != "launch_intake_status"
    )
    if checks.get("launch_intake_status") != 200:
        checks["pass"] = False
    else:
        checks["pass"] = (
            checks.get("launch_dashboard_title") is True
            and checks.get("story_saved") is True
            and checks.get("photo_count_gte_2") is True
            and checks.get("submit_success") is True
            and checks.get("submit_idempotent") is True
            and checks.get("resume_submitted") is True
            and checks.get("workbench_visible") is True
            and checks.get("story_visible") is True
            and checks.get("submitted_phase") is True
            and checks.get("broker_done_false") is True
            and checks.get("submit_event_count") == 1
        )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="P19M-1A mini program E2E smoke")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument(
        "--cloud-sql",
        action="store_true",
        help="Seed/read QA GCP Cloud SQL (matches run_demo_local.sh and Cloud Run)",
    )
    parser.add_argument(
        "--qa-db",
        action="store_true",
        help="Deprecated alias for --cloud-sql",
    )
    parser.add_argument("--inprocess", action="store_true", help="In-process TestClient (no network)")
    parser.add_argument(
        "--json-local",
        action="store_true",
        help="Isolated temp JSON store (must match API if using HTTP — prefer --cloud-sql)",
    )
    parser.add_argument(
        "--shared-local-store",
        action="store_true",
        help="Deprecated: use repo data/unified_intake_cases.json (JSON dev only)",
    )
    args = parser.parse_args()
    if args.qa_db:
        args.cloud_sql = True

    if args.inprocess:
        result = run_e2e(args.base_url, cloud_sql=False, inprocess=True, json_local=True)
    else:
        json_local = args.json_local or args.shared_local_store
        if args.shared_local_store:
            os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(REPO / "data" / "unified_intake_cases.json")
        if not args.cloud_sql and not json_local:
            parser.error("HTTP mode requires --cloud-sql (QA SSOT) or --json-local / --shared-local-store")
        result = run_e2e(
            args.base_url,
            cloud_sql=args.cloud_sql,
            inprocess=False,
            json_local=json_local,
        )

    out_path = REPO / "docs" / "evidence" / f"p19m1a_devtools_e2e_smoke_{_utc_tag().replace('-', '_')}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in result if k != "upload_failed"}, ensure_ascii=False, indent=2))
    print(f"\nEvidence: {out_path}")
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    sys.exit(main())
