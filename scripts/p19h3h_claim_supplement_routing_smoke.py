#!/usr/bin/env python3
"""P19H-3h — Claim supplement routing smoke (submitted Claim beats Add Car Phase 2)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.demo_db_resolve import load_cloudrun_env_skip_db

load_cloudrun_env_skip_db()


os.environ["ENV"] = "prod"

from scripts.demo_db_resolve import apply_qa_postgres_env  # noqa: E402

apply_qa_postgres_env(for_write=True)

from services.fiqa_api.inbox_triage.case_store import (  # noqa: E402
    append_follow_up_message,
    append_h5_gcs_attachment_metadata,
    bind_case_channel_identity,
    get_case_by_id,
    patch_case_known_facts,
    save_case,
    update_case_workbench_flags,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read, list_all_cases_for_read
from services.fiqa_api.inbox_triage.claim_workbench_display import enrich_claim_for_workbench
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message

_NOW = datetime.now(timezone.utc)
_PHASE2_MARKERS = ("提车日期", "停放 ZIP", "联系电话", "我还需要一点信息")


def _suffix() -> str:
    return datetime.now(timezone.utc).strftime("csr_smoke_%H%M%S")


def _evidence_path(suffix: str) -> Path:
    return REPO / "docs" / "evidence" / f"p19h3h_claim_supplement_routing_smoke_{suffix}.json"


def _text(content: str, *, ext: str, msg_id: str) -> dict:
    return normalize_text_message(
        {
            "msgid": msg_id,
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "text": {"content": content},
        }
    )


def _claim_stub() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Claim guided workflow — collect accident basics.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "claim_phase": "claim_started",
    }


def _triage_stub() -> dict:
    return {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": "Review.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
    }


def _open_claim(ext: str) -> str:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = str(saved["case_id"])
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    update_case_workbench_flags(cid, is_test=True)
    ts = (_NOW - timedelta(hours=2)).isoformat()
    patch_case_known_facts(
        cid,
        {
            "accident_datetime": "7月7日上午",
            "accident_location": "Irvine Blvd",
            "accident_description": "被追尾",
        },
    )
    append_follow_up_message(
        cid,
        "7月7日上午在 Irvine Blvd 被追尾",
        {
            **_claim_stub(),
            "collected_fields": [
                "accident_datetime",
                "accident_location",
                "accident_description",
            ],
        },
    )
    update_claim_workflow_state(
        cid,
        claim_phase="accident_basics_complete",
        guided_workflow_state="collecting_text",
    )
    case = get_case_by_id(cid) or saved
    case["created_at"] = ts
    case["updated_at"] = ts
    return cid


def _submitted_claim(ext: str) -> str:
    cid = _open_claim(ext)
    update_claim_workflow_state(
        cid,
        claim_phase="intake_ready_for_broker",
        guided_workflow_state="ready_for_broker_review",
    )
    return cid


def _photo_complete_add_car(ext: str) -> str:
    saved = save_case(
        "add car",
        {**_triage_stub(), "still_needed_fields": ["delivery_date", "zip", "phone"], "collected_fields": []},
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    cid = str(saved["case_id"])
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    update_case_workbench_flags(cid, is_test=True)
    for idx, slot in enumerate(("vin_photo", "registration_photo", "insurance_card_photo")):
        append_h5_gcs_attachment_metadata(
            cid,
            {
                "source": "h5_task",
                "slot_assignment": slot,
                "h5_upload_id": f"upload_{idx}",
                "mime_type": "image/jpeg",
            },
        )
    case = get_case_by_id(cid) or saved
    case["h5_photo_flow_state"] = {"end_card_sent_at": _NOW.isoformat()}
    return cid


def _add_car_count(ext: str) -> int:
    return sum(
        1
        for c in list_all_cases_for_read()
        if c.get("wecom_external_userid") == ext and c.get("service_lane") == SERVICE_LANE_ADD_CAR
    )


def run_smoke(*, base_url: str | None = None) -> dict:
    suffix = _suffix()
    ext = f"wm_csr_{suffix}"
    claim_id = _submitted_claim(ext)
    add_car_id = _photo_complete_add_car(ext)
    before_add_car = _add_car_count(ext)
    checks: dict[str, dict] = {}

    plate_text = "补充一下，对方车牌是 ABC123"
    r1 = ingest_claim_basics_message(
        _text(plate_text, ext=ext, msg_id=f"csr1_{suffix}"),
        classify_wecom_intent(plate_text),
    )
    reply1 = str(r1.get("reply_text") or "")
    case1 = get_case_for_read(claim_id) or get_case_by_id(claim_id) or {}
    facts1 = case1.get("known_facts") or {}
    timeline1 = case1.get("claim_timeline") or []
    checks["1_plate_supplement_beats_phase2"] = {
        "pass": r1.get("case_id") == claim_id
        and r1.get("case_created") is False
        and r1.get("active_case_outcome") == "claim_supplement_appended"
        and not any(m in reply1 for m in _PHASE2_MARKERS)
        and _add_car_count(ext) == before_add_car
        and facts1.get("other_party_plate") == "ABC123"
        and any(
            e.get("event_type") == "customer_text" and "ABC123" in str(e.get("text") or "")
            for e in timeline1
            if isinstance(e, dict)
        ),
        "active_case_outcome": r1.get("active_case_outcome"),
        "reply_excerpt": reply1[:200],
        "claim_id": claim_id,
        "add_car_id": add_car_id,
    }

    insurance_text = "对方保险是 State Farm"
    r2 = ingest_claim_basics_message(
        _text(insurance_text, ext=ext, msg_id=f"csr2_{suffix}"),
        classify_wecom_intent(insurance_text),
    )
    case2 = get_case_for_read(claim_id) or get_case_by_id(claim_id) or {}
    facts2 = case2.get("known_facts") or {}
    enriched = enrich_claim_for_workbench(case2)
    checks["2_insurance_supplement_append"] = {
        "pass": r2.get("case_id") == claim_id
        and r2.get("active_case_outcome") == "claim_supplement_appended"
        and facts2.get("other_party_info") == "State Farm"
        and _add_car_count(ext) == before_add_car,
        "workbench_has_plate": (enriched.get("known_facts") or {}).get("other_party_plate") == "ABC123",
    }

    add_car_text = "我要加车"
    r3 = ingest_claim_basics_message(
        _text(add_car_text, ext=ext, msg_id=f"csr3_{suffix}"),
        classify_wecom_intent(add_car_text),
    )
    checks["3_explicit_add_car_still_routes"] = {
        "pass": r3.get("internal_intent") == "add_car"
        or r3.get("active_case_outcome") not in ("claim_supplement_appended", None)
        or "加车" in str(r3.get("reply_text") or ""),
        "outcome": r3.get("active_case_outcome"),
        "intent": r3.get("internal_intent"),
    }

    all_pass = all(c.get("pass") for c in checks.values())
    return {
        "script": "p19h3h_claim_supplement_routing_smoke.py",
        "sprint": "P19H-3h-claim-supplement-routing",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "suffix": suffix,
        "verdict": "PASS" if all_pass else "FAIL",
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--use-qa-db", action="store_true")
    args = parser.parse_args()
    if args.use_qa_db:
        apply_qa_postgres_env(for_write=True)
    result = run_smoke(base_url=args.base_url)
    out_path = _evidence_path(result["suffix"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": result["verdict"] == "PASS", "evidence": str(out_path)}, indent=2))
    if result["verdict"] != "PASS":
        print(json.dumps(result.get("checks"), indent=2, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
