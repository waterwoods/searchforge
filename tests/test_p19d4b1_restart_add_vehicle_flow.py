"""P19D-4B.1 — explicit restart creates fresh add-car H5 photo flow."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    count_stored_cases,
    get_case_by_id,
    save_case,
    _load_case_for_mutation,
    _persist_case_after_update,
)
from services.fiqa_api.inbox_triage.h5_task_token import verify_h5_task_token
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.inbox_triage.h5_task_upload import is_explicit_add_car_restart
from services.fiqa_api.routes.h5_task_upload import router as h5_router
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event
import services.fiqa_api.wecom.slice as slice_mod

_H5_URL_RE = re.compile(r"https://example\.test/task/upload/h5t1\.[^/\s]+")


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


def _b0_cfg(monkeypatch) -> object:
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://example.test")
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")
    load_wecom_kf_config.cache_clear()
    return load_wecom_kf_config()


def _completed_add_car_case(*, external_userid: str = "wm_restart_user") -> str:
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    case_id = saved["case_id"]
    bind_case_channel_identity(
        case_id,
        wecom_external_userid=external_userid,
        wecom_open_kf_id="wktest001",
    )
    mut = _load_case_for_mutation(case_id)
    assert mut is not None
    mut["case_attachments"] = [
        {"attachment_id": "a1", "source": "h5_task", "slot_assignment": "vin_photo"},
        {"attachment_id": "a2", "source": "h5_task", "slot_assignment": "registration_photo"},
        {"attachment_id": "a3", "source": "h5_task", "slot_assignment": "insurance_card_photo"},
    ]
    _persist_case_after_update(case_id, mut)
    return case_id


def _msg(msg_id: str, text: str, *, external_userid: str = "wm_restart_user") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": external_userid,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": text},
    }


def _run_slice(cfg, text: str, *, msg_id: str = "m_run", external_userid: str = "wm_restart_user"):
    reset_message_processed_memory_for_tests()
    reset_reply_dedup_memory_for_tests()
    captured: dict = {}

    def fake_dispatch(_cfg, normalized, *, send_enabled, menu_payload, text_content, outcome):
        captured["menu"] = menu_payload
        captured["text"] = text_content
        captured["outcome"] = outcome

    with patch.object(slice_mod, "_dispatch_reply", fake_dispatch):
        results = process_kf_msg_or_event(
            cfg,
            callback_token="t",
            open_kf_id="wktest001",
            pull_messages=lambda _c, **kw: [_msg(msg_id, text, external_userid=external_userid)],
        )
    return results[0], captured


@pytest.mark.parametrize(
    "text",
    [
        "重新加车",
        "重新开始加车",
        "重新上传加车资料",
        "新加一辆车",
        "再加一辆车",
        "换一辆车",
        "另加一辆车",
        "add another car please",
    ],
)
def test_explicit_restart_phrases_detected(text):
    assert is_explicit_add_car_restart(text) is True


def test_ordinary_add_car_not_restart():
    assert is_explicit_add_car_restart("我要加车") is False
    assert is_explicit_add_car_restart("你好") is False


def test_restart_on_completed_flow_creates_new_case(monkeypatch):
    cfg = _b0_cfg(monkeypatch)
    old_id = _completed_add_car_case()
    outcome, captured = _run_slice(cfg, "重新加车", msg_id="m_restart_1")
    assert outcome["case_created"] is True
    assert outcome["case_id"] != old_id
    assert outcome["active_case_outcome"] == "start_card_sent"
    assert count_stored_cases() == 2
    menu = captured["menu"]
    assert menu is not None
    assert "重新开始" in menu["head_content"]
    assert "https://example.test" not in menu["tail_content"]
    url = menu["list"][0]["view"]["url"]
    assert _H5_URL_RE.match(url)
    token = url.rsplit("/", 1)[-1]
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.case_id == outcome["case_id"]
    assert claims.case_id != old_id


def test_restart_h5_get_starts_at_vin_step(monkeypatch):
    cfg = _b0_cfg(monkeypatch)
    _completed_add_car_case()
    outcome, captured = _run_slice(cfg, "重新加车", msg_id="m_restart_h5")
    url = captured["menu"]["list"][0]["view"]["url"]
    token = url.rsplit("/", 1)[-1]
    app = FastAPI()
    app.include_router(h5_router)
    client = TestClient(app)
    resp = client.get(f"/api/h5/tasks/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_step"] == "vin_photo"
    assert data.get("flow_complete") is not True


def test_ordinary_add_car_on_completed_flow_returns_followup(monkeypatch):
    cfg = _b0_cfg(monkeypatch)
    old_id = _completed_add_car_case()
    outcome, captured = _run_slice(cfg, "我要加车", msg_id="m_followup_1")
    assert outcome["case_id"] == old_id
    assert outcome["case_created"] is False
    assert outcome["active_case_outcome"] == "photo_flow_complete_followup"
    assert captured["menu"] is None
    assert captured["text"] is not None
    assert "照片已收到" in captured["text"]
    assert count_stored_cases() == 1


@pytest.mark.parametrize("text", ["新加一辆车", "再加一辆车", "换一辆车"])
def test_restart_variants_create_new_flow(monkeypatch, text):
    cfg = _b0_cfg(monkeypatch)
    old_id = _completed_add_car_case(external_userid=f"wm_{text[:4]}")
    outcome, captured = _run_slice(
        cfg,
        text,
        msg_id=f"m_{text[:4]}",
        external_userid=f"wm_{text[:4]}",
    )
    assert outcome["case_created"] is True
    assert outcome["case_id"] != old_id
    assert captured["menu"] is not None


def test_premium_lane_unaffected_by_restart_logic(monkeypatch):
    cfg = _b0_cfg(monkeypatch)
    outcome, captured = _run_slice(
        cfg,
        "陈总，我保险又涨了",
        msg_id="m_prem",
        external_userid="wm_prem_only",
    )
    assert outcome.get("h5_task_link_masked") is None
    assert outcome.get("detected_intent") != "add_vehicle"
    menu = captured.get("menu")
    if menu:
        view_items = [i for i in menu.get("list") or [] if i.get("type") == "view"]
        assert not view_items


def test_hello_unaffected(monkeypatch):
    cfg = _b0_cfg(monkeypatch)
    outcome, _ = _run_slice(cfg, "你好", msg_id="m_hello", external_userid="wm_hello")
    assert outcome.get("case_created") is False
    assert outcome.get("h5_task_link_masked") is None
