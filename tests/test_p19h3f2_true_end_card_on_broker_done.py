"""P19H-3f-2 — True End Card on broker_done (Claim only, no auto close)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_store import (
    ClaimBrokerDoneError,
    get_case_by_id,
    mark_claim_broker_done,
    save_case,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.claim_workbench_display import (
    build_claim_display_status,
    is_claim_broker_done,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_WECOM_MEDIA_INTAKE
from services.fiqa_api.inbox_triage.workbench_enrichment import (
    filter_broker_workbench_cases,
    is_broker_active_queue_case,
)
from services.fiqa_api.routes.inbox_triage import router as inbox_router
from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_BROKER_DONE,
    SERVICE_LANE_CLAIM,
    customer_copy_contains_forbidden_phrase,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.reply import build_claim_end_card_reply, build_claim_start_card_reply

_FORBIDDEN_SNIPPETS = (
    "保险公司已结案",
    "一定会赔",
    "对方全责",
    "coverage approved",
    "claim filed",
    "carrier accepted",
    "已报案",
    "已受理",
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
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


@pytest.fixture
def cfg(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "sec")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    return load_wecom_kf_config()


def _api_client() -> TestClient:
    app = FastAPI()
    app.include_router(inbox_router)
    return TestClient(app)


def _msg(msg_id: str, content: str, *, ext: str = "wm_p19h3f2") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": ext,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": content},
    }


def _normalized(text: str, *, ext: str = "wm_p19h3f2", msg_id: str = "m1") -> dict:
    return normalize_text_message(_msg(msg_id, text, ext=ext))


def _image_msg(msg_id: str, *, ext: str = "wm_p19h3f2_photo") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": ext,
        "origin": 3,
        "msgtype": "image",
        "image": {"media_id": f"media_{msg_id}"},
    }


def _fake_download(_cfg, *, media_id: str, msgtype: str) -> WeComMediaDownloadResult:
    return WeComMediaDownloadResult(
        content=b"\xff\xd8\xff",
        content_type="image/jpeg",
        filename="photo.jpg",
    )


def _fake_upload(**_kwargs) -> dict:
    return {
        "storage_uri": "gs://test-bucket/wecom/photo.jpg",
        "mime_type": "image/jpeg",
        "size_bytes": 3,
    }


def _seed_claim() -> str:
    result = ingest_claim_basics_message(
        _normalized("我要理赔", ext="wm_claim_done", msg_id="m_start"),
        classify_wecom_intent("我要理赔"),
    )
    case_id = str(result["case_id"])
    assert result.get("active_case_outcome") == "claim_start_card_sent"
    return case_id


def _seed_wecom_media_intake(cfg) -> str:
    norm = normalize_media_message(_image_msg("img_raw", ext="wm_raw_done"))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert result["active_case_outcome"] == "media_unassigned"
    return str(result["case_id"])


def _broker_done_events(case: dict) -> list[dict]:
    timeline = case.get("claim_timeline") or []
    return [e for e in timeline if isinstance(e, dict) and e.get("event_type") == "broker_done"]


def _assert_no_forbidden_copy(text: str) -> None:
    assert customer_copy_contains_forbidden_phrase(text or "") is None
    for phrase in _FORBIDDEN_SNIPPETS:
        assert phrase not in (text or "")


def test_01_broker_done_allowed_for_formal_claim():
    case_id = _seed_claim()
    result = mark_claim_broker_done(case_id)
    assert result["outcome"] == "broker_done"
    assert result["already_done"] is False
    assert result["case"]["claim_phase"] == CLAIM_PHASE_BROKER_DONE


def test_02_broker_done_rejects_raw_inbound(cfg):
    media_id = _seed_wecom_media_intake(cfg)
    with pytest.raises(ClaimBrokerDoneError, match="raw_inbound"):
        mark_claim_broker_done(media_id)


def test_03_broker_done_rejects_non_claim_lane():
    saved = save_case(
        "add car request",
        triage_stub(),
        service_lane="add_car",
    )
    with pytest.raises(ClaimBrokerDoneError, match="not_claim"):
        mark_claim_broker_done(saved["case_id"])


def test_04_broker_done_appends_timeline_event():
    case_id = _seed_claim()
    mark_claim_broker_done(case_id)
    stored = get_case_by_id(case_id) or {}
    events = _broker_done_events(stored)
    assert len(events) == 1
    assert events[0].get("actor") == "broker"
    assert events[0].get("metadata", {}).get("source") == "workbench"


def test_05_broker_done_sets_done_status():
    case_id = _seed_claim()
    mark_claim_broker_done(case_id)
    stored = get_case_by_id(case_id) or {}
    assert stored.get("claim_phase") == CLAIM_PHASE_BROKER_DONE
    assert stored.get("claim_end_card_state", {}).get("broker_done_at")


def test_06_broker_done_returns_end_card_copy():
    case_id = _seed_claim()
    result = mark_claim_broker_done(case_id)
    preview = result.get("end_card_preview") or ""
    assert "【陈总已确认" in preview
    assert "收集阶段已结束" in preview


def test_07_end_card_copy_has_disclaimer():
    copy = build_claim_end_card_reply()
    assert "不代表保险公司已经结案" in copy
    assert "不代表赔付结果" in copy


def test_08_end_card_copy_no_forbidden_language():
    _assert_no_forbidden_copy(build_claim_end_card_reply())


def test_09_broker_done_idempotent_no_duplicate_timeline():
    case_id = _seed_claim()
    mark_claim_broker_done(case_id)
    mark_claim_broker_done(case_id)
    stored = get_case_by_id(case_id) or {}
    assert len(_broker_done_events(stored)) == 1


def test_10_second_broker_done_does_not_resend_end_card(monkeypatch):
    case_id = _seed_claim()
    send_calls: list[str] = []

    def _fake_send(cid: str) -> dict:
        send_calls.append(cid)
        return {"sent": True, "end_card_preview": build_claim_end_card_reply(), "send_skipped": False}

    monkeypatch.setattr(
        "services.fiqa_api.wecom.claim_end_card.try_send_claim_end_card",
        _fake_send,
    )
    first = mark_claim_broker_done(case_id)
    second = mark_claim_broker_done(case_id)
    assert first["already_done"] is False
    assert second["already_done"] is True
    assert len(send_calls) == 1


def test_11_done_case_display_label():
    case_id = _seed_claim()
    mark_claim_broker_done(case_id)
    stored = get_case_by_id(case_id) or {}
    label = build_claim_display_status(stored)
    assert "已确认" in label or "已交接" in label


def test_12_start_card_policy_still_passes():
    start = build_claim_start_card_reply()
    assert "【事故记录已开始" in start
    assert "这只是资料收集，不代表已经正式向保险公司报案。" in start
    _assert_no_forbidden_copy(start.replace("这只是资料收集，不代表已经正式向保险公司报案。", ""))


def test_13_raw_inbound_hidden_policy_still_passes(cfg):
    media_id = _seed_wecom_media_intake(cfg)
    claim_id = _seed_claim()
    visible = filter_broker_workbench_cases(list_all_cases_for_read())
    ids = [c["case_id"] for c in visible]
    assert media_id not in ids
    assert claim_id in ids


def test_14_done_claim_leaves_active_queue():
    case_id = _seed_claim()
    mark_claim_broker_done(case_id)
    stored = get_case_by_id(case_id) or {}
    assert is_claim_broker_done(stored)
    assert is_broker_active_queue_case(stored) is False
    visible = filter_broker_workbench_cases(list_all_cases_for_read())
    assert not any(c.get("case_id") == case_id for c in visible)


def test_15_api_endpoint_broker_done():
    case_id = _seed_claim()
    resp = _api_client().post(f"/api/inbox/cases/{case_id}/broker-done")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("claim_phase") == CLAIM_PHASE_BROKER_DONE
    assert body.get("display_status", "").find("已确认") >= 0 or "已交接" in body.get("display_status", "")
    assert body.get("end_card_preview")


def test_16_api_rejects_raw_inbound(cfg):
    media_id = _seed_wecom_media_intake(cfg)
    resp = _api_client().post(f"/api/inbox/cases/{media_id}/broker-done")
    assert resp.status_code == 400


def triage_stub() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "medium",
        "manual_followup_needed": False,
        "broker_next_step": "Review",
        "client_prep": "",
        "client_reply_draft": "",
        "primary_vehicle_summary": "",
    }
