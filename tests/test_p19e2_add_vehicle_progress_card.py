"""P19E-2 — Add Vehicle Progress Card / status resume layer."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    save_case,
    _load_case_for_mutation,
    _persist_case_after_update,
    update_case_workspace_flags,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.add_vehicle_progress import (
    derive_add_vehicle_progress,
    find_active_add_car_case_for_progress,
    should_route_add_vehicle_progress,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import (
    classify_wecom_intent,
    is_add_vehicle_status_inquiry,
)
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply import build_add_vehicle_progress_card, build_guided_menu_payload
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


def _save_add_car_case(*, ext: str = "wm_test", updated_at: str | None = None) -> dict:
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    if updated_at:
        mut = _load_case_for_mutation(cid)
        assert mut is not None
        mut["updated_at"] = updated_at
        _persist_case_after_update(cid, mut)
    return get_case_by_id(cid) or saved


def _case_phase1_partial(*, ext: str = "wm_test") -> dict:
    case = _save_add_car_case(ext=ext)
    mut = _load_case_for_mutation(case["case_id"])
    assert mut is not None
    mut["case_attachments"] = [
        {"attachment_id": "a1", "source": "h5_task", "slot_assignment": "vin_photo"},
    ]
    _persist_case_after_update(case["case_id"], mut)
    return get_case_by_id(case["case_id"]) or mut


def _case_phase1_complete(*, ext: str = "wm_test") -> dict:
    case = _save_add_car_case(ext=ext)
    mut = _load_case_for_mutation(case["case_id"])
    assert mut is not None
    mut["case_attachments"] = [
        {"attachment_id": "a1", "source": "h5_task", "slot_assignment": "vin_photo"},
        {"attachment_id": "a2", "source": "h5_task", "slot_assignment": "registration_photo"},
        {"attachment_id": "a3", "source": "h5_task", "slot_assignment": "insurance_card_photo"},
    ]
    _persist_case_after_update(case["case_id"], mut)
    return get_case_by_id(case["case_id"]) or mut


def _case_phase2_partial(*, ext: str = "wm_test") -> dict:
    case = _case_phase1_complete(ext=ext)
    mut = _load_case_for_mutation(case["case_id"])
    assert mut is not None
    mut["collected_fields"] = ["zip"]
    mut["known_facts"] = {"zip": "92705"}
    _persist_case_after_update(case["case_id"], mut)
    return get_case_by_id(case["case_id"]) or mut


def _case_phase3(*, ext: str = "wm_test") -> dict:
    case = _case_phase1_complete(ext=ext)
    mut = _load_case_for_mutation(case["case_id"])
    assert mut is not None
    mut["collected_fields"] = ["delivery_date", "zip", "phone"]
    mut["known_facts"] = {
        "delivery_date": "7月10日",
        "zip": "92705",
        "phone": "9491234567",
    }
    mut["guided_workflow_state"] = "ready_for_broker_review"
    mut["add_vehicle_phase"] = "phase_3_broker_review"
    _persist_case_after_update(case["case_id"], mut)
    return get_case_by_id(case["case_id"]) or mut


def _b0_cfg(monkeypatch) -> object:
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-secret-for-h5")
    load_wecom_kf_config.cache_clear()
    return load_wecom_kf_config()


def _process_text(monkeypatch, text: str, *, ext: str = "wm_test", msg_id: str | None = None) -> list[dict]:
    _b0_cfg(monkeypatch)
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()
    mid = msg_id or f"msg_{abs(hash(text)) & 0xFFFF}"
    msg = {
        "msgid": mid,
        "msgtype": "text",
        "text": {"content": text},
        "external_userid": ext,
        "open_kfid": "wktest001",
    }
    with patch("services.fiqa_api.wecom.slice.send_menu_reply"):
        with patch("services.fiqa_api.wecom.slice.send_text_reply"):
            results = process_kf_msg_or_event(
                cfg,
                callback_token="tok",
                open_kf_id="wktest001",
                pull_messages=lambda *_a, **_k: [msg],
            )
    return results


# --- Intent ---


@pytest.mark.parametrize(
    "text",
    [
        "进度",
        "还差什么",
        "我现在到哪了",
        "status",
        "continue",
        "did I submit",
    ],
)
def test_status_inquiry_markers(text: str):
    assert is_add_vehicle_status_inquiry(text) is True


def test_hello_is_not_status_inquiry_marker_alone():
    assert is_add_vehicle_status_inquiry("你好") is False


def test_restart_not_status_inquiry():
    assert is_add_vehicle_status_inquiry("重新加车") is False


# --- Progress intent routing ---


def test_hello_no_active_case_returns_guided_menu(monkeypatch):
    results = _process_text(monkeypatch, "你好")
    assert results[0]["guided_menu_required"] is True
    assert results[0].get("active_case_outcome") != "add_vehicle_progress_card"


def test_hello_with_phase1_incomplete_returns_progress_card(monkeypatch):
    _case_phase1_partial()
    results = _process_text(monkeypatch, "你好")
    assert results[0].get("active_case_outcome") == "add_vehicle_progress_card"
    assert results[0]["guided_menu_required"] is False


@pytest.mark.parametrize("text", ["进度", "还差什么", "我现在到哪了", "status"])
def test_status_with_active_case_returns_progress_card(monkeypatch, text: str):
    _case_phase2_partial()
    results = _process_text(monkeypatch, text)
    assert results[0].get("active_case_outcome") == "add_vehicle_progress_card"


# --- Routing priority ---


def test_restart_still_starts_new_flow_not_progress(monkeypatch):
    _case_phase3()
    results = _process_text(monkeypatch, "重新加车")
    assert results[0].get("active_case_outcome") != "add_vehicle_progress_card"
    assert results[0].get("active_case_outcome") in ("start_card_sent", "photo_flow_complete_followup")


def test_claim_lane_not_hijacked_by_progress(monkeypatch):
    _case_phase2_partial()
    results = _process_text(monkeypatch, "我要理赔")
    assert results[0].get("active_case_outcome") != "add_vehicle_progress_card"
    assert results[0]["internal_intent"] == "claim_intake"


def test_phase2_combined_text_extracts_not_progress(monkeypatch):
    case = _case_phase1_complete()
    _b0_cfg(monkeypatch)
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()
    text = "7月10号提车，zip 92705，电话2031234567"
    msg = {
        "msgid": "msg_phase2_combo",
        "msgtype": "text",
        "text": {"content": text},
        "external_userid": case["wecom_external_userid"],
        "open_kfid": "wktest001",
    }
    with patch("services.fiqa_api.wecom.slice.send_menu_reply"):
        with patch("services.fiqa_api.wecom.slice.send_text_reply"):
            results = process_kf_msg_or_event(
                cfg,
                callback_token="tok",
                open_kf_id="wktest001",
                pull_messages=lambda *_a, **_k: [msg],
            )
    assert results[0].get("active_case_outcome") != "add_vehicle_progress_card"
    assert "phase2" in str(results[0].get("active_case_outcome") or "")


def test_add_car_after_phase1_complete_returns_progress_not_new_h5(monkeypatch):
    _case_phase1_complete()
    results = _process_text(monkeypatch, "我要加车")
    assert results[0].get("active_case_outcome") == "add_vehicle_progress_card"


# --- State mapping ---


def test_phase1_card_shows_step1_and_missing_photos():
    case = _case_phase1_partial()
    progress = derive_add_vehicle_progress(case)
    text, menu = build_add_vehicle_progress_card(case, progress=progress, h5_url="https://example.com/t")
    assert menu is not None
    assert "第 1 步" in menu["head_content"]
    assert "行驶证照片" in menu["head_content"]
    assert menu["list"][0]["view"]["content"] == "继续上传照片"


def test_phase2_incomplete_card():
    case = _case_phase1_complete()
    progress = derive_add_vehicle_progress(case)
    text, menu = build_add_vehicle_progress_card(case, progress=progress)
    assert menu is None
    assert text is not None
    assert "第 2 步" in text
    assert "提车日期" in text


def test_phase2_partial_card_shows_collected_values():
    case = _case_phase2_partial()
    progress = derive_add_vehicle_progress(case)
    text, menu = build_add_vehicle_progress_card(case, progress=progress)
    assert "92705" in (text or "")
    assert "提车日期" in (text or "")


def test_phase3_card_broker_review_no_action():
    case = _case_phase3()
    progress = derive_add_vehicle_progress(case)
    text, menu = build_add_vehicle_progress_card(case, progress=progress)
    assert "第 3 步" in (text or "")
    assert "不需要您补充资料" in (text or "")


def test_multiple_open_cases_chooses_newest_and_tail():
    older = _save_add_car_case(ext="wm_multi", updated_at="2026-07-01T00:00:00Z")
    mut_old = _load_case_for_mutation(older["case_id"])
    assert mut_old is not None
    mut_old["case_attachments"] = [
        {"attachment_id": "a1", "source": "h5_task", "slot_assignment": "vin_photo"},
    ]
    _persist_case_after_update(older["case_id"], mut_old)

    newer = _case_phase2_partial(ext="wm_multi")
    mut = _load_case_for_mutation(newer["case_id"])
    assert mut is not None
    mut["updated_at"] = "2026-07-06T00:00:00Z"
    _persist_case_after_update(newer["case_id"], mut)

    case, count = find_active_add_car_case_for_progress("wm_multi")
    assert count == 2
    assert case is not None
    assert case["case_id"] == newer["case_id"]
    progress = derive_add_vehicle_progress(case)
    text, _ = build_add_vehicle_progress_card(case, progress=progress, multiple_open_cases=True)
    assert "多台车" in (text or "")


# --- Read path ---


def test_progress_uses_postgres_read_facade_not_legacy_get_case_by_id(monkeypatch):
    pg_case = _case_phase2_partial(ext="wm_pg")
    with patch(
        "services.fiqa_api.wecom.add_vehicle_progress.list_all_cases_for_read",
        return_value=[pg_case],
    ):
        with patch(
            "services.fiqa_api.inbox_triage.case_store.get_case_by_id",
            return_value=None,
        ):
            case, count = find_active_add_car_case_for_progress("wm_pg")
    assert count == 1
    assert case is not None
    assert case["case_id"] == pg_case["case_id"]


def test_progress_works_when_legacy_get_case_by_id_returns_none(monkeypatch):
    pg_case = _case_phase1_complete(ext="wm_pg_only")
    normalized = {"text": "进度", "external_userid": "wm_pg_only"}
    intent = classify_wecom_intent("进度")
    with patch(
        "services.fiqa_api.wecom.add_vehicle_progress.list_all_cases_for_read",
        return_value=[pg_case],
    ):
        with patch(
            "services.fiqa_api.inbox_triage.case_store.get_case_by_id",
            return_value=None,
        ):
            assert should_route_add_vehicle_progress(normalized, intent, guided_menu=False) is True


# --- Regression ---


def test_broker_done_progress_card(monkeypatch):
    case = _case_phase3()
    update_case_workspace_flags(case["case_id"], broker_confirmed_at="2026-07-06T12:00:00Z")
    refreshed = get_case_by_id(case["case_id"]) or case
    progress = derive_add_vehicle_progress(refreshed)
    assert progress["phase"] == "broker_done"
    text, _ = build_add_vehicle_progress_card(refreshed, progress=progress)
    assert "陈总已处理" in (text or "")
