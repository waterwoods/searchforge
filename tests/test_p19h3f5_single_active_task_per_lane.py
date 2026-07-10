"""P19H-3f-5 — Single Active Task per Lane tests."""

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
    mark_claim_broker_done,
    patch_case_known_facts,
    save_case,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.inbox_triage.claim_workbench_display import build_claim_case_brief
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_collision_choice,
    ingest_claim_status_request,
    list_open_claim_candidates_for_basics,
)
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
from services.fiqa_api.wecom.reply import build_claim_status_card_reply
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

_NOW = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
_START_MARKER = "【事故记录已开始 ✅】"
_CONFIRM_MARKERS = ("【请确认】", "继续当前事故", "开始新的事故记录")
_STATUS_TITLE = "【当前状态】"
_END_MARKER = "【陈总已确认 ✅】"
_ACCIDENT_NARRATIVE = "昨天7月8号，我们在 Santa Ana 红绿灯停下来，后车没停撞了我们。"


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


def _open_claim(
    *,
    ext: str = "wm_sat",
    with_prior_story: bool = False,
    updated_hours_ago: int = 2,
) -> dict:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    ts = (_NOW - timedelta(hours=updated_hours_ago)).isoformat()
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
    case = get_case_by_id(cid) or saved
    case["created_at"] = ts
    case["updated_at"] = ts
    return case


def _two_open_claims(ext: str) -> tuple[str, str]:
    older = _open_claim(ext=ext, with_prior_story=True)
    newer = _open_claim(ext=ext, with_prior_story=True)
    return str(older["case_id"]), str(newer["case_id"])


def _normalized(text: str, *, ext: str = "wm_sat", msg_id: str = "m1") -> dict:
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


def _slice_text(text: str, *, ext: str = "wm_sat", msg_id: str = "m1") -> dict:
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

    results = process_kf_msg_or_event(
        cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
    )
    assert results, f"no slice outcome for {text!r}"
    return results[0]


def _fake_download(cfg, **kwargs):
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


def test_01_single_active_claim_ordinary_supplement_append_no_confirm():
    ext = "wm_sat_01"
    saved = _open_claim(ext=ext, with_prior_story=True)
    result = ingest_claim_basics_message(
        _normalized("对方保险卡已拍照", ext=ext),
        classify_wecom_intent("对方保险卡已拍照"),
    )
    assert result["case_created"] is False
    assert result["case_id"] == saved["case_id"]
    assert result["active_case_outcome"] != "claim_collision_resolver"


def test_02_single_active_claim_new_accident_confirm_no_silent_new():
    ext = "wm_sat_02"
    _open_claim(ext=ext, with_prior_story=True)
    result = ingest_claim_basics_message(
        _normalized("新的事故", ext=ext),
        classify_wecom_intent("新的事故"),
    )
    assert result["active_case_outcome"] == "claim_collision_resolver"
    assert result["case_created"] is False
    assert _claim_count(ext) == 1
    assert any(m in (result.get("reply_text") or "") for m in _CONFIRM_MARKERS)


def test_03_confirm_choice_1_appends_to_current_claim():
    ext = "wm_sat_03"
    saved = _open_claim(ext=ext, with_prior_story=True)
    ingest_claim_basics_message(
        _normalized("新的事故", ext=ext, msg_id="m_trig"),
        classify_wecom_intent("新的事故"),
    )
    result = ingest_claim_collision_choice(_normalized("1", ext=ext, msg_id="m_choice"))
    assert result["active_case_outcome"] == "claim_collision_continue"
    assert result["case_id"] == saved["case_id"]
    assert result["case_created"] is False


def test_04_confirm_choice_2_creates_new_claim_start_card():
    ext = "wm_sat_04"
    _open_claim(ext=ext, with_prior_story=True)
    ingest_claim_basics_message(
        _normalized(_ACCIDENT_NARRATIVE, ext=ext, msg_id="m_trig"),
        classify_wecom_intent(_ACCIDENT_NARRATIVE),
    )
    result = ingest_claim_collision_choice(_normalized("2", ext=ext, msg_id="m_new"))
    assert result["active_case_outcome"] == "claim_start_card_sent"
    assert result["case_created"] is True
    assert _claim_count(ext) == 2
    assert _START_MARKER in (result.get("reply_text") or "")


def test_05_confirm_choice_3_manual_no_append_create():
    ext = "wm_sat_05"
    saved = _open_claim(ext=ext, with_prior_story=True)
    ingest_claim_basics_message(
        _normalized("新的事故", ext=ext, msg_id="m_trig"),
        classify_wecom_intent("新的事故"),
    )
    before = len((get_case_by_id(saved["case_id"]) or {}).get("claim_timeline") or [])
    result = ingest_claim_collision_choice(_normalized("3", ext=ext, msg_id="m_contact"))
    assert result["active_case_outcome"] == "claim_collision_contact"
    assert result["case_created"] is False
    assert _claim_count(ext) == 1
    after = len((get_case_by_id(saved["case_id"]) or {}).get("claim_timeline") or [])
    assert after == before


def test_06_multi_open_ordinary_supplement_append_newest_with_flag():
    ext = "wm_sat_06"
    _older, newer = _two_open_claims(ext)
    result = ingest_claim_basics_message(
        _normalized("补充一下对方保险信息", ext=ext),
        classify_wecom_intent("补充一下对方保险信息"),
    )
    assert result["case_created"] is False
    assert result["case_id"] == newer
    assert result["active_case_outcome"] != "claim_collision_resolver"
    case = get_case_by_id(newer)
    assert "possible_multi_claim_context" in (case.get("risk_flags") or [])


def test_07_multi_open_aaa_insurance_append_no_resolver():
    ext = "wm_sat_07"
    _older, newer = _two_open_claims(ext)
    result = ingest_claim_basics_message(
        _normalized("对方保险是 AAA", ext=ext),
        classify_wecom_intent("对方保险是 AAA"),
    )
    assert result["case_id"] == newer
    assert result["active_case_outcome"] != "claim_collision_resolver"


def test_08_multi_open_new_accident_confirm_not_picker():
    ext = "wm_sat_08"
    _two_open_claims(ext)
    result = ingest_claim_basics_message(
        _normalized("新的事故", ext=ext),
        classify_wecom_intent("新的事故"),
    )
    assert result["active_case_outcome"] == "claim_collision_resolver"
    reply = result.get("reply_text") or ""
    assert "【请确认】" in reply
    assert "继续当前事故" in reply
    assert "请选择" not in reply


def test_09_multi_open_status_card_newest_with_footnote():
    ext = "wm_sat_09"
    _older, newer = _two_open_claims(ext)
    result = ingest_claim_status_request(
        _normalized("进度怎么样了", ext=ext),
        classify_wecom_intent("进度怎么样了"),
    )
    assert result["active_case_outcome"] == "claim_status_card"
    assert result["case_id"] == newer
    reply = result.get("reply_text") or ""
    assert _STATUS_TITLE in reply
    assert "最近这份事故记录" in reply
    assert "新的事故" in reply


def test_10_multi_open_photo_bind_newest_with_flag():
    ext = "wm_sat_10"
    _older, newer = _two_open_claims(ext)
    cfg = load_wecom_kf_config()
    norm = normalize_media_message(
        {
            "msgid": "img_sat_10",
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "image",
            "image": {"media_id": "mid10"},
        }
    )
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert result["case_id"] == newer
    assert result["active_case_outcome"] == "media_attached_to_case"
    case = get_case_by_id(newer)
    assert "possible_multi_claim_context" in (case.get("risk_flags") or [])


def test_11_random_photo_before_start_hidden_no_claim():
    ext = "wm_sat_11"
    cfg = load_wecom_kf_config()
    norm = normalize_media_message(
        {
            "msgid": "img_sat_11",
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "image",
            "image": {"media_id": "mid11"},
        }
    )
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert _claim_count(ext) == 0
    assert result.get("active_case_outcome") == "media_unassigned"
    assert _START_MARKER not in (result.get("reply_text") or "")


def test_12_add_car_draft_still_discoverable():
    from services.fiqa_api.wecom.active_case_bridge import find_open_add_car_case_by_external_userid

    ext = "wm_sat_12"
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid=ext)
    assert find_open_add_car_case_by_external_userid(ext) == saved["case_id"]


def test_13_add_car_restart_marker_recognized_partial():
    from services.fiqa_api.inbox_triage.h5_task_upload import is_explicit_add_car_restart

    assert is_explicit_add_car_restart("再加一辆车") is True


def test_14_add_car_to_claim_lane_switch_still_works():
    ext = "wm_sat_14"
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid=ext)
    result = _slice_text("我要理赔", ext=ext, msg_id="m_lane")
    assert result.get("active_case_outcome") == "claim_lane_switch_prompt"
    assert _START_MARKER not in (result.get("reply_text") or "")


def test_15_claim_to_add_car_no_unsafe_silent_switch():
    ext = "wm_sat_15"
    _open_claim(ext=ext, with_prior_story=True)
    result = _slice_text("我要加车", ext=ext, msg_id="m_add")
    assert result.get("active_case_outcome") != "claim_start_card_sent"
    assert _claim_count(ext) == 1


def test_16_broker_done_end_card_still_pass():
    ext = "wm_sat_16"
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid=ext)
    update_claim_workflow_state(saved["case_id"], claim_phase=CLAIM_PHASE_BROKER_REVIEW)
    done = mark_claim_broker_done(saved["case_id"])
    assert done.get("already_done") is False or done.get("end_card_sent") is not False
    case = get_case_by_id(saved["case_id"])
    assert case.get("claim_phase") == CLAIM_PHASE_BROKER_DONE


def test_17_status_start_end_card_frames_pass():
    ext = "wm_sat_17"
    case = _open_claim(ext=ext, with_prior_story=True)
    status = build_claim_status_card_reply(case, multiple_open_claims=False)
    assert status.startswith("━━━━━━━━━━━━")
    assert _STATUS_TITLE in status


def test_18_process_kf_multi_open_ordinary_supplement_e2e():
    ext = "wm_sat_18"
    _older, newer = _two_open_claims(ext)
    result = _slice_text("补充一下车牌号", ext=ext, msg_id="m_e2e_1")
    assert result.get("case_id") == newer
    assert result.get("active_case_outcome") != "claim_collision_resolver"


def test_19_process_kf_multi_open_strong_new_accident_e2e():
    ext = "wm_sat_19"
    _two_open_claims(ext)
    result = _slice_text("新的事故", ext=ext, msg_id="m_e2e_2")
    assert result.get("active_case_outcome") == "claim_collision_resolver"


def test_20_h5_subset_status_card_brief_warning():
    ext = "wm_sat_20"
    _older, newer = _two_open_claims(ext)
    ingest_claim_basics_message(
        _normalized("对方保险是 State Farm", ext=ext),
        classify_wecom_intent("对方保险是 State Farm"),
    )
    case = get_case_by_id(newer)
    brief = build_claim_case_brief(case)
    assert any("多份未完成事故记录" in h for h in brief.get("highlights") or [])
    open_claims = list_open_claim_candidates_for_basics(ext)
    assert len(open_claims) == 2
