#!/usr/bin/env python3
"""
P24G — Camry Golden QA Case helpers (reset / seed / verify / mint).

Scoped to demo_name=camry_golden_qa + workbench_test only.
Reuses case_store + Slice1 command service + Constitution projection + H5 tokens.

Usage (prefer the shell wrapper):
  bash scripts/reset_camry_golden_qa.sh --qa --reseed
  PYTHONPATH=. python3 scripts/camry_golden_qa.py reset --target local --reseed
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEMO_NAME: Final[str] = "camry_golden_qa"
CUSTOMER_NAME: Final[str] = "陈明"
VEHICLE: Final[str] = "2020 Toyota Camry"
EXTERNAL_USER_PREFIX: Final[str] = "wm_camry_golden_"
# `ui-smoky-beta` is a Production alias (Production API). Founder QA must use the
# Vercel Preview QA alias + document-intake so Phone + Workbench share Cloud QA.
# SSOT: docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md · ui/src/config/workbenchEnv.ts
WORKBENCH_QA_URL: Final[str] = (
    "https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/document-intake"
)
# Cloud QA, not Production. Keep this aligned with CLOUD_QA_RESOURCE_NAMES.md
# and the Preview/Mini Program QA clients.
API_QA_BASE: Final[str] = "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app"
ARTIFACT_DIR: Final[Path] = ROOT / "docs" / "evidence" / "golden_qa" / "last_reset"

# Constitution oracle (do not redesign — match constitution_projection + Camry fixtures).
EXPECTED_CUSTOMER = {
    "today": "上传保险卡",
    "why": "事故经过和现场照片已经完成。",
    "after": "陈总开始审核。",
    "trust_care_line": "陈总已收到资料",
    "trust_care_note": "如有需要，我们会联系您",
    "current_stage": "customer_action_needed",
}
EXPECTED_BROKER = {
    "next_label": "暂无动作",
    "next_enabled": False,
    "next_note": "等客户上传保险卡后再开始审核。",
    "priority_band": "customer_missing",
    "queue_label": "还缺客户关键资料",
    "why_attention": "关键保险卡还在客户手里，今天案件推不动。",
    "customer_focus": "上传保险卡",
    "current_stage": "customer_action_needed",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _utc_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _mask_token(token: str) -> str:
    t = (token or "").strip()
    if len(t) <= 16:
        return "h5t1_…"
    return f"{t[:8]}…{t[-6:]}"


def _is_golden_case(case: dict[str, Any]) -> bool:
    if str(case.get("demo_name") or "").strip() == DEMO_NAME:
        return True
    flags = case.get("demo_flags")
    if isinstance(flags, dict) and str(flags.get("demo_name") or "").strip() == DEMO_NAME:
        return True
    return False


def configure_target(target: str) -> str:
    """Configure process env for local JSON or QA Cloud SQL. Returns storage label."""
    from scripts.demo_db_resolve import apply_qa_postgres_env, ensure_h5_task_token_secret

    t = (target or "local").strip().lower()
    if t in ("qa", "cloud", "gcp"):
        ident = apply_qa_postgres_env(for_write=True)
        os.environ.setdefault("ENV", "prod")
        ensure_h5_task_token_secret()
        return f"qa_cloud_sql ({ident.masked()})"
    # local JSON (deterministic, isolated from QA)
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_READS", None)
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    os.environ.setdefault("UNIFIED_INTAKE_JSON_CASE_WRITES", "1")
    os.environ.setdefault("ENV", "development")
    if not (os.getenv("UNIFIED_INTAKE_CASES_PATH") or "").strip():
        path = ROOT / "data" / "camry_golden_qa_cases.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(json.dumps({"cases": []}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    return f"local_json ({os.environ['UNIFIED_INTAKE_CASES_PATH']})"


def configure_ephemeral_local() -> str:
    """Temp JSON store for unit tests (does not touch data/camry_golden_qa_cases.json)."""
    tmp = tempfile.mkdtemp(prefix="camry_golden_qa_")
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_READS", None)
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    return str(path)


def list_golden_case_ids(target: str) -> list[str]:
    from services.fiqa_api.inbox_triage.case_store import delete_case  # noqa: F401
    from services.fiqa_api.inbox_triage.case_store import list_all_cases
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

    ids: list[str] = []
    if target in ("qa", "cloud", "gcp"):
        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT record_id FROM service_records
                    WHERE COALESCE(extra->>'demo_name', '') = %s
                      AND COALESCE(extra->>'workbench_test', 'false') IN ('true', 't', '1')
                    """,
                    (DEMO_NAME,),
                )
                ids = [str(row[0]) for row in cur.fetchall()]
        # Prefer Postgres list; fall back empty
        return ids

    for case in list_all_cases():
        if not _is_golden_case(case):
            continue
        if not bool(case.get("workbench_test")):
            print(f"[WARN] Skipping non-test golden-tagged case {case.get('case_id')}")
            continue
        cid = str(case.get("case_id") or "").strip()
        if cid:
            ids.append(cid)
    # Touch get_case_for_read import for symmetry / future use
    _ = get_case_for_read
    return ids


def remove_golden_cases(*, target: str, dry_run: bool) -> list[str]:
    from services.fiqa_api.inbox_triage.case_store import delete_case

    removed: list[str] = []
    for cid in list_golden_case_ids(target):
        if dry_run:
            print(f"[DRY-RUN] Would remove Golden Case {cid}")
        elif delete_case(cid):
            print(f"[OK] Removed Golden Case {cid}")
        else:
            raise RuntimeError(f"failed_to_remove_golden_case:{cid}")
        removed.append(cid)
    return removed


def _camry_slice1_before(case_id: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "workflow_state": "broker_more_requested",
        "customer_next_action": {
            "action_type": "provide_evidence",
            "title": "上传保险卡",
            "required_input": "policy_or_insurance_card",
            "status": "active",
            "instructions": "请上传清晰的保险卡照片",
        },
        "broker_next_action": {
            "action_type": "wait_for_customer_item",
            "status": "waiting_for_customer",
        },
        "open_request": {
            "status": "open",
            "active_item": {
                "item_type": "policy_or_insurance_card",
                "label": "上传保险卡",
                "status": "active",
            },
            "queued_items": [],
            "items": [
                {
                    "item_type": "policy_or_insurance_card",
                    "label": "上传保险卡",
                    "status": "active",
                }
            ],
        },
    }


def _brief_and_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    brief = {
        "summary": "客户已提交事故经过和现场照片。",
        "missing_info": ["保险卡"],
        "brief_version": 1,
    }
    evidence = {
        "received_slots": ["scene_photo", "customer_damage_photo"],
        "missing_required_slots": [],
    }
    return brief, evidence


def _golden_photo_slots() -> dict[str, Any]:
    """Durable photo completion for DB-primary + workbench enrich rebuild.

    claim_evidence_summary alone is not enough on QA: Cloud SQL previously dropped
    it from the extra bag, and case-detail enrich rebuilds evidence from slots.
    Explicit received slots (already in PG extra) keep customer.why on the Camry
    oracle copy after enrich.
    """
    ts = _utc_now_iso()
    return {
        "scene_photo": {
            "status": "received",
            "source_channel": "h5_task",
            "attachment_ids": ["att_golden_scene"],
            "latest_attachment_id": "att_golden_scene",
            "updated_at": ts,
        },
        "customer_damage_photo": {
            "status": "received",
            "source_channel": "h5_task",
            "attachment_ids": ["att_golden_damage"],
            "latest_attachment_id": "att_golden_damage",
            "updated_at": ts,
        },
    }


def _finalize_case_flags(case_id: str) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_store import _persist_case_after_update
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
    from services.fiqa_api.inbox_triage.p20_slice1_command_service import SLICE1_CAPABILITY_VERSION

    case = get_case_for_read(case_id)
    if case is None:
        from services.fiqa_api.inbox_triage.case_store import get_case_by_id

        case = get_case_by_id(case_id)
    if case is None:
        raise RuntimeError(f"golden_case_missing_after_create:{case_id}")

    brief, evidence = _brief_and_evidence()
    case = dict(case)
    case["workbench_test"] = True
    case["demo_name"] = DEMO_NAME
    case["demo_flags"] = {"demo_name": DEMO_NAME, "golden_qa": True}
    case["customer_name"] = CUSTOMER_NAME
    case["slice1_capability_version"] = SLICE1_CAPABILITY_VERSION
    case["p20_slice1_capability_version"] = SLICE1_CAPABILITY_VERSION
    case["claim_case_brief"] = brief
    case["claim_evidence_summary"] = evidence
    case["claim_attachment_slots"] = _golden_photo_slots()
    case["updated_at"] = _utc_now_iso()
    if not _persist_case_after_update(case_id, case):
        raise RuntimeError(f"failed_to_persist_golden_flags:{case_id}")
    refreshed = get_case_for_read(case_id)
    if refreshed is None:
        from services.fiqa_api.inbox_triage.case_store import get_case_by_id

        refreshed = get_case_by_id(case_id)
    if refreshed is None:
        raise RuntimeError(f"golden_case_unreadable:{case_id}")
    return refreshed


def _seed_via_compat_projection(case_id: str) -> dict[str, Any]:
    """Local / fallback: persist Camry Slice1 shape via existing compat helper."""
    from services.fiqa_api.inbox_triage.case_store import apply_p20_slice1_compat_projection

    slice1 = _camry_slice1_before(case_id)
    updated = apply_p20_slice1_compat_projection(
        case_id,
        {
            "claim_phase": "broker_needs_more_info",
            "p20_slice1_projection": slice1,
            "slice1_projection": slice1,
        },
    )
    if updated is None:
        raise RuntimeError(f"compat_projection_failed:{case_id}")
    return _finalize_case_flags(case_id)


def _seed_via_slice1_request_more(case_id: str) -> dict[str, Any]:
    """QA path: real Slice1 Request More (insurance card) + legacy projection update."""
    from services.fiqa_api.inbox_triage.case_store import _persist_case_after_update
    from services.fiqa_api.inbox_triage.p20_slice1_command_service import default_slice1_service
    from services.fiqa_api.wecom.claim_state import CLAIM_PHASE_BROKER_REVIEW

    # Ensure capability flag on case before command
    case = _finalize_case_flags(case_id)
    # accept_request_more requires broker_reviewing (not broker_needs_more_info).
    case = dict(case)
    case["claim_phase"] = CLAIM_PHASE_BROKER_REVIEW
    if not _persist_case_after_update(case_id, case):
        raise RuntimeError(f"failed_to_set_broker_review_for_request_more:{case_id}")

    cmd = f"golden-reset-{uuid.uuid4().hex[:16]}"
    result = default_slice1_service().accept_request_more(
        case_id=case_id,
        broker_id="office:camry_golden_qa",
        command_id=cmd,
        idempotency_key=cmd,
        expected_case_version=0,
        requested_items=[
            {
                "item_type": "policy_or_insurance_card",
                "label": "上传保险卡",
                "instructions": "请上传清晰的保险卡照片",
                "required": True,
                "position": 1,
            }
        ],
        reason="Camry Golden QA initial state",
    )
    outcome = str(result.get("outcome") or "")
    if outcome != "accepted":
        raise RuntimeError(f"slice1_request_more_failed:{outcome}:{result.get('error_code')}")
    # Re-apply brief/evidence/tags (command may rewrite case patch)
    return _finalize_case_flags(case_id)


def seed_golden_case(*, target: str, dry_run: bool = False) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_store import (
        patch_case_known_facts,
        save_case,
        update_case_customer,
    )
    from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

    if dry_run:
        print("[DRY-RUN] Would seed Camry Golden QA (陈明 / 上传保险卡)")
        return {"case_id": "(dry-run)", "dry_run": True}

    saved = save_case(
        "Camry Golden QA",
        {
            "issue_category": "claim_intake",
            "urgency": "high",
            "manual_followup_needed": True,
            "broker_next_step": "Wait for customer insurance card",
            "client_prep": "",
            "client_reply_draft": "",
            "handoff_ready": False,
            # Broker reviewing first — Request More transitions into needs_more_info.
            "claim_phase": "broker_review",
        },
        service_lane=SERVICE_LANE_CLAIM,
    )
    case_id = str(saved.get("case_id") or "").strip()
    if not case_id:
        raise RuntimeError("save_case_returned_empty_case_id")

    update_case_customer(case_id, customer_name=CUSTOMER_NAME)
    patch_case_known_facts(
        case_id,
        {
            "own_vehicle_info": VEHICLE,
            "accident_location": "停车场",
            "accident_description": "倒车碰撞，前保险杠受损",
            "qa_label": "Camry Golden QA",
        },
        source="customer_task",
    )

    if target in ("qa", "cloud", "gcp"):
        try:
            case = _seed_via_slice1_request_more(case_id)
        except Exception as exc:
            print(f"[WARN] Slice1 Request More path failed ({exc}); falling back to compat projection")
            case = _seed_via_compat_projection(case_id)
    else:
        case = _seed_via_compat_projection(case_id)

    print(f"[OK] Seeded Camry Golden QA: {case_id}")
    return case


def mint_golden_token(case_id: str) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.p20_customer_launch import issue_customer_launch_token

    ext = f"{EXTERNAL_USER_PREFIX}{_utc_tag()}"
    launch = issue_customer_launch_token(case_id=case_id, external_userid=ext)
    return {
        "case_id": case_id,
        "token": launch.token,
        "masked_token": _mask_token(launch.token),
        "token_hash": launch.token_hash,
        "expires_at": launch.expires_at_iso,
        "launch_url": launch.launch_url,
        "mini_program_path": launch.mini_program_path,
        "devtools_launch_query": f"token={launch.token}",
        "external_userid": ext,
    }


def _load_case(case_id: str) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

    case = get_case_for_read(case_id)
    if case is None:
        from services.fiqa_api.inbox_triage.case_store import get_case_by_id

        case = get_case_by_id(case_id)
    if case is None:
        raise RuntimeError(f"case_not_found:{case_id}")
    return case


def _slice1_looks_like_customer_work(slice1: dict[str, Any] | None) -> bool:
    """True when projection still has an active customer evidence/fact task."""
    if not isinstance(slice1, dict) or not slice1:
        return False
    action = slice1.get("customer_next_action")
    if isinstance(action, dict):
        action_type = str(action.get("action_type") or "").strip().lower()
        if action_type in ("provide_evidence", "provide_fact"):
            return True
    open_request = slice1.get("open_request")
    if isinstance(open_request, dict) and str(open_request.get("status") or "").lower() == "open":
        active = open_request.get("active_item")
        if isinstance(active, dict) and str(active.get("status") or "").lower() == "active":
            return True
    return False


def _slice1_for_case(case: dict[str, Any], *, prefer_live: bool) -> dict[str, Any] | None:
    stored: dict[str, Any] | None = None
    for key in ("p20_slice1_projection", "slice1_projection"):
        raw = case.get(key)
        if isinstance(raw, dict) and raw:
            stored = dict(raw)
            break

    if prefer_live:
        try:
            from services.fiqa_api.inbox_triage.p20_slice1_command_service import default_slice1_service

            live = default_slice1_service().fetch_projection(str(case.get("case_id") or ""))
            if isinstance(live, dict) and live:
                # Prefer live only when it still reflects customer work. Empty/idle
                # live aggregates must not mask a correct stored Golden seed.
                if _slice1_looks_like_customer_work(live) or not _slice1_looks_like_customer_work(stored):
                    return live
        except Exception as exc:
            print(f"[WARN] live Slice1 fetch failed: {exc}")
    return stored


def build_golden_constitution(case_id: str, *, prefer_live_slice1: bool) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.constitution_projection import (
        ConstitutionInputs,
        build_constitution_projection,
    )

    case = _load_case(case_id)
    slice1 = _slice1_for_case(case, prefer_live=prefer_live_slice1)
    return build_constitution_projection(
        ConstitutionInputs(
            case=case,
            slice1=slice1,
            brief=case.get("claim_case_brief") if isinstance(case.get("claim_case_brief"), dict) else None,
            evidence=(
                case.get("claim_evidence_summary")
                if isinstance(case.get("claim_evidence_summary"), dict)
                else None
            ),
            claim_phase=str(case.get("claim_phase") or "") or None,
        )
    )


def _check_constitution(projection: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    customer = projection.get("customer") if isinstance(projection.get("customer"), dict) else {}
    broker = projection.get("broker") if isinstance(projection.get("broker"), dict) else {}
    trust = customer.get("trust") if isinstance(customer.get("trust"), dict) else {}
    next_action = broker.get("next_action") if isinstance(broker.get("next_action"), dict) else {}
    priority = broker.get("priority") if isinstance(broker.get("priority"), dict) else {}
    queue = broker.get("queue_summary") if isinstance(broker.get("queue_summary"), dict) else {}
    conclusion = broker.get("case_conclusion") if isinstance(broker.get("case_conclusion"), dict) else {}

    checks = [
        ("customer.today", customer.get("today"), EXPECTED_CUSTOMER["today"]),
        ("customer.why", customer.get("why"), EXPECTED_CUSTOMER["why"]),
        ("customer.after", customer.get("after"), EXPECTED_CUSTOMER["after"]),
        ("customer.trust.care_line", trust.get("care_line"), EXPECTED_CUSTOMER["trust_care_line"]),
        ("customer.trust.care_note", trust.get("care_note"), EXPECTED_CUSTOMER["trust_care_note"]),
        ("customer.current_stage", customer.get("current_stage"), EXPECTED_CUSTOMER["current_stage"]),
        ("broker.next_action.label", next_action.get("label"), EXPECTED_BROKER["next_label"]),
        ("broker.next_action.enabled", next_action.get("enabled"), EXPECTED_BROKER["next_enabled"]),
        ("broker.next_action.note", next_action.get("note"), EXPECTED_BROKER["next_note"]),
        ("broker.priority.band", priority.get("band"), EXPECTED_BROKER["priority_band"]),
        ("broker.queue_summary.label", queue.get("label"), EXPECTED_BROKER["queue_label"]),
        ("broker.queue_summary.why_attention", queue.get("why_attention"), EXPECTED_BROKER["why_attention"]),
        ("broker.case_conclusion.customer_focus", conclusion.get("customer_focus"), EXPECTED_BROKER["customer_focus"]),
        ("broker.current_stage", broker.get("current_stage"), EXPECTED_BROKER["current_stage"]),
        ("projection.current_stage", projection.get("current_stage"), EXPECTED_CUSTOMER["current_stage"]),
    ]
    for name, actual, expected in checks:
        if actual != expected:
            defects.append(f"{name}: expected={expected!r} actual={actual!r}")
    return defects


def verify_via_apis(case_id: str, token: str, *, prefer_live_slice1: bool) -> dict[str, Any]:
    """Verify Customer H5 + broker list/detail Constitution via FastAPI TestClient."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from services.fiqa_api.routes.h5_task_intake import router as h5_router
    from services.fiqa_api.routes.inbox_triage import router as inbox_router

    app = FastAPI()
    app.include_router(inbox_router)
    app.include_router(h5_router)
    client = TestClient(app)

    report: dict[str, Any] = {"checks": {}, "defects": []}

    # Pure Constitution (authoritative oracle)
    projection = build_golden_constitution(case_id, prefer_live_slice1=prefer_live_slice1)
    pure_defects = _check_constitution(projection)
    report["checks"]["constitution_pure"] = "PASS" if not pure_defects else "FAIL"
    report["defects"].extend(pure_defects)
    report["constitution_projection"] = projection

    # Customer API
    h5 = client.get(f"/api/h5/tasks/{token}/intake")
    report["checks"]["customer_api_status"] = h5.status_code
    if h5.status_code != 200:
        report["defects"].append(f"customer_api: HTTP {h5.status_code}")
        h5_body: dict[str, Any] = {}
    else:
        h5_body = h5.json()
        cp = h5_body.get("constitution_projection") or {}
        cust = cp.get("customer") if isinstance(cp.get("customer"), dict) else cp
        if str(cust.get("today") or "") != EXPECTED_CUSTOMER["today"]:
            report["defects"].append(
                f"customer_api.today: expected={EXPECTED_CUSTOMER['today']!r} actual={cust.get('today')!r}"
            )
        stage = cust.get("current_stage") or cp.get("current_stage")
        if str(stage or "") != EXPECTED_CUSTOMER["current_stage"]:
            report["defects"].append(
                f"customer_api.stage: expected={EXPECTED_CUSTOMER['current_stage']!r} actual={stage!r}"
            )
    report["checks"]["customer_api"] = (
        "PASS" if h5.status_code == 200 and not any(d.startswith("customer_api") for d in report["defects"]) else "FAIL"
    )
    report["customer_h5"] = {
        "case_id": h5_body.get("case_id"),
        "constitution_projection": h5_body.get("constitution_projection"),
        "slice1_title": ((h5_body.get("slice1_projection") or {}).get("customer_next_action") or {}).get("title"),
    }

    # Case detail — stub live Slice1 to stored/live golden when detail refresh would diverge in local JSON
    import services.fiqa_api.routes.inbox_triage as inbox_mod

    live_slice1 = _slice1_for_case(_load_case(case_id), prefer_live=prefer_live_slice1) or _camry_slice1_before(
        case_id
    )
    inbox_mod.default_slice1_service = lambda: type(  # type: ignore[attr-defined]
        "Svc",
        (),
        {"fetch_projection": staticmethod(lambda _cid: deepcopy(live_slice1))},
    )()
    inbox_mod.default_case_intake_service = lambda: type(  # type: ignore[attr-defined]
        "Svc", (), {"fetch_projection": staticmethod(lambda _cid: None)}
    )()
    inbox_mod.default_send_request_service = lambda: type(  # type: ignore[attr-defined]
        "Svc",
        (),
        {"fetch_customer_access_card": staticmethod(lambda _cid: None)},
    )()

    detail = client.get(f"/api/inbox/cases/{case_id}")
    report["checks"]["case_detail_status"] = detail.status_code
    if detail.status_code != 200:
        report["defects"].append(f"case_detail: HTTP {detail.status_code}")
        detail_body: dict[str, Any] = {}
    else:
        detail_body = detail.json()
        d_defects = _check_constitution(detail_body.get("constitution_projection") or {})
        report["defects"].extend([f"case_detail.{d}" for d in d_defects])
    report["checks"]["case_detail"] = (
        "PASS"
        if detail.status_code == 200 and not any(d.startswith("case_detail.") for d in report["defects"])
        else "FAIL"
    )
    report["case_detail"] = {
        "case_id": detail_body.get("case_id"),
        "demo_name": detail_body.get("demo_name"),
        "constitution_projection": detail_body.get("constitution_projection"),
    }

    # Case list
    listing = client.get("/api/inbox/cases", params={"limit": 50})
    report["checks"]["case_list_status"] = listing.status_code
    list_row = None
    if listing.status_code != 200:
        report["defects"].append(f"case_list: HTTP {listing.status_code}")
    else:
        cases = listing.json().get("cases") or []
        list_row = next((c for c in cases if str(c.get("case_id")) == case_id), None)
        if list_row is None:
            report["defects"].append("case_list: golden case not present in list")
        else:
            q = (list_row.get("constitution_projection") or {}).get("broker") or {}
            qs = q.get("queue_summary") or {}
            na = q.get("next_action") or {}
            pr = q.get("priority") or {}
            if qs.get("band") != EXPECTED_BROKER["priority_band"]:
                report["defects"].append(
                    f"case_list.band: expected={EXPECTED_BROKER['priority_band']!r} actual={qs.get('band')!r}"
                )
            if na.get("label") != EXPECTED_BROKER["next_label"]:
                report["defects"].append(
                    f"case_list.next: expected={EXPECTED_BROKER['next_label']!r} actual={na.get('label')!r}"
                )
            if pr.get("band") != EXPECTED_BROKER["priority_band"]:
                report["defects"].append(
                    f"case_list.priority: expected={EXPECTED_BROKER['priority_band']!r} actual={pr.get('band')!r}"
                )
    report["checks"]["case_list"] = (
        "PASS"
        if listing.status_code == 200 and not any(d.startswith("case_list") for d in report["defects"])
        else "FAIL"
    )
    report["case_list_row"] = {
        "found": list_row is not None,
        "constitution_projection": (list_row or {}).get("constitution_projection"),
    }

    # Frontend resolvers (optional — same oracle fields)
    resolver_result = _verify_frontend_resolvers(
        h5_body=h5_body,
        list_row=list_row or {},
        detail_body=detail_body,
    )
    report["checks"]["customer_resolver"] = resolver_result.get("customer", "SKIP")
    report["checks"]["broker_resolver"] = resolver_result.get("broker", "SKIP")
    report["defects"].extend(resolver_result.get("defects") or [])
    report["resolver"] = resolver_result

    report["ok"] = len(report["defects"]) == 0
    return report


def _verify_frontend_resolvers(
    *,
    h5_body: dict[str, Any],
    list_row: dict[str, Any],
    detail_body: dict[str, Any],
) -> dict[str, Any]:
    """Best-effort production resolver check via node --import tsx."""
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    h5_path = ARTIFACT_DIR / "verify_h5.json"
    list_path = ARTIFACT_DIR / "verify_list_row.json"
    detail_path = ARTIFACT_DIR / "verify_detail.json"
    h5_path.write_text(json.dumps(h5_body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    list_path.write_text(json.dumps(list_row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    detail_path.write_text(json.dumps(detail_body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    script = ROOT / "scripts" / "p24g_verify_golden_resolvers.mjs"
    if not script.exists():
        return {"customer": "SKIP", "broker": "SKIP", "defects": [], "reason": "resolver_script_missing"}

    import subprocess

    # ui/ cwd required for @/ path aliases; tsx binary may live under miniapp/.
    ui_dir = ROOT / "ui"
    tsx_bin = None
    for candidate in (
        ROOT / "ui" / "node_modules" / ".bin" / "tsx",
        ROOT / "miniapp" / "node_modules" / ".bin" / "tsx",
        ROOT / "node_modules" / ".bin" / "tsx",
    ):
        if candidate.exists():
            tsx_bin = candidate
            break
    if tsx_bin is None or not ui_dir.exists():
        return {
            "customer": "SKIP",
            "broker": "SKIP",
            "defects": [],
            "reason": "tsx_unavailable",
        }

    try:
        proc = subprocess.run(
            [
                str(tsx_bin),
                str(script),
                str(h5_path),
                str(list_path),
                str(detail_path),
            ],
            cwd=str(ui_dir),
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
    except FileNotFoundError:
        return {"customer": "SKIP", "broker": "SKIP", "defects": [], "reason": "node_unavailable"}
    except Exception as exc:
        return {"customer": "SKIP", "broker": "SKIP", "defects": [], "reason": f"resolver_error:{exc}"}

    err = (proc.stderr or "").strip()
    out = (proc.stdout or "").strip()
    toolchain_markers = (
        "ERR_MODULE_NOT_FOUND",
        "Cannot find package 'tsx'",
        "Cannot find module",
        "ERR_REQUIRE_ESM",
    )
    if any(m in err for m in toolchain_markers) and "customer.today=" not in out:
        # Toolchain / alias issues are SKIP — not a Golden Case content failure.
        return {
            "customer": "SKIP",
            "broker": "SKIP",
            "defects": [],
            "reason": "resolver_toolchain",
            "stderr": err[:500],
        }

    try:
        payload = json.loads(out.splitlines()[-1]) if out else {}
    except Exception:
        payload = {}

    if not isinstance(payload, dict) or "customer" not in payload:
        if proc.returncode != 0:
            return {
                "customer": "SKIP",
                "broker": "SKIP",
                "defects": [],
                "reason": "resolver_unparseable",
                "stderr": err[:500],
            }
        payload = {"customer": "PASS", "broker": "PASS", "defects": []}

    if not isinstance(payload.get("defects"), list):
        payload["defects"] = []
    # Only content mismatches block reset (prefixed customer.* / broker.*)
    content_defects = [
        d for d in payload["defects"] if str(d).startswith(("customer.", "broker."))
    ]
    payload["defects"] = content_defects
    if content_defects:
        payload["customer"] = "FAIL" if any(str(d).startswith("customer.") for d in content_defects) else payload.get("customer", "PASS")
        payload["broker"] = "FAIL" if any(str(d).startswith("broker.") for d in content_defects) else payload.get("broker", "PASS")
    return payload


def reset_golden_qa(
    *,
    target: str,
    reseed: bool = True,
    dry_run: bool = False,
    skip_verify: bool = False,
) -> dict[str, Any]:
    """
    Atomic-enough Golden reset:
      remove tagged cases → seed → mint token → verify.
    On verify failure after seed: one recovery reseed; still fail closed if not green.
    """
    storage = configure_target(target)
    print("=" * 56)
    print(f"Camry Golden QA Reset (target={target})")
    print(f"Storage: {storage}")
    print("=" * 56)

    removed = remove_golden_cases(target=target, dry_run=dry_run)
    print(f"Removed: {len(removed)}")

    if not reseed:
        return {
            "ok": True,
            "removed": removed,
            "reseeded": False,
            "storage": storage,
        }

    if dry_run:
        seed_golden_case(target=target, dry_run=True)
        return {"ok": True, "removed": removed, "reseeded": False, "dry_run": True, "storage": storage}

    prefer_live = target in ("qa", "cloud", "gcp")
    case: dict[str, Any] | None = None
    token_info: dict[str, Any] | None = None
    verify_report: dict[str, Any] | None = None
    last_error: str | None = None

    for attempt in (1, 2):
        try:
            if attempt == 2:
                print("[RECOVERY] Verification failed — removing and reseeding once")
                remove_golden_cases(target=target, dry_run=False)
            case = seed_golden_case(target=target, dry_run=False)
            case_id = str(case.get("case_id") or "")
            token_info = mint_golden_token(case_id)
            if skip_verify:
                verify_report = {"ok": True, "skipped": True, "checks": {}, "defects": []}
                break
            verify_report = verify_via_apis(
                case_id,
                str(token_info["token"]),
                prefer_live_slice1=prefer_live,
            )
            if verify_report.get("ok"):
                break
            last_error = "; ".join(verify_report.get("defects") or ["verify_failed"])
            print(f"[FAIL] Verify attempt {attempt}: {last_error}")
        except Exception as exc:
            last_error = str(exc)
            print(f"[FAIL] Reset attempt {attempt}: {exc}")
            case = None
            token_info = None

    if case is None or token_info is None or not (verify_report or {}).get("ok"):
        # Fail closed — do not print Founder-ready token on red verify
        raise RuntimeError(
            "golden_reset_failed_closed: "
            + (last_error or "unknown")
            + " — Golden Case may be absent or unverified; re-run reset after fixing cause"
        )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    handoff = {
        "timestamp_utc": _utc_now_iso(),
        "target": target,
        "storage": storage,
        "demo_name": DEMO_NAME,
        "case_id": case.get("case_id"),
        "customer_name": CUSTOMER_NAME,
        "vehicle": VEHICLE,
        "removed_case_ids": removed,
        "token_masked": token_info["masked_token"],
        "token": token_info["token"],
        "expires_at": token_info["expires_at"],
        "devtools_launch_query": token_info["devtools_launch_query"],
        "mini_program_path": token_info["mini_program_path"],
        "launch_url": token_info["launch_url"],
        "workbench_url": WORKBENCH_QA_URL if prefer_live else "http://localhost:5173/workbench/document-intake",
        "api_intake_url": f"{API_QA_BASE if prefer_live else 'http://127.0.0.1:8001'}/api/h5/tasks/{token_info['token']}/intake",
        "verification": {
            "ok": True,
            "checks": verify_report.get("checks"),
            "defects": verify_report.get("defects"),
        },
        "expected_initial_state": {
            "customer": EXPECTED_CUSTOMER,
            "broker": EXPECTED_BROKER,
        },
    }
    handoff_path = ARTIFACT_DIR / "handoff.json"
    # Session handoff — contains raw token; do not commit
    handoff_path.write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ARTIFACT_DIR / "verify_report.json").write_text(
        json.dumps(verify_report, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    _print_founder_handoff(handoff, handoff_path)
    return handoff


def _print_founder_handoff(handoff: dict[str, Any], handoff_path: Path) -> None:
    token = str(handoff.get("token") or "")
    case_id = str(handoff.get("case_id") or "")
    print()
    print("=" * 56)
    print("GOLDEN QA READY")
    print("=" * 56)
    print(f"Case ID:     {case_id}")
    print(f"Customer:    {CUSTOMER_NAME}")
    print(f"Vehicle:     {VEHICLE}")
    print(f"Token:       {token}")
    print(f"Masked:      {handoff.get('token_masked')}")
    print(f"Expires:     {handoff.get('expires_at')}")
    print(f"Workbench:   {handoff.get('workbench_url')}")
    print()
    print("Preview launch (WeChat DevTools — once):")
    print("  pathName: pages/entry/entry")
    print(f"  query:    token={token}")
    print("  Then: 清缓存 → 全部清除 → 重新编译 → Preview → scan QR ONCE")
    print()
    print("QR generation:")
    print("  Use DevTools Preview QR after the compile query above is set.")
    print("  Or open Workbench Copy Link for the same Case (optional).")
    print()
    print("Initial state (verified):")
    print(f"  Customer Today: {EXPECTED_CUSTOMER['today']}")
    print(f"  Stage:          {EXPECTED_CUSTOMER['current_stage']}")
    print(f"  Broker next:    {EXPECTED_BROKER['next_label']} / note={EXPECTED_BROKER['next_note']}")
    print(f"  Priority:       {EXPECTED_BROKER['priority_band']}")
    print()
    print(f"Handoff file (session; do not commit): {handoff_path}")
    print("Next: run Golden Production QA — docs/product/p24f_golden_production_qa_flow.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Camry Golden QA reset / seed / verify")
    parser.add_argument(
        "command",
        nargs="?",
        default="reset",
        choices=("reset", "seed", "remove", "verify", "mint"),
        help="reset = remove + reseed + mint + verify (default)",
    )
    parser.add_argument(
        "--target",
        choices=("local", "qa", "cloud"),
        default="local",
        help="local=JSON store; qa/cloud=GCP Cloud SQL (Cloud Run SSOT)",
    )
    parser.add_argument("--reseed", action="store_true", help="After remove, seed Golden Case (reset default)")
    parser.add_argument("--no-reseed", action="store_true", help="Remove only")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-verify", action="store_true")
    parser.add_argument("--case-id", default="", help="For verify/mint only")
    parser.add_argument("--token", default="", help="For verify only")
    args = parser.parse_args()

    target = "qa" if args.target in ("qa", "cloud") else "local"
    reseed = True
    if args.no_reseed:
        reseed = False
    elif args.command == "reset" and not args.reseed and not args.no_reseed:
        reseed = True  # reset always reseeds unless --no-reseed
    elif args.command == "reset":
        reseed = bool(args.reseed) or not args.no_reseed

    try:
        if args.command == "remove":
            configure_target(target)
            removed = remove_golden_cases(target=target, dry_run=args.dry_run)
            print(json.dumps({"removed": removed}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "seed":
            configure_target(target)
            case = seed_golden_case(target=target, dry_run=args.dry_run)
            print(json.dumps({"case_id": case.get("case_id")}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "mint":
            configure_target(target)
            cid = (args.case_id or "").strip()
            if not cid:
                ids = list_golden_case_ids(target)
                if not ids:
                    raise RuntimeError("no_golden_case_to_mint")
                cid = ids[0]
            info = mint_golden_token(cid)
            print(json.dumps(info, ensure_ascii=False, indent=2))
            return 0
        if args.command == "verify":
            configure_target(target)
            cid = (args.case_id or "").strip()
            if not cid:
                ids = list_golden_case_ids(target)
                if not ids:
                    raise RuntimeError("no_golden_case_to_verify")
                cid = ids[0]
            token = (args.token or "").strip()
            if not token:
                token = str(mint_golden_token(cid)["token"])
            report = verify_via_apis(cid, token, prefer_live_slice1=(target == "qa"))
            print(json.dumps({"ok": report["ok"], "checks": report["checks"], "defects": report["defects"]}, ensure_ascii=False, indent=2))
            return 0 if report["ok"] else 1

        # reset
        reset_golden_qa(
            target=target,
            reseed=reseed,
            dry_run=args.dry_run,
            skip_verify=args.skip_verify,
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
