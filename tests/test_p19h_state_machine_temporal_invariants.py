"""P19H — Workflow state machine temporal invariants (audit battery).

Read-only audit companion: exercises boundary / broker_done / lane-switch invariants
without modifying production workflow code. See docs/p19h_state_machine_temporal_audit_2026_07_10.md.
"""

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
    bind_case_channel_identity,
    get_case_by_id,
    mark_claim_broker_done,
    save_case,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import (
    SERVICE_LANE_ADD_CAR,
    SERVICE_LANE_WECOM_MEDIA_INTAKE,
)
from services.fiqa_api.inbox_triage.workbench_enrichment import (
    filter_broker_workbench_cases,
    is_raw_inbound_case,
)
from services.fiqa_api.routes.inbox_triage import router as inbox_router
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_holding_ack,
    ingest_claim_lane_switch_choice,
    should_route_claim_guided_workflow,
    should_route_claim_holding_ack,
)
from services.fiqa_api.wecom.claim_end_card import try_send_claim_end_card
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_BROKER_DONE,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.reply import build_claim_end_card_reply, build_claim_start_card_reply

_START_MARKER = "【事故记录已开始 ✅】"
_NARRATIVE = "昨晚 Costco 被追尾了，后保险杠有点坏。"


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


def _msg(msg_id: str, content: str, *, ext: str = "wm_p19h_audit") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": ext,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": content},
    }


def _normalized(text: str, *, ext: str = "wm_p19h_audit", msg_id: str = "m1") -> dict:
    return normalize_text_message(_msg(msg_id, text, ext=ext))


def _image_msg(msg_id: str, *, ext: str = "wm_p19h_audit_photo") -> dict:
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


def _claim_cases() -> list[dict]:
    return [c for c in list_all_cases_for_read() if c.get("service_lane") == SERVICE_LANE_CLAIM]


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


def _seed_active_add_car(*, ext: str = "wm_av_audit") -> dict:
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid=ext)
    return get_case_by_id(saved["case_id"]) or saved


def _broker_done_events(case: dict) -> list[dict]:
    timeline = case.get("claim_timeline") or []
    return [e for e in timeline if isinstance(e, dict) and e.get("event_type") == "broker_done"]


# --- 1. Random accident narrative before Start Card does not create Claim ---


def test_invariant_01_random_narrative_no_formal_claim():
    normalized = _normalized(_NARRATIVE, msg_id="inv01")
    intent = classify_wecom_intent(_NARRATIVE)
    assert should_route_claim_holding_ack(normalized, intent) is True
    assert should_route_claim_guided_workflow(normalized, intent) is False
    result = ingest_claim_holding_ack(normalized)
    assert result["case_created"] is False
    assert _claim_cases() == []
    assert _START_MARKER not in (result.get("reply_text") or "")


# --- 2. Random photo before Start Card hidden from default queue ---


def test_invariant_02_random_photo_hidden_from_broker_queue(cfg):
    norm = normalize_media_message(_image_msg("inv02", ext="wm_inv02"))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert result["active_case_outcome"] == "media_unassigned"
    assert _claim_cases() == []
    case = get_case_by_id(result["case_id"]) or {}
    assert case.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE
    visible = filter_broker_workbench_cases(list_all_cases_for_read())
    assert not any(c.get("case_id") == result["case_id"] for c in visible)
    resp = _api_client().get("/api/inbox/cases", params={"limit": 50})
    assert result["case_id"] not in [c["case_id"] for c in resp.json().get("cases") or []]


# --- 3. Explicit Claim start emits Start Card before claim recording ---


def test_invariant_03_explicit_start_emits_start_card_before_timeline_story():
    ext = "wm_inv03"
    result = ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="inv03a"),
        classify_wecom_intent("我要理赔"),
    )
    assert result["case_created"] is True
    reply = result.get("reply_text") or ""
    assert _START_MARKER in reply
    assert "提交给陈总审核" in reply
    case = get_case_by_id(result["case_id"]) or {}
    timeline = case.get("claim_timeline") or []
    types = {e.get("event_type") for e in timeline}
    assert "claim_started" in types
    assert "basics_complete" not in types
    assert "customer_text" not in types or len(types) <= 2


# --- 4. End Card cannot occur before broker_done ---


def test_invariant_04_end_card_only_after_broker_done():
    case_id = ingest_claim_basics_message(
        _normalized("我要理赔", ext="wm_inv04", msg_id="inv04"),
        classify_wecom_intent("我要理赔"),
    )["case_id"]
    stored = get_case_by_id(case_id) or {}
    assert stored.get("claim_phase") != CLAIM_PHASE_BROKER_DONE
    assert not _broker_done_events(stored)
    assert not (stored.get("claim_end_card_state") or {}).get("broker_done_at")
    preview = build_claim_end_card_reply()
    assert "陈总已确认" in preview
    send = try_send_claim_end_card(case_id)
    assert send.get("send_skipped") is True
    after = get_case_by_id(case_id) or {}
    assert after.get("claim_phase") != CLAIM_PHASE_BROKER_DONE


# --- 5. broker_done rejects raw inbound ---


def test_invariant_05_broker_done_rejects_raw_inbound(cfg):
    norm = normalize_media_message(_image_msg("inv05", ext="wm_inv05"))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    media_id = str(result["case_id"])
    assert is_raw_inbound_case(get_case_by_id(media_id) or {})
    with pytest.raises(ClaimBrokerDoneError, match="raw_inbound"):
        mark_claim_broker_done(media_id)
    resp = _api_client().post(f"/api/inbox/cases/{media_id}/broker-done")
    assert resp.status_code == 400


# --- 6. broker_done idempotent ---


def test_invariant_06_broker_done_idempotent():
    case_id = ingest_claim_basics_message(
        _normalized("我要理赔", ext="wm_inv06", msg_id="inv06"),
        classify_wecom_intent("我要理赔"),
    )["case_id"]
    first = mark_claim_broker_done(case_id)
    second = mark_claim_broker_done(case_id)
    assert first["already_done"] is False
    assert second["already_done"] is True
    stored = get_case_by_id(case_id) or {}
    assert len(_broker_done_events(stored)) == 1


# --- 7. Done Claim hidden from default queue but single GET works ---


def test_invariant_07_done_claim_hidden_but_get_works():
    case_id = ingest_claim_basics_message(
        _normalized("我要理赔", ext="wm_inv07", msg_id="inv07"),
        classify_wecom_intent("我要理赔"),
    )["case_id"]
    mark_claim_broker_done(case_id)
    visible = filter_broker_workbench_cases(list_all_cases_for_read())
    assert not any(c.get("case_id") == case_id for c in visible)
    resp = _api_client().get(f"/api/inbox/cases/{case_id}")
    assert resp.status_code == 200
    assert resp.json().get("claim_phase") == CLAIM_PHASE_BROKER_DONE


# --- 8. Active Add Car + ambiguous accident narrative does not auto Claim ---


def test_invariant_08_active_add_car_narrative_holding_not_claim():
    ext = "wm_inv08"
    _seed_active_add_car(ext=ext)
    normalized = _normalized(_NARRATIVE, ext=ext, msg_id="inv08")
    intent = classify_wecom_intent(_NARRATIVE)
    assert should_route_claim_holding_ack(normalized, intent) is True
    result = ingest_claim_holding_ack(normalized)
    assert result["case_created"] is False
    assert result["active_case_outcome"] == "claim_holding_ack"
    assert _claim_cases() == []
    assert _START_MARKER not in (result.get("reply_text") or "")


# --- 9. Active Add Car + explicit Claim intent → lane switch confirm (not swallowed) ---


def test_invariant_09_active_add_car_explicit_claim_lane_switch_prompt():
    ext = "wm_inv09"
    _seed_active_add_car(ext=ext)
    result = ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="inv09"),
        classify_wecom_intent("我要理赔"),
    )
    assert result["active_case_outcome"] == "claim_lane_switch_prompt"
    assert result["case_created"] is False
    reply = result.get("reply_text") or ""
    assert "开始事故记录" in reply
    assert "继续加车" in reply
    assert _START_MARKER not in reply


# --- 10. Duplicate explicit start does not create multiple Claims ---


def test_invariant_10_duplicate_explicit_start_single_claim():
    ext = "wm_inv10"
    first = ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="inv10a"),
        classify_wecom_intent("我要理赔"),
    )
    second = ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="inv10b"),
        classify_wecom_intent("我要理赔"),
    )
    assert first["case_created"] is True
    assert second["case_created"] is False
    assert first["case_id"] == second["case_id"]
    assert len(_claim_cases()) == 1
    case = get_case_by_id(first["case_id"]) or {}
    started = [e for e in (case.get("claim_timeline") or []) if e.get("event_type") == "claim_started"]
    assert len(started) == 1


# --- 11. Lane switch confirm then start — temporal order ---


def test_invariant_11_lane_switch_confirm_before_start_card():
    ext = "wm_inv11"
    _seed_active_add_car(ext=ext)
    prompt = ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="inv11a"),
        classify_wecom_intent("我要理赔"),
    )
    assert prompt["active_case_outcome"] == "claim_lane_switch_prompt"
    confirm = ingest_claim_lane_switch_choice(_normalized("开始事故记录", ext=ext, msg_id="inv11b"))
    assert confirm["case_created"] is True
    assert confirm["active_case_outcome"] == "claim_start_card_sent"
    assert _START_MARKER in (confirm.get("reply_text") or "")
    assert len(_claim_cases()) == 1


# --- 12. Start Card copy contract (ceremony marker) ---


def test_invariant_12_start_card_ceremony_copy():
    start = build_claim_start_card_reply()
    assert "事故记录已开始" in start
    assert "提交给陈总审核" in start
    assert "这只是资料收集，不代表已经正式向保险公司报案。" in start
