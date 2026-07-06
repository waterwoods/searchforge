"""WeCom Premium Review / Claim Lite minimal lane — rule-based case create/update (Loop 2)."""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from services.fiqa_api.inbox_triage.case_store import (
    _persist_case_after_update,
    append_follow_up_message,
    bind_case_channel_identity,
    get_case_by_id,
    save_case,
    update_case_status,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import (
    SERVICE_LANE_CLAIM_LITE,
    SERVICE_LANE_POLICY_REVIEW,
)
from services.fiqa_api.p16.packet_persist import (
    build_p16_broker_packet_blob,
    build_portal_copy_text_policy_review,
    map_policy_review_readiness,
)
from services.fiqa_api.wecom.active_case_bridge import (
    _record_wecom_evidence,
    find_case_by_wecom_msg_id,
)
from services.fiqa_api.wecom.identity import extract_phone_from_text, wecom_customer_display_label
from services.fiqa_api.wecom.intent import IntentResult, WeComIntent
from services.fiqa_api.wecom.lane_extractors import extract_claim_facts, extract_premium_facts

logger = logging.getLogger(__name__)

_MINIMAL_LANE_BY_INTENT: dict[WeComIntent, str] = {
    "policy_review": SERVICE_LANE_POLICY_REVIEW,
    "claim_intake": SERVICE_LANE_CLAIM_LITE,
}

WeComMinimalLaneOutcome = Literal[
    "skipped",
    "duplicate_msg",
    "created",
    "attached",
    "secondary_topic_deferred",
    "intent_not_actionable",
]

_DEMO_USER_PREFIX = "demo_chen_kui_"


def _log_event(event: str, payload: dict[str, Any]) -> None:
    logger.info("%s %s", event, json.dumps(payload, ensure_ascii=False))


def _pkt(value: str, *, source: str = "wecom_intake") -> dict[str, Any]:
    return {
        "value": value,
        "confidence": 1.0,
        "confidence_label": "high",
        "source_file": source,
        "is_mock": False,
    }


def find_open_minimal_lane_case_by_external_userid(
    external_userid: str,
    *,
    service_lane: str | None = None,
) -> str | None:
    """Find open Premium Review or Claim Lite case bound to this WeCom user."""
    ext = (external_userid or "").strip()
    if not ext:
        return None
    lanes = {service_lane} if service_lane else {SERVICE_LANE_POLICY_REVIEW, SERVICE_LANE_CLAIM_LITE}
    for case in list_all_cases_for_read():
        if case.get("wecom_external_userid") != ext:
            continue
        if case.get("case_status") == "closed":
            continue
        lane = str(case.get("service_lane") or "").strip()
        if lane not in lanes:
            continue
        cid = str(case.get("case_id") or "").strip()
        if cid:
            return cid
    return None


def find_open_add_car_case_by_external_userid(external_userid: str) -> str | None:
    """Return open add_car case id for One-Flow-at-a-Time guard."""
    ext = (external_userid or "").strip()
    if not ext:
        return None
    for case in list_all_cases_for_read():
        if case.get("wecom_external_userid") != ext:
            continue
        if case.get("case_status") == "closed":
            continue
        if case.get("service_lane") != "add_car":
            continue
        cid = str(case.get("case_id") or "").strip()
        if cid:
            return cid
    return None


def _is_demo_wecom_user(external_userid: str) -> bool:
    return (external_userid or "").strip().startswith(_DEMO_USER_PREFIX)


def _premium_tags(facts: dict[str, Any]) -> list[str]:
    tags = ["WeCom", "Manual Review", "Broker Review", "Price Sensitive", "Retention Risk"]
    usage = str(facts.get("usage") or "")
    if "uber" in usage.lower() or "tcp" in usage.lower():
        tags.extend(["Uber Black", "Commercial Driver"])
    premium = str(facts.get("premium_amount") or "")
    try:
        if premium and int(premium) >= 10000:
            tags.append("High Premium")
    except ValueError:
        pass
    return list(dict.fromkeys(tags))


def _claim_tags(facts: dict[str, Any]) -> list[str]:
    tags = ["WeCom", "Urgent", "Needs Fast Response", "Claim Active", "Manual Handle"]
    injury = str(facts.get("injury") or "")
    if injury and "none" not in injury.lower():
        tags.append("Injury")
    return list(dict.fromkeys(tags))


def _build_premium_p16_packet(
    *,
    facts: dict[str, Any],
    broker_next: str,
    customer_message: str,
) -> dict[str, Any]:
    packet: dict[str, Any] = {}
    if facts.get("premium_amount"):
        packet["premium_amount"] = _pkt(str(facts["premium_amount"]))
    if facts.get("carrier"):
        packet["current_carrier"] = _pkt(str(facts["carrier"]))
    if facts.get("zip"):
        packet["garaging_zip"] = _pkt(str(facts["zip"]))
    broker_action = {"en": broker_next, "zh": broker_next}
    portal = build_portal_copy_text_policy_review(
        packet=packet,
        vehicles=[],
        drivers=[],
        broker_next_action=broker_action,
    )
    return build_p16_broker_packet_blob(
        request_type="policy_review",
        readiness_status=map_policy_review_readiness("broker_review"),
        packet=packet,
        vehicles=[],
        drivers=[],
        copy_text=f"PREMIUM REVIEW (WeCom)\n{customer_message[:500]}",
        portal_copy_text=portal or f"Customer message: {customer_message[:300]}",
        broker_next_action=broker_action,
        follow_up_message_zh="",
        sources=[{"file": "wecom", "fields": "premium_review_minimal"}],
        warnings=["No auto-quote — broker manual review only"],
    )


def _build_claim_p16_packet(
    *,
    facts: dict[str, Any],
    broker_next: str,
    customer_message: str,
) -> dict[str, Any]:
    packet: dict[str, Any] = {}
    if facts.get("accident_time"):
        packet["accident_time"] = _pkt(str(facts["accident_time"]))
    if facts.get("location"):
        packet["accident_location"] = _pkt(str(facts["location"]))
    if facts.get("other_vehicle"):
        packet["other_vehicle"] = _pkt(str(facts["other_vehicle"]))
    if facts.get("injury"):
        packet["injury_status"] = _pkt(str(facts["injury"]))
    broker_action = {"en": broker_next, "zh": broker_next}
    summary = customer_message[:500]
    return build_p16_broker_packet_blob(
        request_type="claim_intake",
        readiness_status="BROKER_REVIEW",
        packet=packet,
        copy_text=f"CLAIM LITE (WeCom)\n{summary}",
        portal_copy_text=summary[:300],
        broker_next_action=broker_action,
        follow_up_message_zh="",
        sources=[{"file": "wecom", "fields": "claim_lite_minimal"}],
        warnings=["Urgent — broker call customer; no auto FNOL or claim advice"],
    )


def _build_premium_stub(text: str, extracted: dict[str, Any]) -> dict[str, Any]:
    facts = extracted["facts"]
    still_needed = list(extracted["still_needed"])
    collected = list(extracted["collected_keys"])
    broker_next = "陈总人工查看保单 / 回电 / 核对 renewal notice 与 dec page 后再给方案。"
    summary = "客户反映保费上涨或续保问题，希望人工查看是否有更合适方案。"
    if "太贵" in text or "涨价" in text or "too high" in text.lower():
        summary = "客户反映保费上涨，希望陈总人工查看。"
    return {
        "issue_category": "premium_review",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": broker_next,
        "client_prep": "请准备 renewal notice、declaration page、VIN 及近期理赔记录。",
        "client_reply_draft": "",
        "handoff_ready": False,
        "lifecycle_status": "handed_off",
        "collection_stage": "collecting",
        "service_type": "renewal_premium",
        "conversation_summary": summary,
        "demo_summary": summary,
        "collected_fields": collected,
        "still_needed_fields": still_needed,
        "quote_ready_status": "need_more",
        "workbench_tags": _premium_tags(facts),
        "risk_flags": [
            "price_sensitive",
            "retention_risk",
            "manual_review_required",
        ],
        "known_facts": {k: str(v) for k, v in facts.items() if v},
        "p16_broker_packet": _build_premium_p16_packet(
            facts=facts,
            broker_next=broker_next,
            customer_message=text,
        ),
    }


def _build_claim_stub(text: str, extracted: dict[str, Any]) -> dict[str, Any]:
    facts = extracted["facts"]
    still_needed = list(extracted["still_needed"])
    collected = list(extracted["collected_keys"])
    broker_next = "Broker call customer / Manual Handle — 收集对方信息、现场照片与 police report。"
    summary = "客户发生事故，询问下一步；需 broker 人工联系。"
    return {
        "issue_category": "claim_intake",
        "urgency": "critical",
        "manual_followup_needed": True,
        "broker_next_step": broker_next,
        "client_prep": "请先确保安全；如方便请拍照并记录对方信息。",
        "client_reply_draft": "",
        "handoff_ready": False,
        "lifecycle_status": "handed_off",
        "service_type": "claim_intake",
        "conversation_summary": summary,
        "demo_summary": summary,
        "collected_fields": collected,
        "still_needed_fields": still_needed,
        "quote_ready_status": "need_more",
        "workbench_tags": _claim_tags(facts),
        "risk_flags": [
            "urgent",
            "needs_fast_response",
            "manual_handle",
        ],
        "known_facts": {k: str(v) for k, v in facts.items() if v},
        "p16_broker_packet": _build_claim_p16_packet(
            facts=facts,
            broker_next=broker_next,
            customer_message=text,
        ),
    }


def _merge_intelligence(existing: dict[str, Any], stub: dict[str, Any]) -> None:
    """Merge workbench intelligence fields onto case dict before persist."""
    for key in ("workbench_tags", "known_facts", "risk_flags", "demo_summary", "p16_broker_packet"):
        if key in stub:
            if key == "known_facts":
                merged = dict(existing.get("known_facts") or {})
                merged.update(stub.get("known_facts") or {})
                existing[key] = merged
            elif key == "workbench_tags":
                merged = list(
                    dict.fromkeys([*(existing.get("workbench_tags") or []), *(stub.get("workbench_tags") or [])])
                )
                existing[key] = merged
            else:
                existing[key] = stub[key]
    if stub.get("conversation_summary"):
        existing["conversation_summary"] = stub["conversation_summary"]
    if stub.get("demo_summary"):
        existing["demo_summary"] = stub["demo_summary"]


def _finalize_case_intelligence(case_id: str, stub: dict[str, Any], *, external_userid: str) -> None:
    from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation

    case = _load_case_for_mutation(case_id)
    if case is None:
        _log_event("wecom_minimal_lane_persist_failed_v1", {"case_id": case_id, "reason": "case_not_found"})
        return
    _merge_intelligence(case, stub)
    case["client_id"] = case.get("client_id") or "chen_kui"
    if _is_demo_wecom_user(external_userid):
        case["workbench_test"] = True
    if not _persist_case_after_update(case_id, case):
        _log_event("wecom_minimal_lane_persist_failed_v1", {"case_id": case_id, "reason": "persist_failed"})


def ingest_wecom_text_to_minimal_lane(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> dict[str, Any]:
    """
    Create or update a Premium Review / Claim Lite minimal case from WeCom text.
    No phone required. No LLM/OCR/quote/claim filing.
    """
    msg_id = str(normalized.get("msg_id") or "").strip()
    text = str(normalized.get("text") or "").strip()
    external_userid = str(normalized.get("external_userid") or "").strip()
    intent = intent_result.intent

    if intent not in _MINIMAL_LANE_BY_INTENT or intent_result.confidence != "high":
        return {
            "outcome": "intent_not_actionable",
            "case_id": None,
            "case_created": False,
            "readiness_gate": None,
        }

    service_lane = _MINIMAL_LANE_BY_INTENT[intent]

    existing_by_msg = find_case_by_wecom_msg_id(msg_id)
    if existing_by_msg:
        return {
            "outcome": "duplicate_msg",
            "case_id": existing_by_msg,
            "case_created": False,
            "readiness_gate": "BROKER_REVIEW",
        }

    if find_open_add_car_case_by_external_userid(external_userid):
        _log_event(
            "wecom_minimal_lane_deferred_v1",
            {"msg_id": msg_id, "external_userid": external_userid, "reason": "active_add_car_flow"},
        )
        return {
            "outcome": "secondary_topic_deferred",
            "case_id": None,
            "case_created": False,
            "readiness_gate": "BROKER_REVIEW",
        }

    open_same_lane = find_open_minimal_lane_case_by_external_userid(
        external_userid, service_lane=service_lane
    )
    if open_same_lane and get_case_by_id(open_same_lane) is None:
        open_same_lane = None

    if intent == "policy_review":
        extracted = extract_premium_facts(text)
        stub = _build_premium_stub(text, extracted)
    else:
        extracted = extract_claim_facts(text)
        stub = _build_claim_stub(text, extracted)

    source_text = f"[客户] WeCom: {text or '(no text)'}"

    if open_same_lane:
        updated = append_follow_up_message(open_same_lane, text, stub)
        if updated is None:
            return {
                "outcome": "intent_not_actionable",
                "case_id": None,
                "case_created": False,
                "readiness_gate": None,
            }
        _record_wecom_evidence(open_same_lane, msg_id)
        _finalize_case_intelligence(open_same_lane, stub, external_userid=external_userid)
        _log_event(
            "wecom_minimal_lane_attached_v1",
            {"msg_id": msg_id, "case_id": open_same_lane, "lane": service_lane},
        )
        return {
            "outcome": "attached",
            "case_id": open_same_lane,
            "case_created": False,
            "readiness_gate": "BROKER_REVIEW",
            "service_lane": service_lane,
        }

    phone = extract_phone_from_text(text)
    saved = save_case(
        source_text,
        stub,
        status="reviewing",
        client_id="chen_kui",
        service_lane=service_lane,
    )
    case_id = str(saved.get("case_id") or "").strip()
    if case_id:
        display_name = wecom_customer_display_label(
            external_userid,
            customer_phone=phone or None,
        )
        from services.fiqa_api.inbox_triage.case_store import update_case_customer

        update_case_customer(case_id, customer_name=display_name)
        if phone:
            update_case_customer(case_id, customer_phone=phone)
        if external_userid:
            bind_case_channel_identity(
                case_id,
                wecom_external_userid=external_userid,
                wecom_open_kf_id=str(normalized.get("open_kf_id") or "").strip() or None,
            )
        _record_wecom_evidence(case_id, msg_id)
        _finalize_case_intelligence(case_id, stub, external_userid=external_userid)
        update_case_status(case_id, "reviewing")

    _log_event(
        "wecom_minimal_lane_created_v1",
        {"msg_id": msg_id, "case_id": case_id, "lane": service_lane},
    )
    return {
        "outcome": "created",
        "case_id": case_id or None,
        "case_created": True,
        "readiness_gate": "BROKER_REVIEW",
        "service_lane": service_lane,
    }
