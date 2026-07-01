"""WeCom synthetic message → Active Case integration tests (Track A readiness)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import count_stored_cases, get_case_by_id, list_all_cases
from services.fiqa_api.wecom.active_case_bridge import (
    find_case_by_wecom_msg_id,
    ingest_wecom_text_to_active_case,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.slice import process_kf_msg_or_event
from services.fiqa_api.wecom.sync_msg import WECOM_ADMIN_BLOCKED_ERRCODE, sync_kf_messages
from services.fiqa_api.wecom.synthetic_fixtures import (
    SYNTHETIC_ADD_CAR_NO_PHONE,
    SYNTHETIC_ADD_CAR_WITH_PHONE,
    SYNTHETIC_DUPLICATE,
    SYNTHETIC_FOLLOWUP_VIN,
    SYNTHETIC_UNRELATED,
)


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


def _setup_json_store() -> None:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)


def test_normalize_contract_fields() -> None:
    event = normalize_text_message(SYNTHETIC_ADD_CAR_WITH_PHONE)
    assert event["channel"] == "wecom_kf"
    assert event["msgtype"] == "text"
    assert event["text"] == SYNTHETIC_ADD_CAR_WITH_PHONE["text"]["content"]
    assert event["phone"] == "6265550101"
    assert event["external_userid"] == SYNTHETIC_ADD_CAR_WITH_PHONE["external_userid"]
    assert event["open_kfid"] == SYNTHETIC_ADD_CAR_WITH_PHONE["open_kfid"]
    assert event["raw"] == SYNTHETIC_ADD_CAR_WITH_PHONE


def test_add_car_no_phone_does_not_create_case(caplog) -> None:
    _setup_json_store()
    normalized = normalize_text_message(SYNTHETIC_ADD_CAR_NO_PHONE)
    intent = classify_wecom_intent(normalized["text"])

    with caplog.at_level("INFO"):
        result = ingest_wecom_text_to_active_case(normalized, intent)

    assert result["outcome"] == "need_phone"
    assert result["case_id"] is None
    assert result["readiness_gate"] == "NEED_INFO"
    assert count_stored_cases() == 0
    assert any("wecom_identity_missing_v1" in r.message for r in caplog.records)


def test_add_car_with_phone_creates_one_active_case() -> None:
    _setup_json_store()
    normalized = normalize_text_message(SYNTHETIC_ADD_CAR_WITH_PHONE)
    intent = classify_wecom_intent(normalized["text"])

    result = ingest_wecom_text_to_active_case(normalized, intent)

    assert result["outcome"] == "created"
    assert result["case_created"] is True
    assert result["case_id"]
    assert count_stored_cases() == 1

    stored = get_case_by_id(result["case_id"])
    assert stored is not None
    assert stored.get("customer_phone") == "6265550101"
    assert stored.get("service_lane") == "add_car"
    assert stored.get("p16_broker_packet") in (None, {})


def test_second_message_same_phone_attaches_to_same_case() -> None:
    _setup_json_store()
    first = normalize_text_message(SYNTHETIC_ADD_CAR_WITH_PHONE)
    first_intent = classify_wecom_intent(first["text"])
    created = ingest_wecom_text_to_active_case(first, first_intent)
    assert created["outcome"] == "created"
    case_id = created["case_id"]

    followup = normalize_text_message(SYNTHETIC_FOLLOWUP_VIN)
    followup_intent = classify_wecom_intent(followup["text"])
    attached = ingest_wecom_text_to_active_case(followup, followup_intent)

    assert attached["outcome"] == "attached"
    assert attached["case_id"] == case_id
    assert count_stored_cases() == 1

    stored = get_case_by_id(case_id)
    assert stored is not None
    events = stored.get("evidence_events") or []
    assert len(events) == 2


def test_unrelated_message_no_case() -> None:
    _setup_json_store()
    normalized = normalize_text_message(SYNTHETIC_UNRELATED)
    intent = classify_wecom_intent(normalized["text"])
    result = ingest_wecom_text_to_active_case(normalized, intent)
    assert result["outcome"] == "intent_not_actionable"
    assert count_stored_cases() == 0


def test_duplicate_msg_id_is_idempotent() -> None:
    _setup_json_store()
    normalized = normalize_text_message(SYNTHETIC_DUPLICATE)
    intent = classify_wecom_intent(normalized["text"])
    first = ingest_wecom_text_to_active_case(normalized, intent)
    assert first["outcome"] == "created"

    second = ingest_wecom_text_to_active_case(normalized, intent)
    assert second["outcome"] == "duplicate_msg"
    assert second["case_id"] == first["case_id"]
    assert count_stored_cases() == 1
    assert find_case_by_wecom_msg_id("msg_add_car_002") == first["case_id"]


def test_slice_pipeline_with_synthetic_pull(monkeypatch, caplog) -> None:
    _setup_json_store()
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()
    assert cfg is not None

    def pull(_cfg, *, token, open_kf_id):
        return [SYNTHETIC_ADD_CAR_WITH_PHONE]

    with caplog.at_level("INFO"):
        results = process_kf_msg_or_event(
            cfg,
            callback_token="t",
            open_kf_id="wktest001",
            pull_messages=pull,
        )

    assert len(results) == 1
    assert results[0]["active_case_outcome"] == "created"
    assert results[0]["case_created"] is True
    assert count_stored_cases() == 1
    assert any("wecom_event_normalized_v1" in r.message for r in caplog.records)
    assert any("wecom_active_case_created_or_attached_v1" in r.message for r in caplog.records)


def test_sync_msg_48002_classified_as_admin_blocker(monkeypatch) -> None:
    from services.fiqa_api.wecom.config import WeComKfConfig

    cfg = WeComKfConfig(token="t", encoding_aes_key="a" * 43, corp_id="ww", kf_secret="s")

    class FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"errcode": WECOM_ADMIN_BLOCKED_ERRCODE, "errmsg": "api forbidden"}

    monkeypatch.setattr(
        "services.fiqa_api.wecom.sync_msg.get_access_token",
        lambda _cfg: "fake_token",
    )
    monkeypatch.setattr(
        "services.fiqa_api.wecom.sync_msg.httpx.post",
        lambda *a, **k: FakeResp(),
    )

    with pytest.raises(RuntimeError, match="wecom_sync_msg_admin_blocked_v1"):
        sync_kf_messages(cfg, token="tok", open_kf_id="wk1")
