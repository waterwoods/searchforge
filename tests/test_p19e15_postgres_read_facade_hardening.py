"""P19E-1.5 — production case reads must use Postgres read facade, not JSON-only get_case_by_id."""

from __future__ import annotations

import ast
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from services.fiqa_api.inbox_triage.intake_service_lanes import (
    SERVICE_LANE_ADD_CAR,
    SERVICE_LANE_CLAIM_LITE,
    SERVICE_LANE_POLICY_REVIEW,
)
from services.fiqa_api.wecom.active_case_bridge import ingest_wecom_text_to_draft_case
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.h5_photo_end_card import try_send_h5_photo_flow_end_card
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.minimal_lanes import ingest_wecom_text_to_minimal_lane
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

_WECOM_PRODUCTION_MODULES = (
    "services/fiqa_api/wecom/slice.py",
    "services/fiqa_api/wecom/active_case_bridge.py",
    "services/fiqa_api/wecom/add_vehicle_phase2.py",
    "services/fiqa_api/wecom/h5_photo_end_card.py",
    "services/fiqa_api/wecom/media_intake.py",
    "services/fiqa_api/wecom/minimal_lanes.py",
)


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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _pg_add_car_case(
    *,
    case_id: str = "case_pg_only",
    ext: str = "wm_pg_user",
    open_kf: str = "wktest001",
) -> dict:
    return {
        "case_id": case_id,
        "case_status": "new",
        "service_lane": SERVICE_LANE_ADD_CAR,
        "wecom_external_userid": ext,
        "wecom_open_kf_id": open_kf,
        "collected_fields": ["vin"],
        "still_needed_fields": ["zip", "phone"],
        "known_facts": {"vin": "1HGCM82633A123456"},
        "case_attachments": [
            {"source": "h5_task", "slot_assignment": "vin_photo"},
            {"source": "h5_task", "slot_assignment": "registration_photo"},
            {"source": "h5_task", "slot_assignment": "insurance_card_photo"},
        ],
        "h5_photo_flow_state": {"end_card_sent_at": "2026-07-07T01:14:01Z"},
    }


def test_production_wecom_modules_do_not_call_get_case_by_id():
    """Guardrail: WeCom routing modules must not invoke JSON-only get_case_by_id."""
    offenders: list[str] = []
    for rel in _WECOM_PRODUCTION_MODULES:
        path = _repo_root() / rel
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "get_case_by_id":
                    offenders.append(f"{rel}:{node.lineno}")
    assert offenders == [], f"JSON-only get_case_by_id in production WeCom: {offenders}"


def test_draft_ingest_hydrates_from_postgres_when_json_misses():
    pg_case = _pg_add_car_case()
    with patch(
        "services.fiqa_api.inbox_triage.case_store.get_case_by_id",
        return_value=None,
    ), patch(
        "services.fiqa_api.wecom.active_case_bridge.get_case_for_read",
        return_value=pg_case,
    ), patch(
        "services.fiqa_api.wecom.active_case_bridge.append_follow_up_message",
        return_value={**pg_case, "collected_fields": ["vin", "zip"]},
    ) as append_mock:
        result = ingest_wecom_text_to_draft_case(
            {"msg_id": "m_draft", "text": "zip 92705"},
            "case_pg_only",
        )
    assert result["outcome"] != "case_not_found"
    append_mock.assert_called_once()


def test_media_intake_reads_lane_from_postgres_when_json_misses():
    pg_case = {
        "case_id": "case_media",
        "service_lane": SERVICE_LANE_POLICY_REVIEW,
        "wecom_external_userid": "wm_media",
    }
    with patch(
        "services.fiqa_api.inbox_triage.case_store.get_case_by_id",
        return_value=None,
    ), patch(
        "services.fiqa_api.wecom.media_intake.get_case_for_read",
        return_value=pg_case,
    ), patch(
        "services.fiqa_api.wecom.media_intake.find_wecom_attachment_by_msg_id",
        return_value=("case_media", {"attachment_id": "att_dup", "binding_confidence": "high"}),
    ):
        result = ingest_wecom_media_message(
            {"msg_id": "m_dup", "msgtype": "image", "media_id": "mid", "external_userid": "wm_media"},
            cfg=None,
        )
    assert result["outcome"] == "duplicate_msg"
    assert result["case_id"] == "case_media"


def test_minimal_lane_continues_when_json_misses_but_postgres_has_case(monkeypatch):
    pg_case = {
        "case_id": "case_premium",
        "case_status": "new",
        "service_lane": SERVICE_LANE_POLICY_REVIEW,
        "wecom_external_userid": "wm_premium",
        "collected_fields": [],
        "still_needed_fields": [],
    }
    intent = type(
        "Intent",
        (),
        {"intent": "policy_review", "confidence": "high", "matched_by": "keyword"},
    )()
    with patch(
        "services.fiqa_api.inbox_triage.case_store.get_case_by_id",
        return_value=None,
    ), patch(
        "services.fiqa_api.wecom.minimal_lanes.get_case_for_read",
        return_value=pg_case,
    ), patch(
        "services.fiqa_api.wecom.minimal_lanes.find_open_minimal_lane_case_by_external_userid",
        return_value="case_premium",
    ), patch(
        "services.fiqa_api.wecom.minimal_lanes.append_follow_up_message",
        return_value=pg_case,
    ):
        result = ingest_wecom_text_to_minimal_lane(
            {"msg_id": "m_prem", "text": "续保报价", "external_userid": "wm_premium"},
            intent,
        )
    assert result.get("outcome") != "secondary_topic_deferred"
    assert result.get("case_id") == "case_premium"


def test_end_card_reads_wecom_binding_from_postgres_extra(monkeypatch):
    pg_case = _pg_add_car_case()
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    load_wecom_kf_config.cache_clear()
    sent: dict = {}

    def fake_send(_cfg, *, external_userid, open_kf_id, content):
        sent["external_userid"] = external_userid
        sent["open_kf_id"] = open_kf_id
        sent["content"] = content

    fresh = {**pg_case, "h5_photo_flow_state": {}}
    with patch(
        "services.fiqa_api.inbox_triage.case_store.get_case_by_id",
        return_value=None,
    ), patch(
        "services.fiqa_api.wecom.h5_photo_end_card.get_case_for_read",
        return_value=fresh,
    ), patch(
        "services.fiqa_api.wecom.h5_photo_end_card.send_text_reply",
        side_effect=fake_send,
    ), patch(
        "services.fiqa_api.wecom.h5_photo_end_card.record_h5_photo_flow_end_card_status",
    ):
        result = try_send_h5_photo_flow_end_card("case_pg_only")
    assert result.get("sent") is True
    assert sent["open_kf_id"] == "wktest001"
    assert sent["external_userid"] == "wm_pg_user"


def test_completed_photo_followup_from_postgres_not_greeting(monkeypatch):
    pg_case = _pg_add_car_case()
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

    def fake_send(_cfg, *, external_userid, open_kf_id, content):
        captured["text"] = content

    with patch(
        "services.fiqa_api.inbox_triage.case_store.get_case_by_id",
        return_value=None,
    ), patch(
        "services.fiqa_api.wecom.slice.find_open_draft_case_by_external_userid",
        return_value="case_pg_only",
    ), patch(
        "services.fiqa_api.wecom.slice.get_case_for_read",
        return_value=pg_case,
    ), patch(
        "services.fiqa_api.wecom.slice.try_send_h5_photo_flow_end_card",
        return_value={"sent": False, "reason": "already_sent"},
    ), patch(
        "services.fiqa_api.wecom.slice.send_text_reply",
        side_effect=fake_send,
    ):
        outcomes = process_kf_msg_or_event(
            cfg,
            callback_token="tok",
            open_kf_id="wktest001",
            pull_messages=lambda *_a, **_k: [
                {
                    "msgid": "m_followup",
                    "msgtype": "text",
                    "text": {"content": "照片都传好了"},
                    "external_userid": "wm_pg_user",
                    "open_kfid": "wktest001",
                }
            ],
        )
    assert "请选择您要办理的事项" not in captured.get("text", "")
    assert outcomes[0].get("guided_menu_required") is not True


def test_binding_not_cleared_when_legacy_json_misses_but_postgres_hydrates(monkeypatch):
    pg_case = _pg_add_car_case()
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()
    reset_message_processed_memory_for_tests()
    stale_logs: list[str] = []

    def capture_log(event, payload):
        if event == "stale_draft_binding_cleared_v1":
            stale_logs.append(payload.get("stale_case_id", ""))

    with patch(
        "services.fiqa_api.inbox_triage.case_store.get_case_by_id",
        return_value=None,
    ), patch(
        "services.fiqa_api.wecom.slice.find_open_draft_case_by_external_userid",
        return_value="case_pg_only",
    ), patch(
        "services.fiqa_api.wecom.slice.get_case_for_read",
        return_value=pg_case,
    ), patch(
        "services.fiqa_api.wecom.add_vehicle_phase2.ingest_phase2_text_collection",
        return_value={"active_case_outcome": "phase2_fields_collected", "case_id": "case_pg_only"},
    ), patch(
        "services.fiqa_api.wecom.slice._log_slice",
        side_effect=capture_log,
    ):
        outcomes = process_kf_msg_or_event(
            cfg,
            callback_token="tok",
            open_kf_id="wktest001",
            pull_messages=lambda *_a, **_k: [
                {
                    "msgid": "m_bind",
                    "msgtype": "text",
                    "text": {"content": "zip 92705 电话2031234567"},
                    "external_userid": "wm_pg_user",
                    "open_kfid": "wktest001",
                }
            ],
        )
    assert stale_logs == []
    assert outcomes[0].get("case_id") == "case_pg_only"


def test_hello_without_active_case_still_shows_menu(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()
    reset_message_processed_memory_for_tests()

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
                    "msgid": "m_hello",
                    "msgtype": "text",
                    "text": {"content": "你好"},
                    "external_userid": "wm_new",
                    "open_kfid": "wktest001",
                }
            ],
        )
    assert outcomes[0]["guided_menu_required"] is True


def test_claim_lane_not_regressed_when_json_misses_postgres_has_case():
    pg_case = {
        "case_id": "case_claim",
        "case_status": "new",
        "service_lane": SERVICE_LANE_CLAIM_LITE,
        "wecom_external_userid": "wm_claim",
        "collected_fields": [],
        "still_needed_fields": [],
    }
    intent = type(
        "Intent",
        (),
        {"intent": "claim_intake", "confidence": "high", "matched_by": "keyword"},
    )()
    with patch(
        "services.fiqa_api.inbox_triage.case_store.get_case_by_id",
        return_value=None,
    ), patch(
        "services.fiqa_api.wecom.minimal_lanes.get_case_for_read",
        return_value=pg_case,
    ), patch(
        "services.fiqa_api.wecom.minimal_lanes.find_open_minimal_lane_case_by_external_userid",
        return_value="case_claim",
    ), patch(
        "services.fiqa_api.wecom.minimal_lanes.append_follow_up_message",
        return_value=pg_case,
    ):
        result = ingest_wecom_text_to_minimal_lane(
            {"msg_id": "m_claim", "text": "出险了", "external_userid": "wm_claim"},
            intent,
        )
    assert result.get("service_lane") == SERVICE_LANE_CLAIM_LITE or result.get("case_id") == "case_claim"
