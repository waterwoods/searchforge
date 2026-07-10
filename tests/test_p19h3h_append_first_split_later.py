"""P19H-3h-1F — Append-first, Split-later policy tests."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    append_follow_up_message,
    bind_case_channel_identity,
    get_case_by_id,
    patch_case_known_facts,
    save_case,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_collision_choice,
    ingest_claim_injury_quick_reply,
    ingest_claim_lane_switch_choice,
    ingest_claim_status_request,
)
from services.fiqa_api.wecom.claim_identity import is_collision_triggering_input
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_BROKER_DONE,
    CLAIM_PHASE_BROKER_REVIEW,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

_NOW = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
_START_MARKER = "【事故记录已开始 ✅】"
_RESOLVER_MARKERS = ("【请确认】", "继续当前事故", "开始新的事故记录")
_STATUS_TITLE = "【当前状态】"


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
    os.environ["WECOM_KF_TOKEN"] = "tok"
    os.environ["WECOM_KF_ENCODING_AES_KEY"] = "a" * 43
    os.environ["WECOM_CORP_ID"] = "wwtest"
    os.environ["WECOM_KF_SECRET"] = "secret"
    os.environ["WECOM_B0_ACTIVE_WORKSPACE"] = "1"
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)
    load_wecom_kf_config.cache_clear()


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


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


def _open_claim(*, ext: str, with_prior_story: bool = False, incomplete: bool = False) -> dict:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    ts = (_NOW - timedelta(hours=2)).isoformat()
    if with_prior_story:
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
    elif incomplete:
        update_claim_workflow_state(
            cid,
            claim_phase="claim_started",
            guided_workflow_state="collecting_text",
        )
    case = get_case_by_id(cid) or saved
    case["created_at"] = ts
    case["updated_at"] = ts
    return case


def _two_open_claims(ext: str) -> tuple[str, str]:
    older = _open_claim(ext=ext, with_prior_story=True)
    newer = _open_claim(ext=ext, with_prior_story=True)
    return older["case_id"], newer["case_id"]


def _normalized(text: str, *, ext: str, msg_id: str = "m1") -> dict:
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


def _claim_count(ext: str) -> int:
    return sum(
        1
        for c in list_all_cases_for_read()
        if c.get("wecom_external_userid") == ext and c.get("service_lane") == SERVICE_LANE_CLAIM
    )


def _fake_download(_cfg, **kwargs):
    return WeComMediaDownloadResult(
        content=b"fake-image-bytes",
        content_type="image/jpeg",
        filename="photo.jpg",
    )


def _fake_upload(**kwargs):
    return {
        "storage_uri": "gs://caseiq-wecom-media-qa/wecom/test/2026/07/msg.jpg",
        "bucket": "caseiq-wecom-media-qa",
        "object_path": "wecom/test/2026/07/msg.jpg",
        "mime_type": kwargs.get("mime_type"),
        "size_bytes": len(kwargs["content"]),
        "extension": ".jpg",
    }


def test_01_active_claim_accident_narrative_appends_no_collision():
    ext = "wm_af_01"
    saved = _open_claim(ext=ext, with_prior_story=True)
    result = ingest_claim_basics_message(
        _normalized("昨天在 Santa Ana 红绿灯被追尾", ext=ext),
        classify_wecom_intent("昨天在 Santa Ana 红绿灯被追尾"),
    )
    assert result["case_created"] is False
    assert result["case_id"] == saved["case_id"]
    assert result["active_case_outcome"] != "claim_collision_resolver"
    assert not any(m in (result.get("reply_text") or "") for m in _RESOLVER_MARKERS)


def test_02_active_claim_supplement_insurance_appends():
    ext = "wm_af_02"
    saved = _open_claim(ext=ext, with_prior_story=True)
    result = ingest_claim_basics_message(
        _normalized("补充一下，对方保险是 State Farm", ext=ext),
        classify_wecom_intent("补充一下，对方保险是 State Farm"),
    )
    assert result["case_created"] is False
    assert result["case_id"] == saved["case_id"]
    assert result["active_case_outcome"] != "claim_collision_resolver"


def test_03_active_claim_photo_supplement_no_new_case_confirm():
    ext = "wm_af_03"
    saved = _open_claim(ext=ext, with_prior_story=True)
    cfg = load_wecom_kf_config()
    norm = normalize_media_message(
        {
            "msgid": "img_af_03",
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "image",
            "image": {"media_id": "mid03"},
        }
    )
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert result["case_id"] == saved["case_id"]
    assert result["active_case_outcome"] == "media_attached_to_case"
    assert _claim_count(ext) == 1


def test_04_active_claim_explicit_new_accident_triggers_confirm():
    ext = "wm_af_04"
    _open_claim(ext=ext, with_prior_story=True)
    result = ingest_claim_basics_message(
        _normalized("这是另一个事故", ext=ext),
        classify_wecom_intent("这是另一个事故"),
    )
    assert result["active_case_outcome"] == "claim_collision_resolver"
    assert result["case_created"] is False
    assert any(m in (result.get("reply_text") or "") for m in _RESOLVER_MARKERS)


def test_05_repeat_woyao_claim_on_open_offers_continue_not_collision():
    ext = "wm_af_05"
    saved = _open_claim(ext=ext, incomplete=True)
    result = ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext),
        classify_wecom_intent("我要理赔"),
    )
    assert result["case_created"] is False
    assert result["case_id"] == saved["case_id"]
    assert result["active_case_outcome"] != "claim_collision_resolver"


def test_06_passive_markers_do_not_call_collision_resolver():
    passive_samples = (
        "追尾了",
        "被撞",
        "红绿灯",
        "对方保险是 AAA",
        "车牌 ABC123",
        "补充一下",
    )
    for sample in passive_samples:
        assert is_collision_triggering_input(sample) is False


def test_07_multi_open_ordinary_supplement_appends_newest_with_flag():
    ext = "wm_af_07"
    _older, newer = _two_open_claims(ext)
    result = ingest_claim_basics_message(
        _normalized("补充一下对方保险信息", ext=ext),
        classify_wecom_intent("补充一下对方保险信息"),
    )
    assert result["case_id"] == newer
    assert result["active_case_outcome"] != "claim_collision_resolver"
    case = get_case_by_id(newer)
    assert "possible_multi_claim_context" in (case.get("risk_flags") or [])


def test_08_collision_new_start_uses_h5_start_card_not_injury_menu():
    ext = "wm_af_08"
    _open_claim(ext=ext, with_prior_story=True)
    ingest_claim_basics_message(
        _normalized("新的事故", ext=ext, msg_id="m_trig"),
        classify_wecom_intent("新的事故"),
    )
    result = ingest_claim_collision_choice(_normalized("2", ext=ext, msg_id="m_new"))
    assert result["active_case_outcome"] == "claim_start_card_sent"
    assert _START_MARKER in (result.get("reply_text") or "")
    menu = result.get("menu_payload") or {}
    click_items = [item.get("click", {}).get("id") for item in menu.get("list", [])]
    assert "claim_injury_no" not in click_items


def test_09_legacy_injury_quick_reply_still_works():
    ext = "wm_af_09"
    saved = _open_claim(ext=ext, incomplete=True)
    result = ingest_claim_injury_quick_reply(_normalized("没有受伤", ext=ext), injury_value="no")
    assert result["case_id"] == saved["case_id"]
    assert result["active_case_outcome"] in (
        "claim_injury_reply_recorded",
        "claim_injury_manual_handle",
    )


def test_10_status_card_h5_link_open_not_submitted_vs_submitted():
    ext = "wm_af_10"
    open_case = _open_claim(ext=ext, incomplete=True)
    status_open = ingest_claim_status_request(
        _normalized("进度", ext=ext),
        classify_wecom_intent("进度"),
    )
    assert status_open["active_case_outcome"] == "claim_status_card"
    assert status_open.get("h5_task_link_masked") or "h5" in (status_open.get("reply_text") or "").lower()

    submitted = _open_claim(ext="wm_af_10b", with_prior_story=True)
    update_claim_workflow_state(
        submitted["case_id"],
        claim_phase="broker_review",
        guided_workflow_state="awaiting_broker",
    )
    status_sub = ingest_claim_status_request(
        _normalized("进度", ext="wm_af_10b"),
        classify_wecom_intent("进度"),
    )
    assert status_sub["active_case_outcome"] == "claim_status_card"
    assert status_sub.get("h5_task_link_masked") is None


def test_11_lane_switch_confirm_uses_h5_start_card():
    ext = "wm_af_11"
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid=ext)
    ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="m_lane_trig"),
        classify_wecom_intent("我要理赔"),
    )
    result = ingest_claim_lane_switch_choice(_normalized("1", ext=ext, msg_id="m_lane_ok"))
    assert result["active_case_outcome"] == "claim_start_card_sent"
    assert _START_MARKER in (result.get("reply_text") or "")
    menu = result.get("menu_payload") or {}
    click_items = [item.get("click", {}).get("id") for item in menu.get("list", [])]
    assert "claim_injury_no" not in click_items
