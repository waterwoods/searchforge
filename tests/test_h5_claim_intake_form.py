"""P19H-3h-1A — Claim H5 structured intake form tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    save_case,
)
from services.fiqa_api.inbox_triage.claim_workbench_display import enrich_claim_for_workbench
from services.fiqa_api.inbox_triage.h5_task_intake import is_h5_intake_continuable
from services.fiqa_api.inbox_triage.h5_task_link import mint_h5_claim_intake_form_link
from services.fiqa_api.inbox_triage.h5_task_token import (
    FLOW_CLAIM_INTAKE_FORM,
    issue_h5_intake_form_token,
    verify_h5_task_token,
)
from services.fiqa_api.routes.h5_task_intake import router as h5_intake_router
from services.fiqa_api.wecom.claim_basics import ingest_claim_status_request
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    SERVICE_LANE_CLAIM,
    derive_claim_phase,
)
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.reply import build_claim_status_card_reply


@pytest.fixture(autouse=True)
def _case_storage(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cases.json"
        path.write_text("[]", encoding="utf-8")
        monkeypatch.setenv("UNIFIED_INTAKE_CASE_STORAGE_PATH", str(path))
        yield


def _app() -> TestClient:
    app = FastAPI()
    app.include_router(h5_intake_router)
    return TestClient(app)


def _triage_stub() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Collect claim basics via H5.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "claim_phase": "accident_basics_in_progress",
    }


def _save_claim_case(case_id: str = "case_claim_h5_intake") -> str:
    saved = save_case(
        "我要理赔",
        _triage_stub(),
        service_lane=SERVICE_LANE_CLAIM,
    )
    return str(saved.get("case_id") or case_id)


def test_intake_form_token_mint_and_verify():
    token = issue_h5_intake_form_token(case_id="case_tok", lane="claim")
    assert token.startswith("h5t1.")
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.flow == FLOW_CLAIM_INTAKE_FORM
    assert claims.is_intake_form_token
    assert claims.case_id == "case_tok"


def test_mint_link_uses_claim_route(monkeypatch):
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://example.test")
    url = mint_h5_claim_intake_form_link(case_id="case_link")
    assert url.startswith("https://example.test/task/claim/h5t1.")


def test_h5_intake_happy_path_and_idempotent_submit():
    case_id = _save_claim_case()
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    intent = "11111111-2222-4333-8444-555555555555"

    r0 = client.get(f"/api/h5/tasks/{token}/intake")
    assert r0.status_code == 200
    data0 = r0.json()
    assert data0["flow"] == FLOW_CLAIM_INTAKE_FORM
    assert data0["current_step"] == "injury"
    assert data0["submitted"] is False

    steps = [
        ("injury", {"anyone_injured": "no"}),
        ("time_location", {"accident_datetime": "今天上午10点", "accident_location": "Irvine Blvd"}),
        ("story", {"accident_description": "我停在红灯前，后车追尾撞上我的车。"}),
        ("vehicle_other_party", {"own_vehicle_info": "2020 Toyota Camry"}),
    ]
    for step, fields in steps:
        resp = client.patch(f"/api/h5/tasks/{token}/fields", json={"step": step, "fields": fields})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["completed_count"] >= 1

    r_review = client.get(f"/api/h5/tasks/{token}/intake")
    assert r_review.json()["current_step"] == "review"

    r_submit = client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": intent},
        headers={"X-Submit-Intent-Id": intent},
    )
    assert r_submit.status_code == 200
    submit_body = r_submit.json()
    assert submit_body["submitted"] is True
    assert submit_body["already_submitted"] is False

    case = get_case_by_id(case_id) or {}
    facts = case.get("known_facts") or {}
    assert facts.get("anyone_injured") == "no"
    assert facts.get("accident_location") == "Irvine Blvd"
    timeline = case.get("claim_timeline") or []
    event_types = [str(e.get("event_type")) for e in timeline]
    assert "h5_step_complete" in event_types
    assert event_types.count("customer_submitted_intake") == 1
    assert derive_claim_phase(case) == CLAIM_PHASE_INTAKE_READY_FOR_BROKER

    r_dup = client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": intent},
        headers={"X-Submit-Intent-Id": intent},
    )
    assert r_dup.status_code == 200
    assert r_dup.json()["already_submitted"] is True
    case2 = get_case_by_id(case_id) or {}
    timeline2 = case2.get("claim_timeline") or []
    assert sum(1 for e in timeline2 if e.get("event_type") == "customer_submitted_intake") == 1


def test_patch_after_submit_rejected():
    case_id = _save_claim_case("case_submit_guard")
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    intent = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"

    for step, fields in [
        ("injury", {"anyone_injured": "no"}),
        ("time_location", {"accident_datetime": "昨天", "accident_location": "LA downtown"}),
        ("story", {"accident_description": "对方变道刮到我左前门，双方下车交换信息。"}),
        ("vehicle_other_party", {"own_vehicle_info": "Honda Civic"}),
    ]:
        assert client.patch(
            f"/api/h5/tasks/{token}/fields",
            json={"step": step, "fields": fields},
        ).status_code == 200

    assert client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": intent},
    ).status_code == 200

    blocked = client.patch(
        f"/api/h5/tasks/{token}/fields",
        json={"step": "story", "fields": {"accident_description": "尝试再次修改经过描述内容。"}},
    )
    assert blocked.status_code == 409


def test_get_intake_returns_upload_url_and_photo_metadata(monkeypatch):
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://example.test")
    case_id = _save_claim_case("case_evidence_meta")
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()

    resp = client.get(f"/api/h5/tasks/{token}/intake")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("upload_url", "").startswith("https://example.test/task/upload/h5t1.")
    assert body.get("attachment_count") == 0
    assert body.get("photo_count") == 0
    assert "evidence" in body.get("steps", [])


def test_evidence_step_skippable_submit_without_evidence_patch():
    case_id = _save_claim_case("case_evidence_skip")
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    intent = "22222222-3333-4333-8444-555555555555"

    for step, fields in [
        ("injury", {"anyone_injured": "no"}),
        ("time_location", {"accident_datetime": "今天上午10点", "accident_location": "Irvine Blvd"}),
        ("story", {"accident_description": "我停在红灯前，后车追尾撞上我的车。"}),
        ("vehicle_other_party", {"own_vehicle_info": "2020 Toyota Camry"}),
    ]:
        assert client.patch(
            f"/api/h5/tasks/{token}/fields",
            json={"step": step, "fields": fields},
        ).status_code == 200

    assert client.get(f"/api/h5/tasks/{token}/intake").json()["current_step"] == "review"

    submit = client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": intent},
        headers={"X-Submit-Intent-Id": intent},
    )
    assert submit.status_code == 200
    assert submit.json()["submitted"] is True


def test_h5_patch_timeline_source_is_h5_task():
    case_id = _save_claim_case("case_h5_source")
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()

    resp = client.patch(
        f"/api/h5/tasks/{token}/fields",
        json={"step": "injury", "fields": {"anyone_injured": "no"}},
    )
    assert resp.status_code == 200

    case = get_case_by_id(case_id) or {}
    events = [e for e in (case.get("claim_timeline") or []) if e.get("event_type") == "h5_step_complete"]
    assert len(events) == 1
    assert events[0].get("source_channel") == "h5_task"


def test_status_card_includes_h5_continue_link_without_duplicate_case(monkeypatch):
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://example.test")
    case_id = _save_claim_case("case_status_h5")
    bind_case_channel_identity(case_id, wecom_external_userid="wm_status_h5")
    case = get_case_by_id(case_id) or {}
    assert is_h5_intake_continuable(case)

    reply = build_claim_status_card_reply(case, h5_intake_url=mint_h5_claim_intake_form_link(case_id=case_id))
    assert "继续补充资料：点击打开资料填写页面" in reply
    assert "/task/claim/h5t1." in reply

    norm = normalize_text_message(
        {
            "msgid": "m_status_h5",
            "open_kfid": "wktest001",
            "external_userid": "wm_status_h5",
            "origin": 3,
            "msgtype": "text",
            "text": {"content": "进度"},
        }
    )
    intent = classify_wecom_intent("进度")
    result = ingest_claim_status_request(norm, intent)
    assert result["case_created"] is False
    assert result["active_case_outcome"] == "claim_status_card"
    assert "继续补充资料" in (result.get("reply_text") or "")


def test_wecom_text_does_not_advance_h5_intake_phase():
    case_id = _save_claim_case("case_no_ai_advance")
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()

    assert client.patch(
        f"/api/h5/tasks/{token}/fields",
        json={"step": "injury", "fields": {"anyone_injured": "no"}},
    ).status_code == 200

    case_before = get_case_by_id(case_id) or {}
    state_before = dict(case_before.get("h5_intake_state") or {})

    # Simulated WeCom free-text would patch known_facts elsewhere — must not auto-submit H5.
    from services.fiqa_api.inbox_triage.case_store import patch_case_known_facts

    patch_case_known_facts(case_id, {"accident_location": "微信补充的地点描述"})

    case_after = get_case_by_id(case_id) or {}
    state_after = dict(case_after.get("h5_intake_state") or {})
    assert state_after.get("submitted_at") is None
    assert state_before.get("field_dedup_keys") == state_after.get("field_dedup_keys")
    assert derive_claim_phase(case_after) != CLAIM_PHASE_INTAKE_READY_FOR_BROKER


def test_workbench_shows_h5_submit_summary_and_timeline():
    case_id = _save_claim_case("case_workbench_h5")
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    intent = "33333333-4444-4333-8444-555555555555"

    for step, fields in [
        ("injury", {"anyone_injured": "no"}),
        ("time_location", {"accident_datetime": "今天上午10点", "accident_location": "Irvine Blvd"}),
        ("story", {"accident_description": "我停在红灯前，后车追尾撞上我的车。"}),
        ("vehicle_other_party", {"own_vehicle_info": "2020 Toyota Camry"}),
    ]:
        assert client.patch(
            f"/api/h5/tasks/{token}/fields",
            json={"step": step, "fields": fields},
        ).status_code == 200

    assert client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": intent},
        headers={"X-Submit-Intent-Id": intent},
    ).status_code == 200

    case = get_case_by_id(case_id) or {}
    row = enrich_claim_for_workbench(case)
    brief = row.get("claim_case_brief") or {}
    key_facts = brief.get("key_facts") or {}
    assert key_facts.get("accident_location") == "Irvine Blvd"
    assert key_facts.get("own_vehicle_info") == "2020 Toyota Camry"
    assert row.get("workflow_phase") == CLAIM_PHASE_INTAKE_READY_FOR_BROKER
    assert row.get("workbench_visible") is True

    timeline = row.get("claim_timeline") or []
    event_types = [str(e.get("event_type")) for e in timeline]
    assert "customer_submitted_intake" in event_types
    assert isinstance(brief.get("missing_info"), list)


def test_status_card_omits_continue_link_after_h5_submit():
    case_id = _save_claim_case("case_status_submitted")
    bind_case_channel_identity(case_id, wecom_external_userid="wm_status_submitted")
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    intent = "44444444-5555-4333-8444-555555555555"

    for step, fields in [
        ("injury", {"anyone_injured": "no"}),
        ("time_location", {"accident_datetime": "昨天", "accident_location": "LA downtown"}),
        ("story", {"accident_description": "对方变道刮到我左前门，双方下车交换信息。"}),
        ("vehicle_other_party", {"own_vehicle_info": "Honda Civic"}),
    ]:
        assert client.patch(
            f"/api/h5/tasks/{token}/fields",
            json={"step": step, "fields": fields},
        ).status_code == 200

    assert client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": intent},
    ).status_code == 200

    case = get_case_by_id(case_id) or {}
    assert not is_h5_intake_continuable(case)

    norm = normalize_text_message(
        {
            "msgid": "m_status_submitted",
            "open_kfid": "wktest001",
            "external_userid": "wm_status_submitted",
            "origin": 3,
            "msgtype": "text",
            "text": {"content": "进度"},
        }
    )
    result = ingest_claim_status_request(norm, classify_wecom_intent("进度"))
    reply = result.get("reply_text") or ""
    assert result["case_created"] is False
    assert "继续补充资料" not in reply
    assert "已提交给陈总审核" in reply


def test_status_card_shows_submitted_phase_label():
    case_id = _save_claim_case("case_status_phase")
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    intent = "99999999-aaaa-4333-8444-555555555555"
    _complete_h5_intake(client, token, intent)
    case = get_case_by_id(case_id) or {}
    reply = build_claim_status_card_reply(case)
    assert "状态：已提交给陈总审核" in reply
    assert "继续补充资料" not in reply


def _complete_h5_intake(client: TestClient, token: str, intent: str) -> dict:
    for step, fields in [
        ("injury", {"anyone_injured": "no"}),
        ("time_location", {"accident_datetime": "今天上午10点", "accident_location": "Irvine Blvd"}),
        ("story", {"accident_description": "我停在红灯前，后车追尾撞上我的车。"}),
        ("vehicle_other_party", {"own_vehicle_info": "2020 Toyota Camry"}),
    ]:
        assert client.patch(
            f"/api/h5/tasks/{token}/fields",
            json={"step": step, "fields": fields},
        ).status_code == 200
    resp = client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": intent},
        headers={"X-Submit-Intent-Id": intent},
    )
    assert resp.status_code == 200
    return resp.json()


def test_submit_returns_completion_summary_and_done_fields():
    case_id = _save_claim_case("case_completion_summary")
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    intent = "55555555-6666-4333-8444-555555555555"

    body = _complete_h5_intake(client, token, intent)
    assert body["submitted"] is True
    summary = body.get("completion_summary") or {}
    assert summary.get("title") == "已提交给陈总 ✅"
    assert "受伤情况" in (summary.get("received") or [])
    assert "照片数量：0 张" in (summary.get("received") or [])
    assert summary.get("next_step")
    assert summary.get("disclaimer")


def test_submit_idempotent_does_not_duplicate_wecom_confirmation_marker(monkeypatch):
    from services.fiqa_api.wecom.config import load_wecom_kf_config

    load_wecom_kf_config.cache_clear()
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")

    case_id = _save_claim_case("case_wecom_confirm_dedup")
    bind_case_channel_identity(
        case_id,
        wecom_external_userid="wm_h5_submit_confirm",
        wecom_open_kf_id="wktest001",
    )
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    intent = "66666666-7777-4333-8444-555555555555"
    sent: list[str] = []

    monkeypatch.setattr(
        "services.fiqa_api.wecom.h5_submit_confirmation.send_text_reply",
        lambda *_a, **_k: sent.append("ok") or {"errcode": 0},
    )

    first = _complete_h5_intake(client, token, intent)
    assert first.get("wecom_confirmation_sent") is True
    case1 = get_case_by_id(case_id) or {}
    state1 = case1.get("h5_intake_state") or {}
    assert state1.get("h5_submit_confirmation_sent_at")

    second = client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": intent},
        headers={"X-Submit-Intent-Id": intent},
    ).json()
    assert second.get("already_submitted") is True
    assert len(sent) == 1

    case2 = get_case_by_id(case_id) or {}
    timeline2 = case2.get("claim_timeline") or []
    assert sum(1 for e in timeline2 if e.get("event_type") == "customer_submitted_intake") == 1


def test_h5_submit_confirmation_is_not_broker_done(monkeypatch):
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")

    case_id = _save_claim_case("case_not_broker_done")
    bind_case_channel_identity(
        case_id,
        wecom_external_userid="wm_not_broker_done",
        wecom_open_kf_id="wktest001",
    )
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    intent = "77777777-8888-4333-8444-555555555555"

    monkeypatch.setattr(
        "services.fiqa_api.wecom.h5_submit_confirmation.send_text_reply",
        lambda *_a, **_k: {"errcode": 0},
    )

    _complete_h5_intake(client, token, intent)
    case = get_case_by_id(case_id) or {}
    assert derive_claim_phase(case) == CLAIM_PHASE_INTAKE_READY_FOR_BROKER
    assert derive_claim_phase(case) != "broker_done"
    timeline = case.get("claim_timeline") or []
    assert not any(e.get("event_type") == "broker_done" for e in timeline)


def test_submit_without_wecom_identity_still_succeeds():
    case_id = _save_claim_case("case_no_wecom")
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    intent = "88888888-9999-4333-8444-555555555555"

    body = _complete_h5_intake(client, token, intent)
    assert body["submitted"] is True
    assert body.get("wecom_confirmation_sent") is False
    case = get_case_by_id(case_id) or {}
    state = case.get("h5_intake_state") or {}
    assert not state.get("h5_submit_confirmation_sent_at")
