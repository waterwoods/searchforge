"""P19D-4B — H5 photo flow WeCom End Card send tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import bind_case_channel_identity, get_case_by_id, save_case
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.h5_photo_end_card import try_send_h5_photo_flow_end_card


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


def _setup_json_store() -> None:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)


def _triage_stub() -> dict:
    return {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": "Review photos.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "extracted_contact_name": "陈女士",
    }


def _case_with_photos(*, insurance_skipped: bool = False) -> dict:
    saved = save_case("end card test", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(
        saved["case_id"],
        wecom_external_userid="wm_end_card_user",
        wecom_open_kf_id="wktest001",
    )
    case = get_case_by_id(saved["case_id"]) or saved
    atts = [
        {
            "attachment_id": "att_vin",
            "source": "h5_task",
            "slot_assignment": "vin_photo",
        },
        {
            "attachment_id": "att_reg",
            "source": "h5_task",
            "slot_assignment": "registration_photo",
        },
    ]
    if not insurance_skipped:
        atts.append(
            {
                "attachment_id": "att_ins",
                "source": "h5_task",
                "slot_assignment": "insurance_card_photo",
            }
        )
    from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation, _persist_case_after_update

    mut = _load_case_for_mutation(case["case_id"])
    assert mut is not None
    mut["case_attachments"] = atts
    if insurance_skipped:
        mut["h5_photo_flow_state"] = {"skipped_slots": ["insurance_card_photo"]}
    _persist_case_after_update(case["case_id"], mut)
    return get_case_by_id(case["case_id"]) or mut


def test_end_card_skipped_when_open_kf_id_missing(monkeypatch):
    """End Card requires both wecom_external_userid and wecom_open_kf_id."""
    _setup_json_store()
    saved = save_case("end card test", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(
        saved["case_id"],
        wecom_external_userid="wm_ext_only",
        wecom_open_kf_id=None,
    )
    from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation, _persist_case_after_update

    mut = _load_case_for_mutation(saved["case_id"])
    assert mut is not None
    mut["case_attachments"] = [
        {"attachment_id": "a1", "source": "h5_task", "slot_assignment": "vin_photo"},
        {"attachment_id": "a2", "source": "h5_task", "slot_assignment": "registration_photo"},
    ]
    _persist_case_after_update(saved["case_id"], mut)

    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    result = try_send_h5_photo_flow_end_card(saved["case_id"])
    assert result["sent"] is False
    assert result["reason"] == "no_wecom_channel_binding"


def test_end_card_send_with_mock(monkeypatch):
    _setup_json_store()
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    load_wecom_kf_config.cache_clear()

    case = _case_with_photos()
    sent_content: list[str] = []

    def fake_send(cfg, *, external_userid, open_kf_id, content):
        sent_content.append(content)
        return {"errcode": 0}

    monkeypatch.setattr(
        "services.fiqa_api.wecom.h5_photo_end_card.send_text_reply",
        fake_send,
    )

    r1 = try_send_h5_photo_flow_end_card(case["case_id"])
    assert r1["sent"] is True
    assert len(sent_content) == 1
    assert "✓ VIN 照片" in sent_content[0]
    assert "提车日期" in sent_content[0]

    r2 = try_send_h5_photo_flow_end_card(case["case_id"])
    assert r2.get("deduped") is True
    assert len(sent_content) == 1


def test_end_card_send_failure_does_not_mark_sent(monkeypatch):
    _setup_json_store()
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    load_wecom_kf_config.cache_clear()

    case = _case_with_photos()

    def boom(*_a, **_k):
        raise RuntimeError("network")

    monkeypatch.setattr(
        "services.fiqa_api.wecom.h5_photo_end_card.send_text_reply",
        boom,
    )

    r = try_send_h5_photo_flow_end_card(case["case_id"])
    assert r["sent"] is False
    assert r["reason"] == "send_failed"
    updated = get_case_by_id(case["case_id"])
    state = (updated or {}).get("h5_photo_flow_state") or {}
    assert not state.get("end_card_sent_at")
    assert state.get("end_card_send_status") == "failed"
