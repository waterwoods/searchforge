"""P19H-3c-3A — Claim evidence checklist backend summary tests."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.claim_workbench_display import (
    build_claim_evidence_summary,
    claim_evidence_copy_is_broker_safe,
    enrich_claim_for_workbench,
)
from services.fiqa_api.inbox_triage.h5_task_token import FLOW_CLAIM_EVIDENCE_PACK
from services.fiqa_api.inbox_triage.workbench_enrichment import enrich_cases_for_workbench
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)

_FORBIDDEN_PHRASES = (
    "已报案",
    "claim 已正式提交",
    "已联系保险公司",
    "是对方责任",
    "一定会赔",
)


def _claim_case(**overrides: object) -> dict:
    base: dict = {
        "case_id": "case_claim_evidence",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        "known_facts": {
            "accident_datetime": "今天上午10点",
            "accident_location": "Irvine Blvd",
            "accident_description": "刮蹭",
        },
        "collected_fields": [
            "accident_datetime",
            "accident_location",
            "accident_description",
        ],
        "case_attachments": [],
        "claim_attachment_slots": {},
    }
    base.update(overrides)
    return base


def _h5_claim_attachment(
    *,
    slot: str,
    attachment_id: str = "att_h5_damage",
    filename: str = "damage.jpg",
) -> dict:
    return {
        "attachment_id": attachment_id,
        "source": "h5_task",
        "flow": FLOW_CLAIM_EVIDENCE_PACK,
        "slot_assignment": slot,
        "filename": filename,
        "mime_type": "image/jpeg",
        "received_at": "2026-07-09T18:00:00+00:00",
        "eligible_for_ocr": False,
    }


def _assert_forbidden_copy_absent(summary: dict) -> None:
    for field in ("summary_text", "broker_next_action"):
        text = str(summary.get(field) or "")
        assert claim_evidence_copy_is_broker_safe(text)
        for phrase in _FORBIDDEN_PHRASES:
            assert phrase not in text


def test_01_empty_claim_evidence():
    summary = build_claim_evidence_summary(_claim_case())

    assert len(summary["slots"]) == 3
    by_key = {s["slot_key"]: s for s in summary["slots"]}
    assert by_key["customer_damage_photo"]["status"] == "missing"
    assert by_key["other_party_vehicle_photo"]["status"] == "missing"
    assert by_key["scene_photo"]["status"] == "missing"
    assert summary["missing_required_slots"] == ["customer_damage_photo"]
    assert summary["missing_soft_required_slots"] == ["other_party_vehicle_photo"]
    assert summary["completion_level"] == "empty"
    assert "自己车损照片" in summary["broker_next_action"]
    _assert_forbidden_copy_absent(summary)


def test_02_h5_customer_damage_photo_received():
    summary = build_claim_evidence_summary(
        _claim_case(
            case_attachments=[
                _h5_claim_attachment(slot="customer_damage_photo"),
            ]
        )
    )
    by_key = {s["slot_key"]: s for s in summary["slots"]}
    customer = by_key["customer_damage_photo"]

    assert customer["status"] == "received"
    assert customer["attachment_count"] == 1
    assert customer["source_channel"] == "h5_task"
    assert customer["latest_attachment"] is not None
    assert customer["latest_attachment"]["attachment_id"] == "att_h5_damage"
    assert customer["latest_attachment"]["filename"] == "damage.jpg"
    assert "customer_damage_photo" not in summary["missing_required_slots"]
    assert summary["missing_soft_required_slots"] == ["other_party_vehicle_photo"]
    assert summary["completion_level"] == "required_complete"
    assert "对方车辆" in summary["broker_next_action"] or "车牌" in summary["broker_next_action"]
    _assert_forbidden_copy_absent(summary)


def test_03_other_party_skipped():
    summary = build_claim_evidence_summary(
        _claim_case(
            case_attachments=[
                _h5_claim_attachment(slot="customer_damage_photo"),
            ],
            claim_attachment_slots={
                "other_party_vehicle_photo": {
                    "status": "skipped",
                    "skip_reason": "not_available",
                }
            },
        )
    )
    by_key = {s["slot_key"]: s for s in summary["slots"]}
    other_party = by_key["other_party_vehicle_photo"]

    assert other_party["status"] == "skipped"
    assert other_party["skip_reason"] == "not_available"
    assert summary["missing_soft_required_slots"] == []
    assert summary["completion_level"] == "review_ready"
    assert "陈总" in summary["broker_next_action"] or "资料基本够" in summary["broker_next_action"]
    _assert_forbidden_copy_absent(summary)


def test_04_scene_optional_missing_does_not_block():
    summary = build_claim_evidence_summary(
        _claim_case(
            case_attachments=[
                _h5_claim_attachment(slot="customer_damage_photo"),
                _h5_claim_attachment(
                    slot="other_party_vehicle_photo",
                    attachment_id="att_other",
                    filename="other.jpg",
                ),
            ]
        )
    )
    by_key = {s["slot_key"]: s for s in summary["slots"]}

    assert by_key["scene_photo"]["status"] == "missing"
    assert summary["missing_required_slots"] == []
    assert summary["missing_soft_required_slots"] == []
    assert summary["completion_level"] == "review_ready"
    assert "现场照片" not in summary["broker_next_action"] or "可选" in summary["broker_next_action"]
    assert "现场照片可选" in summary["summary_text"] or "可选" in summary["summary_text"]
    _assert_forbidden_copy_absent(summary)


def test_05_needs_retake_priority():
    summary = build_claim_evidence_summary(
        _claim_case(
            case_attachments=[
                _h5_claim_attachment(slot="customer_damage_photo"),
            ],
            claim_attachment_slots={
                "customer_damage_photo": {
                    "status": "needs_retake",
                    "skip_reason": "blurry",
                }
            },
        )
    )
    by_key = {s["slot_key"]: s for s in summary["slots"]}
    customer = by_key["customer_damage_photo"]

    assert customer["status"] == "needs_retake"
    assert customer["needs_broker_review"] is True
    assert "重新上传" in summary["broker_next_action"]
    _assert_forbidden_copy_absent(summary)


def test_06_exclude_add_vehicle_attachments():
    summary = build_claim_evidence_summary(
        _claim_case(
            case_attachments=[
                {
                    "attachment_id": "att_vin",
                    "source": "h5_task",
                    "flow": "add_vehicle_photo_flow",
                    "slot_assignment": "vin_photo",
                    "filename": "vin.jpg",
                    "mime_type": "image/jpeg",
                    "received_at": "2026-07-09T17:00:00+00:00",
                },
                _h5_claim_attachment(slot="customer_damage_photo"),
            ]
        )
    )
    by_key = {s["slot_key"]: s for s in summary["slots"]}

    assert by_key["customer_damage_photo"]["status"] == "received"
    assert by_key["customer_damage_photo"]["attachment_count"] == 1
    assert "vin_photo" not in {s["slot_key"] for s in summary["slots"] if s["status"] == "received" and s["slot_key"] != "customer_damage_photo"}


def test_07_enrichment_includes_claim_evidence_summary():
    case = enrich_claim_for_workbench(_claim_case())
    assert case["claim_evidence_summary"] is not None
    assert case["display_title"] == "理赔资料"
    assert case["claim_summary"] is not None
    assert case["workbench_visible"] is True

    enriched = enrich_cases_for_workbench([_claim_case()])[0]
    assert enriched["claim_evidence_summary"]["completion_level"] == "empty"
    assert enriched["workbench_lane_kind"] == "explicit"


def test_08_forbidden_copy_absent():
    scenarios = [
        _claim_case(),
        _claim_case(case_attachments=[_h5_claim_attachment(slot="customer_damage_photo")]),
        _claim_case(
            case_attachments=[
                _h5_claim_attachment(slot="customer_damage_photo"),
                _h5_claim_attachment(slot="other_party_vehicle_photo", attachment_id="att2"),
            ]
        ),
    ]
    for case in scenarios:
        summary = build_claim_evidence_summary(case)
        _assert_forbidden_copy_absent(summary)
