"""P19H-3c-2 — Claim C1 WeCom H5 upload button tests."""

from __future__ import annotations

import json
import logging
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
from services.fiqa_api.inbox_triage.h5_task_token import (
    FLOW_CLAIM_EVIDENCE_PACK,
    issue_h5_task_token,
    verify_h5_task_token,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.reply import build_h5_vin_start_card_payload
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.routing_observability import routing_decision_from_log_message
from services.fiqa_api.wecom.slice import process_kf_msg_or_event
from services.fiqa_api.wecom.workflow_scenario_simulator import (
    SCENARIO_ADD_VEHICLE_TO_CLAIM_INTERRUPT,
    SCENARIO_NO_ACTIVE_CLAIM_BASICS,
    WorkflowScenarioSession,
    run_predefined_scenario,
)
from services.fiqa_api.routes.h5_task_upload import router as h5_router

_BASICS_TEXT = "今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门"
_FORBIDDEN_SNIPPETS = (
    "已经报案",
    "理赔已经提交",
    "已联系保险公司",
    "是对方责任",
    "一定会赔",
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


@pytest.fixture(autouse=True)
def _h5_secret(monkeypatch):
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")


def _triage_stub_claim() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Review claim evidence.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
    }


def _triage_stub_add_car() -> dict:
    return {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": "Review.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
    }


def _normalized(text: str, *, ext: str = "wm_h3c2", msg_id: str = "m1") -> dict:
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


def _h5_client() -> TestClient:
    app = FastAPI()
    app.include_router(h5_router)
    return TestClient(app)


def _view_url_from_menu(menu: dict) -> str | None:
    for item in menu.get("list") or []:
        if item.get("type") == "view":
            return str((item.get("view") or {}).get("url") or "").strip() or None
    return None


def _token_from_menu(menu: dict) -> str:
    url = _view_url_from_menu(menu)
    assert url
    return url.rsplit("/", 1)[-1]


def _assert_no_forbidden_copy(text: str) -> None:
    for phrase in _FORBIDDEN_SNIPPETS:
        assert phrase not in (text or "")


def _send_basics_c1(*, ext: str = "wm_h3c2_c1") -> dict:
    ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="m_start"),
        classify_wecom_intent("我要理赔"),
    )
    return ingest_claim_basics_message(
        _normalized(_BASICS_TEXT, ext=ext, msg_id="m_basics"),
        classify_wecom_intent(_BASICS_TEXT),
    )


def test_01_c1_includes_h5_upload_button():
    result = _send_basics_c1()
    assert result["active_case_outcome"] == "claim_c1_sent"
    reply = result["reply_text"] or ""
    assert "【理赔资料 · 第 1 步完成 ✅】" in reply
    assert "请点击下面按钮上传事故照片" in reply

    menu = result.get("menu_payload")
    assert isinstance(menu, dict)
    assert any(
        item.get("type") == "view"
        and "上传事故照片" in str((item.get("view") or {}).get("content") or "")
        for item in menu.get("list") or []
    )

    token = _token_from_menu(menu)
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.case_id == result["case_id"]
    assert claims.lane == "claim"
    assert claims.flow == FLOW_CLAIM_EVIDENCE_PACK
    assert claims.slots[0] == "customer_damage_photo"


def test_02_h5_link_opens_first_claim_slot_metadata():
    result = _send_basics_c1(ext="wm_h3c2_meta")
    menu = result["menu_payload"]
    assert menu
    token = _token_from_menu(menu)
    resp = _h5_client().get(f"/api/h5/tasks/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["lane"] == "claim"
    assert data["flow"] == FLOW_CLAIM_EVIDENCE_PACK
    assert data["slot_key"] == "customer_damage_photo"
    assert "理赔资料" in data["title"]
    assert "车损照片" in data["title"]
    assert "不代表 claim 已正式提交" in data["safety_copy"]
    assert data["eligible_for_ocr"] is False


def test_03_add_vehicle_active_to_claim_c1_full_path(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()

    ext = "wm_h3c2_path"
    saved = save_case("add car", _triage_stub_add_car(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid=ext)

    def pull(_cfg, *, token, open_kf_id):
        nonlocal msg_counter
        msg_counter += 1
        return [
            {
                "msgid": f"m_path_{msg_counter}",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": texts[msg_counter - 1]},
            }
        ]

    texts = ["我要理赔", "开始理赔", _BASICS_TEXT]
    msg_counter = 0
    results = []
    for _ in texts:
        results.extend(
            process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
        )

    final = results[-1]
    assert final["active_case_outcome"] == "claim_c1_sent"
    assert "【理赔资料 · 第 1 步完成 ✅】" in (final.get("reply_text") or "")
    menu = final.get("menu_payload")
    assert menu
    assert _view_url_from_menu(menu)
    assert "加车资料流程正在进行" not in (final.get("reply_text") or "")


def test_04_no_active_case_claim_c1_has_h5_button():
    result = _send_basics_c1(ext="wm_h3c2_no_active")
    assert result["active_case_outcome"] == "claim_c1_sent"
    menu = result.get("menu_payload")
    assert menu
    token = _token_from_menu(menu)
    assert verify_h5_task_token(token) is not None


def test_05_forbidden_copy_absent():
    result = _send_basics_c1(ext="wm_h3c2_safe")
    reply = result["reply_text"] or ""
    menu = result.get("menu_payload") or {}
    combined = "\n".join(
        [
            reply,
            str(menu.get("head_content") or ""),
            str(menu.get("tail_content") or ""),
        ]
    )
    _assert_no_forbidden_copy(combined)


def test_06_add_vehicle_h5_start_card_unchanged():
    add_car_token = issue_h5_task_token(case_id="case_add_car_only", lane="add_car", slot="vin_photo")
    add_claims = verify_h5_task_token(add_car_token)
    assert add_claims is not None
    assert add_claims.lane == "add_car"

    menu = build_h5_vin_start_card_payload(h5_url="https://example.test/task/upload/h5t1.addcar")
    assert any(
        item.get("type") == "view"
        and "开始上传资料" in str((item.get("view") or {}).get("content") or "")
        for item in menu.get("list") or []
    )


def test_07_routing_decision_log_unchanged(caplog):
    ext = "wm_h3c2_route"
    with caplog.at_level(logging.INFO):
        result = _send_basics_c1(ext=ext)
    assert result["active_case_outcome"] == "claim_c1_sent"

    logs = [
        routing_decision_from_log_message(r.getMessage())
        for r in caplog.records
        if routing_decision_from_log_message(r.getMessage())
    ]
    c1_logs = [x for x in logs if x and x.get("response_type") == "claim_c1"]
    assert c1_logs
    log = c1_logs[-1]
    assert log["priority_rule"] == "active_claim_basics_collection"
    assert log["decision"] == "send_claim_c1"
    assert log["response_type"] == "claim_c1"


def test_08_scenario_simulator_checks_h5_button():
    name, steps = SCENARIO_ADD_VEHICLE_TO_CLAIM_INTERRUPT
    result = run_predefined_scenario(name, list(steps), seed_add_vehicle=True)
    assert result.passed, result.summary

    name2, steps2 = SCENARIO_NO_ACTIVE_CLAIM_BASICS
    result2 = run_predefined_scenario(name2, list(steps2), seed_add_vehicle=False)
    assert result2.passed, result2.summary

    session = WorkflowScenarioSession(external_userid="wm_h3c2_token_check")
    session.setup_wecom_env()
    ingest_claim_basics_message(
        _normalized("我要理赔", ext=session.external_userid, msg_id="s1"),
        classify_wecom_intent("我要理赔"),
    )
    turn = session.route_inbound_text(_BASICS_TEXT)
    menu = turn.outcome.get("menu_payload")
    assert menu
    token = _token_from_menu(menu)
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.flow == FLOW_CLAIM_EVIDENCE_PACK
    assert claims.slots[0] == "customer_damage_photo"
