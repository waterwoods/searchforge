"""Postgres extra bag — WeCom channel binding round-trip."""

from __future__ import annotations

from services.fiqa_api.db.service_record_repository import (
    _build_extra,
    _hydrate_extra_pilot_fields,
)


def test_build_extra_includes_wecom_open_kf_id_and_h5_state():
    case = {
        "wecom_external_userid": "wm_test_user",
        "wecom_open_kf_id": "wktest001",
        "h5_photo_flow_state": {"end_card_send_status": "pending"},
    }
    extra = _build_extra(case)
    assert extra["wecom_open_kf_id"] == "wktest001"
    assert extra["h5_photo_flow_state"]["end_card_send_status"] == "pending"


def test_build_extra_includes_phase2_workflow_fields():
    case = {
        "guided_workflow_state": "ready_for_broker_review",
        "add_vehicle_phase": "phase_3_broker_review",
        "h5_photo_flow_state": {"s2_stage_complete_sent_at": "2026-07-07T01:14:46Z"},
    }
    extra = _build_extra(case)
    assert extra["guided_workflow_state"] == "ready_for_broker_review"
    assert extra["add_vehicle_phase"] == "phase_3_broker_review"
    assert extra["h5_photo_flow_state"]["s2_stage_complete_sent_at"]


def test_hydrate_extra_restores_phase2_workflow_fields():
    case: dict = {}
    _hydrate_extra_pilot_fields(
        case,
        {
            "guided_workflow_state": "collecting_text_fields",
            "add_vehicle_phase": "phase_2_text_in_progress",
            "h5_photo_flow_state": {"end_card_sent_at": "2026-07-07T01:14:01Z"},
        },
    )
    assert case["guided_workflow_state"] == "collecting_text_fields"
    assert case["add_vehicle_phase"] == "phase_2_text_in_progress"
    assert case["h5_photo_flow_state"]["end_card_sent_at"] == "2026-07-07T01:14:01Z"


def test_build_extra_includes_claim_attachment_slots():
    case = {
        "claim_attachment_slots": {
            "customer_damage_photo": {
                "status": "received",
                "source_channel": "h5_task",
                "latest_attachment_id": "att_test",
            }
        }
    }
    extra = _build_extra(case)
    assert extra["claim_attachment_slots"]["customer_damage_photo"]["status"] == "received"


def test_hydrate_extra_restores_claim_attachment_slots():
    case: dict = {}
    _hydrate_extra_pilot_fields(
        case,
        {
            "claim_attachment_slots": {
                "other_party_vehicle_photo": {
                    "status": "skipped",
                    "skip_reason": "not_available",
                }
            }
        },
    )
    assert case["claim_attachment_slots"]["other_party_vehicle_photo"]["status"] == "skipped"


def test_hydrate_extra_restores_wecom_open_kf_id_and_h5_state():
    case: dict = {}
    _hydrate_extra_pilot_fields(
        case,
        {
            "wecom_external_userid": "wm_hydrate",
            "wecom_open_kf_id": "wk_hydrate",
            "h5_photo_flow_state": {"skipped_slots": ["insurance_card_photo"]},
        },
    )
    assert case["wecom_open_kf_id"] == "wk_hydrate"
    assert case["h5_photo_flow_state"]["skipped_slots"] == ["insurance_card_photo"]
