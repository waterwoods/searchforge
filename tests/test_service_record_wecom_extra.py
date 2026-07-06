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
