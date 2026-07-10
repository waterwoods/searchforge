"""P19H-3j — H5 vs WeCom channel UX policy tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    patch_case_known_facts,
    save_case,
    update_claim_workflow_state,
    update_case_h5_intake_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.channel_ux_policy import (
    SupplementH5CtaKind,
    build_claim_media_supplement_ack,
    build_claim_supplement_received_reply,
    resolve_supplement_h5_cta,
)
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_status_request,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

_LEGACY_FALLBACK_MARKERS = (
    "Chen Kui's team has received your request",
    "陈奎团队已收到您的请求",
)


@pytest.fixture(autouse=True)
def _json_store(monkeypatch):
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://example.test")
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    load_wecom_kf_config.cache_clear()
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)
    load_wecom_kf_config.cache_clear()


def _normalized(text: str, *, ext: str, msg_id: str) -> dict:
    return normalize_text_message(
        {
            "msgid": msg_id,
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "text": {"content": text},
        }
    )


def _claim_stub() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Broker review.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": True,
        "claim_phase": CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    }


def _submitted_claim(*, ext: str) -> dict:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    patch_case_known_facts(
        cid,
        {
            "injury_status": "no",
            "accident_datetime": "7月8日",
            "accident_location": "Santa Ana",
            "accident_description": "后车追尾，对方变道刮到我左前门。",
            "own_vehicle_info": "Toyota Camry",
        },
    )
    update_claim_workflow_state(
        cid,
        claim_phase=CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
        guided_workflow_state="ready_for_broker_review",
    )
    update_case_h5_intake_state(
        cid,
        {"submitted_at": "2026-07-10T12:00:00+00:00", "submitted": True},
    )
    return get_case_by_id(cid) or saved


def _open_claim_missing_basics(*, ext: str) -> dict:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    update_claim_workflow_state(
        cid,
        claim_phase=CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        guided_workflow_state="collecting_text",
    )
    return get_case_by_id(cid) or saved


def _ready_not_submitted_claim(*, ext: str) -> dict:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    patch_case_known_facts(
        cid,
        {
            "anyone_injured": "no",
            "injury_status": "no",
            "accident_datetime": "7月8日上午10点",
            "accident_location": "Irvine Blvd",
            "accident_description": "对方变道刮到我左前门，已靠边停车。",
            "own_vehicle_info": "Toyota Camry 2020",
        },
    )
    update_claim_workflow_state(
        cid,
        claim_phase=CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        guided_workflow_state="collecting_text",
    )
    return get_case_by_id(cid) or saved


def _photo_complete_add_car(*, ext: str) -> dict:
    from services.fiqa_api.inbox_triage.case_store import append_h5_gcs_attachment_metadata

    saved = save_case(
        "add car",
        {
            "issue_category": "add_car_quote",
            "urgency": "medium",
            "manual_followup_needed": True,
            "broker_next_step": "Review.",
            "client_prep": "",
            "client_reply_draft": "",
            "still_needed_fields": ["delivery_date", "zip", "phone"],
            "collected_fields": [],
        },
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
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
    case["h5_photo_flow_state"] = {"end_card_sent_at": "2026-07-10T12:00:00+00:00"}
    return case


def _fake_download(_cfg, **kwargs):
    return WeComMediaDownloadResult(
        content=b"fake-image-bytes",
        content_type="image/jpeg",
        filename="photo.jpg",
    )


def _fake_upload(**kwargs):
    return {
        "storage_uri": "gs://test-bucket/wecom/photo.jpg",
        "mime_type": "image/jpeg",
        "filename": "photo.jpg",
    }


def _ingest_photo(*, ext: str, msg_id: str = "img_photo") -> dict:
    cfg = load_wecom_kf_config()
    norm = normalize_media_message(
        {
            "msgid": msg_id,
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "image",
            "image": {"media_id": f"mid_{msg_id}"},
        }
    )
    return ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)


def _assert_no_legacy(reply: str) -> None:
    for marker in _LEGACY_FALLBACK_MARKERS:
        assert marker not in reply


def _run_slice(text: str, *, ext: str, msg_id: str, monkeypatch) -> dict:
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "0")
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()

    def pull(_cfg, *, token, open_kf_id):
        return [
            {
                "msgid": msg_id,
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": text},
            }
        ]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    assert results
    return results[0]


# --- Explicit H5 request ---


def test_submitted_claim_progress_returns_h5_link():
    ext = "wm_3j_progress"
    _submitted_claim(ext=ext)
    result = ingest_claim_status_request(
        _normalized("进度", ext=ext, msg_id="m_progress"),
        classify_wecom_intent("进度"),
    )
    reply = result.get("reply_text") or ""
    assert result["active_case_outcome"] == "claim_status_card"
    assert "/task/claim/h5t1." in reply
    assert "继续补充事故资料" in reply or "打开" in reply


def test_active_claim_supplement_materials_returns_h5_link():
    ext = "wm_3j_materials"
    _submitted_claim(ext=ext)
    result = ingest_claim_status_request(
        _normalized("补资料", ext=ext, msg_id="m_mat"),
        classify_wecom_intent("补资料"),
    )
    reply = result.get("reply_text") or ""
    assert "/task/claim/h5t1." in reply


def test_explicit_h5_request_start_or_status_card(monkeypatch):
    ext = "wm_3j_h5_req"
    text = "我需要理赔，发给我 H5"
    result = _run_slice(text, ext=ext, msg_id="m_h5", monkeypatch=monkeypatch)
    reply = result.get("reply_text") or ""
    _assert_no_legacy(reply)
    assert result.get("active_case_outcome") != "legacy_fallback"
    assert "/task/claim/h5t1." in reply or result.get("menu_payload")


# --- Ordinary text supplement (submitted) ---


def test_submitted_claim_insurance_supplement_short_ack():
    ext = "wm_3j_ins"
    saved = _submitted_claim(ext=ext)
    text = "对方保险是 State Farm"
    result = ingest_claim_basics_message(
        _normalized(text, ext=ext, msg_id="m_ins"),
        classify_wecom_intent(text),
    )
    reply = result.get("reply_text") or ""
    assert result["case_id"] == saved["case_id"]
    assert "已记录" in reply
    assert "/task/claim/h5t1." not in reply
    assert "进度" in reply or "链接" in reply
    timeline = (get_case_by_id(saved["case_id"]) or {}).get("claim_timeline") or []
    assert timeline


def test_submitted_claim_plate_supplement_no_add_car_no_raw_h5():
    ext = "wm_3j_plate"
    saved = _submitted_claim(ext=ext)
    _photo_complete_add_car(ext=ext)
    text = "补充一下，对方车牌是 ABC123"
    result = ingest_claim_basics_message(
        _normalized(text, ext=ext, msg_id="m_plate"),
        classify_wecom_intent(text),
    )
    reply = result.get("reply_text") or ""
    assert result["active_case_outcome"] == "claim_supplement_appended"
    assert result["case_id"] == saved["case_id"]
    assert "提车日期" not in reply
    assert "/task/claim/h5t1." not in reply


# --- Important missing items / ready to submit ---


def test_open_claim_missing_items_text_supplement_shows_compact_cta():
    ext = "wm_3j_missing"
    case = _open_claim_missing_basics(ext=ext)
    text = "对方叫张先生"
    result = ingest_claim_basics_message(
        _normalized(text, ext=ext, msg_id="m_miss"),
        classify_wecom_intent(text),
    )
    reply = result.get("reply_text") or ""
    assert result["case_id"] == case["case_id"]
    kind, count = resolve_supplement_h5_cta(case)
    assert kind == SupplementH5CtaKind.MISSING_ITEMS
    assert count > 0
    policy_reply = build_claim_supplement_received_reply(
        case=case,
        h5_intake_url="https://example.test/task/claim/h5t1.test",
    )
    assert "还缺" in policy_reply
    assert "继续补充事故资料" in policy_reply
    assert "【当前状态】" not in policy_reply


def test_ready_not_submitted_supplement_shows_submit_cta():
    ext = "wm_3j_ready"
    case = _ready_not_submitted_claim(ext=ext)
    kind, _ = resolve_supplement_h5_cta(case)
    assert kind == SupplementH5CtaKind.READY_TO_SUBMIT
    reply = build_claim_supplement_received_reply(
        case=case,
        h5_intake_url="https://example.test/task/claim/h5t1.test",
    )
    assert "提交给陈总审核" in reply
    assert "/task/claim/h5t1." in reply


# --- Photo ---


def test_submitted_claim_photo_short_ack_no_raw_h5():
    ext = "wm_3j_photo_sub"
    saved = _submitted_claim(ext=ext)
    result = _ingest_photo(ext=ext, msg_id="img_sub")
    reply = result.get("reply_text") or ""
    assert result["case_id"] == saved["case_id"]
    assert "照片已收到" in reply
    assert "/task/claim/h5t1." not in reply


def test_open_claim_photo_missing_items_shows_compact_cta():
    ext = "wm_3j_photo_miss"
    case = _open_claim_missing_basics(ext=ext)
    result = _ingest_photo(ext=ext, msg_id="img_miss")
    reply = result.get("reply_text") or ""
    assert result["case_id"] == case["case_id"]
    assert "照片已收到" in reply
    assert "继续补充事故资料" in reply or "/task/claim/h5t1." in reply


def test_submitted_claim_photo_beats_add_car_phase2():
    ext = "wm_3j_photo_ac"
    saved = _submitted_claim(ext=ext)
    _photo_complete_add_car(ext=ext)
    result = _ingest_photo(ext=ext, msg_id="img_ac")
    reply = result.get("reply_text") or ""
    assert result["case_id"] == saved["case_id"]
    assert "提车日期" not in reply


# --- Regressions ---


def test_legacy_fallback_regression(monkeypatch):
    ext = "wm_3j_legacy"
    result = _run_slice("我要理赔", ext=ext, msg_id="m_legacy", monkeypatch=monkeypatch)
    _assert_no_legacy(result.get("reply_text") or "")


def test_add_car_intent_preserved(monkeypatch):
    ext = "wm_3j_add_car"
    _submitted_claim(ext=ext)
    result = _run_slice("我要加车", ext=ext, msg_id="m_ac", monkeypatch=monkeypatch)
    assert result["internal_intent"] == "add_car"


def test_explicit_new_accident_confirm_allowed():
    ext = "wm_3j_new_acc"
    _submitted_claim(ext=ext)
    text = "这是另一个事故，不是刚才那个"
    result = ingest_claim_basics_message(
        _normalized(text, ext=ext, msg_id="m_new"),
        classify_wecom_intent(text),
    )
    assert result.get("active_case_outcome") in {
        "claim_collision_resolver",
        "claim_status_card",
        "claim_supplement_appended",
        "claim_start_card_sent",
    }
