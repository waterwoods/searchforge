"""P19E-1 debug — Phase 2 routing must use Postgres read facade, not JSON-only get_case_by_id."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.add_vehicle_phase2 import (
    find_phase2_eligible_add_car_case,
    ingest_phase2_text_collection,
    resolve_add_car_case_for_phase2,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event


@pytest.fixture(autouse=True)
def _json_store():
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


def _photo_complete_case(*, case_id: str = "case_pg_only", ext: str = "wm_andy") -> dict:
    return {
        "case_id": case_id,
        "case_status": "new",
        "service_lane": SERVICE_LANE_ADD_CAR,
        "wecom_external_userid": ext,
        "wecom_open_kf_id": "wktest001",
        "collected_fields": [],
        "still_needed_fields": ["delivery_date", "zip", "phone"],
        "case_attachments": [
            {"source": "h5_task", "slot_assignment": "vin_photo"},
            {"source": "h5_task", "slot_assignment": "registration_photo"},
            {"source": "h5_task", "slot_assignment": "insurance_card_photo"},
        ],
        "h5_photo_flow_state": {"end_card_sent_at": "2026-07-07T01:14:01Z"},
    }


def test_andy_message_extracts_all_three_fields():
    from services.fiqa_api.wecom.identity import (
        extract_delivery_date_from_text,
        extract_phone_from_text,
        extract_zip_from_text,
    )

    text = "7月10号提车，zip. 92705。电话2031234567"
    assert extract_delivery_date_from_text(text) == "7月10日"
    assert extract_zip_from_text(text) == "92705"
    assert extract_phone_from_text(text) == "2031234567"


def test_resolve_add_car_case_when_json_get_misses_pg_row():
    pg_case = _photo_complete_case()
    with patch(
        "services.fiqa_api.wecom.add_vehicle_phase2.get_case_for_read",
        return_value=None,
    ), patch(
        "services.fiqa_api.wecom.add_vehicle_phase2.list_all_cases_for_read",
        return_value=[pg_case],
    ):
        cid, case = resolve_add_car_case_for_phase2(
            bound_case_id="case_pg_only",
            bound_case=None,
            external_userid="wm_andy",
        )
    assert cid == "case_pg_only"
    assert case is pg_case


def test_find_phase2_eligible_skips_photo_incomplete():
    incomplete = _photo_complete_case()
    incomplete["case_attachments"] = []
    complete = _photo_complete_case(case_id="case_done")
    with patch(
        "services.fiqa_api.wecom.add_vehicle_phase2.list_all_cases_for_read",
        return_value=[incomplete, complete],
    ):
        found = find_phase2_eligible_add_car_case("wm_andy")
    assert found is not None
    assert found["case_id"] == "case_done"


def test_slice_routes_phase2_not_greeting_when_pg_case_only(monkeypatch):
    pg_case = _photo_complete_case()
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()
    reset_message_processed_memory_for_tests()
    reset_reply_dedup_memory_for_tests()
    captured: dict = {}

    def fake_send_text_reply(_cfg, *, external_userid, open_kf_id, content):
        captured["text"] = content

    text = "7月10号提车，zip. 92705。电话2031234567"
    updated_case = {
        **pg_case,
        "collected_fields": ["delivery_date", "zip", "phone"],
        "still_needed_fields": [],
        "known_facts": {
            "delivery_date": "7月10日",
            "zip": "92705",
            "phone": "2031234567",
        },
    }
    with patch(
        "services.fiqa_api.wecom.slice.find_open_draft_case_by_external_userid",
        return_value="case_pg_only",
    ), patch(
        "services.fiqa_api.wecom.add_vehicle_phase2.find_case_by_wecom_msg_id",
        return_value=None,
        ), patch(
        "services.fiqa_api.wecom.slice.get_case_for_read",
        side_effect=[pg_case, updated_case, updated_case],
    ), patch(
        "services.fiqa_api.wecom.add_vehicle_phase2.get_case_for_read",
        side_effect=[pg_case, updated_case, updated_case, updated_case],
    ), patch(
        "services.fiqa_api.wecom.add_vehicle_phase2.append_follow_up_message",
        return_value=updated_case,
    ), patch(
        "services.fiqa_api.wecom.add_vehicle_phase2.update_add_vehicle_workflow_state",
        return_value=pg_case,
    ), patch(
        "services.fiqa_api.wecom.active_case_bridge._record_wecom_evidence",
        return_value=None,
    ), patch(
        "services.fiqa_api.wecom.slice.send_text_reply",
        side_effect=fake_send_text_reply,
    ):
        outcomes = process_kf_msg_or_event(
            cfg,
            callback_token="tok",
            open_kf_id="wktest001",
            pull_messages=lambda *_a, **_k: [
                {
                    "msgid": "m_phase2_andy",
                    "msgtype": "text",
                    "text": {"content": text},
                    "external_userid": "wm_andy",
                    "open_kfid": "wktest001",
                }
            ],
        )

    assert outcomes[0]["active_case_outcome"] == "phase2_complete_s2_sent"
    assert "第 2 阶段完成" in captured.get("text", "")
    assert "请选择您要办理的事项" not in captured.get("text", "")


def test_phase2_unrecognized_text_gets_format_hint():
    case = _photo_complete_case()
    with patch(
        "services.fiqa_api.wecom.add_vehicle_phase2.get_case_for_read",
        return_value=case,
    ):
        result = ingest_phase2_text_collection(
            {"msg_id": "m_nofields", "text": "谢谢陈总"},
            "case_pg_only",
        )
    assert result["active_case_outcome"] == "phase2_unrecognized_fields"
    assert "还没有识别到" in (result.get("reply_text") or "")


def test_stale_binding_without_read_facade_routes_to_greeting(monkeypatch):
    """Documents live bug: binding id from Postgres but JSON get_case_by_id misses row."""
    pg_case = _photo_complete_case()
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()
    reset_message_processed_memory_for_tests()
    reset_reply_dedup_memory_for_tests()
    text = "7月10号提车，zip. 92705。电话2031234567"

    with patch(
        "services.fiqa_api.wecom.slice.find_open_draft_case_by_external_userid",
        return_value="case_pg_only",
    ), patch(
        "services.fiqa_api.wecom.slice.get_case_for_read",
        return_value=None,
    ), patch(
        "services.fiqa_api.wecom.add_vehicle_phase2.list_all_cases_for_read",
        return_value=[],
    ):
        outcomes = process_kf_msg_or_event(
            cfg,
            callback_token="tok",
            open_kf_id="wktest001",
            pull_messages=lambda *_a, **_k: [
                {
                    "msgid": "m_bug_repro",
                    "msgtype": "text",
                    "text": {"content": text},
                    "external_userid": "wm_andy",
                    "open_kfid": "wktest001",
                }
            ],
        )
    assert outcomes[0]["guided_menu_required"] is True
    assert outcomes[0]["active_case_outcome"] == "intent_not_actionable"


def test_hello_unchanged_without_active_phase2_case(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()
    reset_message_processed_memory_for_tests()
    reset_reply_dedup_memory_for_tests()

    with patch(
        "services.fiqa_api.wecom.slice.find_open_draft_case_by_external_userid",
        return_value=None,
    ), patch(
        "services.fiqa_api.wecom.add_vehicle_phase2.list_all_cases_for_read",
        return_value=[],
    ):
        outcomes = process_kf_msg_or_event(
            cfg,
            callback_token="tok",
            open_kf_id="wktest001",
            pull_messages=lambda *_a, **_k: [
                {
                    "msgid": "m_hello_only",
                    "msgtype": "text",
                    "text": {"content": "你好"},
                    "external_userid": "wm_new_user",
                    "open_kfid": "wktest001",
                }
            ],
        )
    assert outcomes[0]["guided_menu_required"] is True
    assert "intent_not_actionable" in str(outcomes[0].get("active_case_outcome", ""))
