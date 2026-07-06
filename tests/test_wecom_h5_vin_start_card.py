"""P19D-3 — WeCom Add Vehicle Start Card → H5 VIN task link integration tests."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.h5_task_link import mint_h5_task_link
from services.fiqa_api.inbox_triage.h5_task_token import verify_h5_task_token
from services.fiqa_api.routes.h5_task_upload import router as h5_router
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply import build_h5_vin_start_card_payload
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event
from services.fiqa_api.wecom.sync_cursor import reset_sync_cursor_memory_for_tests
from services.fiqa_api.inbox_triage.case_store import count_stored_cases, get_case_by_id

_H5_URL_RE = re.compile(r"https://example\.test/task/upload/h5t1\.[^/\s]+")


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


@pytest.fixture(autouse=True)
def _reset_dedup(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("WECOM_SLICE_SEND_REPLY", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    reset_sync_cursor_memory_for_tests()
    yield
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    reset_sync_cursor_memory_for_tests()


def _setup_json_store() -> None:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)


def _msg(msg_id: str, text: str, *, external_userid: str = "wmexternal001") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": external_userid,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": text},
    }


def _b0_cfg(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://example.test")
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")
    load_wecom_kf_config.cache_clear()
    return load_wecom_kf_config()


def _extract_token_from_masked_url(masked: str) -> str | None:
    if not masked or "…" in masked:
        return None
    m = re.search(r"/task/upload/(h5t1\.[^/\s]+)", masked)
    return m.group(1) if m else None


def test_h5_vin_start_card_payload_copy():
    url = "https://example.test/task/upload/h5t1.abc.sig"
    menu = build_h5_vin_start_card_payload(h5_url=url)
    head = menu["head_content"]
    tail = menu["tail_content"]
    assert "加车资料收集" in head
    assert "VIN 照片" in head
    assert "行驶证" in head
    assert "保险卡" in head
    assert "大约 2 分钟" in head
    assert "上传所有" not in head
    assert "一次发多张" not in head
    assert "OCR" not in head
    assert "https://example.test" not in tail
    assert "请回复：链接" in tail
    view_items = [i for i in menu["list"] if i.get("type") == "view"]
    assert view_items
    assert view_items[0]["view"]["url"] == url
    assert view_items[0]["view"]["content"] == "开始上传照片"


def test_add_car_text_creates_case_and_h5_link(monkeypatch):
    _setup_json_store()
    cfg = _b0_cfg(monkeypatch)
    captured: dict = {}

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_add_car_h5", "我要加车")]

    def fake_dispatch(_cfg, normalized, *, send_enabled, menu_payload, text_content, outcome):
        captured["menu"] = menu_payload
        captured["outcome"] = outcome

    monkeypatch.setattr(
        "services.fiqa_api.wecom.slice._dispatch_reply",
        fake_dispatch,
    )

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)

    assert len(results) == 1
    outcome = results[0]
    assert outcome["active_case_outcome"] == "start_card_sent"
    assert outcome["case_created"] is True
    assert outcome["case_id"]
    assert outcome["h5_task_link_masked"]
    assert "/task/upload/h5t1." in outcome["h5_task_link_masked"]
    assert count_stored_cases() == 1

    menu = captured["menu"]
    assert menu is not None
    url = menu["list"][0]["view"]["url"]
    assert _H5_URL_RE.match(url)
    assert "wmexternal" not in url

    token = url.rsplit("/", 1)[-1]
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.case_id == outcome["case_id"]
    assert claims.lane == "add_car"
    assert claims.is_flow_token
    assert claims.flow == "add_vehicle_photo_flow"
    assert claims.slots == ("vin_photo", "registration_photo", "insurance_card_photo")


def test_add_car_reuses_existing_draft_case(monkeypatch):
    _setup_json_store()
    cfg = _b0_cfg(monkeypatch)

    def pull_first(_cfg, *, token, open_kf_id):
        return [_msg("m_first", "我要加车", external_userid="wm_reuse")]

    process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull_first)
    first_case = list_all_case_ids()[0]

    def pull_second(_cfg, *, token, open_kf_id):
        return [_msg("m_second", "帮我加一辆车", external_userid="wm_reuse")]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull_second)
    assert results[0]["case_id"] == first_case
    assert results[0]["active_case_outcome"] != "start_card_sent"


def list_all_case_ids():
    from services.fiqa_api.inbox_triage.case_store import list_all_cases

    return [c["case_id"] for c in list_all_cases()]


def test_hello_no_h5_link(monkeypatch):
    _setup_json_store()
    cfg = _b0_cfg(monkeypatch)

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_hello", "你好")]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    assert results[0].get("h5_task_link_masked") is None
    assert results[0]["case_created"] is False


def test_premium_claim_coverage_no_h5_vin_link(monkeypatch):
    _setup_json_store()
    cfg = _b0_cfg(monkeypatch)
    cases = [
        ("m_prem", "陈总，我保险又涨了，有没有便宜一点？"),
        ("m_claim", "我撞车了"),
        ("m_cov", "DMV说我没保险"),
    ]

    for msg_id, text in cases:
        def pull(_cfg, *, token, open_kf_id, _mid=msg_id, _text=text):
            return [_msg(_mid, _text, external_userid=f"wm_{_mid}")]

        results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
        assert results[0].get("h5_task_link_masked") is None
        reply = results[0].get("reply_text") or ""
        assert "/task/upload/h5t1." not in reply


def test_h5_task_api_validates_wecom_minted_token(monkeypatch):
    _setup_json_store()
    cfg = _b0_cfg(monkeypatch)
    captured: dict = {}

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_api", "我要加车")]

    def fake_dispatch(_cfg, normalized, *, send_enabled, menu_payload, text_content, outcome):
        captured["menu"] = menu_payload

    monkeypatch.setattr("services.fiqa_api.wecom.slice._dispatch_reply", fake_dispatch)

    process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    url = captured["menu"]["list"][0]["view"]["url"]
    token = url.rsplit("/", 1)[-1]

    app = FastAPI()
    app.include_router(h5_router)
    client = TestClient(app)
    resp = client.get(f"/api/h5/tasks/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["flow"] == "add_vehicle_photo_flow"
    assert data["lane"] == "add_car"
    assert data["current_step"] == "vin_photo"
    assert "VIN" in data["task_label"]


def test_add_car_with_open_premium_case_creates_add_car_draft(monkeypatch):
    """P19D-3 regression: H5 token must bind add_car case, not other open lane."""
    _setup_json_store()
    cfg = _b0_cfg(monkeypatch)
    from services.fiqa_api.wecom.intent import classify_wecom_intent
    from services.fiqa_api.wecom.minimal_lanes import ingest_wecom_text_to_minimal_lane
    from services.fiqa_api.wecom.normalize import normalize_text_message

    prem_norm = normalize_text_message(
        _msg(
            "m_prem_open",
            "陈总，我 Uber Black 保险又涨了，现在一年 15500，有没有便宜一点？",
            external_userid="wm_prem_then_add",
        )
    )
    prem_intent = classify_wecom_intent(prem_norm["text"])
    prem_result = ingest_wecom_text_to_minimal_lane(prem_norm, prem_intent)
    prem_id = prem_result["case_id"]

    captured: dict = {}

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_add_car_prem", "我要加车", external_userid="wm_prem_then_add")]

    def fake_dispatch(_cfg, normalized, *, send_enabled, menu_payload, text_content, outcome):
        captured["outcome"] = outcome
        captured["menu"] = menu_payload

    monkeypatch.setattr("services.fiqa_api.wecom.slice._dispatch_reply", fake_dispatch)

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    outcome = results[0]
    assert outcome["case_id"] != prem_id
    assert outcome["case_created"] is True
    stored = get_case_by_id(outcome["case_id"])
    assert stored is not None
    assert stored.get("service_lane") == "add_car"

    url = captured["menu"]["list"][0]["view"]["url"]
    token = url.rsplit("/", 1)[-1]
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.case_id == outcome["case_id"]


def test_mint_h5_task_link_no_full_external_userid(monkeypatch):
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://example.test")
    url = mint_h5_task_link(
        case_id="case_link_test",
        external_userid="wm_full_secret_external_userid_12345",
    )
    assert "wm_full_secret" not in url
    token = url.rsplit("/", 1)[-1]
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.user_ref
    assert len(claims.user_ref) == 8
