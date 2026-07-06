"""WeCom synthetic message → Active Case integration tests (Track A readiness)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    count_stored_cases,
    get_case_by_id,
    list_all_cases,
    update_case_customer,
)
from services.fiqa_api.wecom.active_case_bridge import (
    BrokerConfirmError,
    confirm_case_by_broker,
    find_case_by_wecom_msg_id,
    find_open_draft_case_by_external_userid,
    ingest_wecom_text_to_active_case,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event
from services.fiqa_api.wecom.sync_cursor import reset_sync_cursor_memory_for_tests
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


@pytest.fixture(autouse=True)
def _reset_reply_dedup(monkeypatch):
    """Deterministic in-process dedup guard; strip host DB URL so tests
    exercise the in-process claim path, not a real Postgres connection.

    Also clears flags that `services.fiqa_api.app_main` (imported by other
    test modules collected in the same pytest session) loads from a local
    `.env.cloudrun` via `load_dotenv(override=False)` — if that file exists
    on disk, those real values would otherwise leak into these tests and
    silently flip send-enabled / production-mode behavior depending on
    collection order.
    """
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("WECOM_SLICE_SEND_REPLY", raising=False)
    monkeypatch.delenv("WECOM_B0_ACTIVE_WORKSPACE", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_JSON_READ_FALLBACK", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_PG_DUAL_WRITE", raising=False)
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


def _click_msg(msg_id: str, *, menu_id: str, content: str = "click") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": "wmexternal001",
        "origin": 3,
        "msgtype": "text",
        "send_time": 1719750000,
        "text": {"content": content, "menu_id": menu_id},
    }


def _text_only_msg(msg_id: str, content: str) -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": "wmexternal001",
        "origin": 3,
        "msgtype": "text",
        "send_time": 1719750000,
        "text": {"content": content},
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
    cfg = load_wecom_kf_config()
    assert cfg is not None
    return cfg


class TestTrackB0StartCard:
    """Track B0.1 — explicit Start Card before any case creation.

    Governed by docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md and
    P16_CUSTOMER_FIRST_CONSTITUTION.md Rule 8 (One Business Flow At A Time).
    Behind WECOM_B0_ACTIVE_WORKSPACE (default OFF). No case is created by the
    Start Card *send* or by "Later"/"Talk to Broker" clicks. The "Start" click
    itself now creates the Draft Case (Track B0.2 — see TestTrackB0DraftCase
    below for that coverage).
    """

    def test_hello_message_no_start_card(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        def pull(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_hello", "你好")]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert len(results) == 1
        outcome = results[0]
        assert outcome["active_case_outcome"] != "start_card_sent"
        assert outcome["internal_intent"] == "unclear"
        assert outcome["guided_menu_required"] is True
        assert outcome["case_created"] is False
        assert count_stored_cases() == 0

    def test_add_car_bought_car_sends_start_card_no_case(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        intent = classify_wecom_intent("我买了一辆车")
        assert intent.intent == "add_car"
        assert intent.confidence == "high"

        def pull(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_bought_car", "我买了一辆车")]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert len(results) == 1
        outcome = results[0]
        assert outcome["active_case_outcome"] == "start_card_sent"
        assert outcome["case_created"] is True
        assert outcome["case_id"]
        assert outcome.get("h5_task_link_masked")
        assert count_stored_cases() == 1

    def test_add_car_want_to_add_sends_start_card_no_case(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        intent = classify_wecom_intent("我想加车")
        assert intent.intent == "add_car"
        assert intent.confidence == "high"

        def pull(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_add_car", "我想加车")]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert len(results) == 1
        outcome = results[0]
        assert outcome["active_case_outcome"] == "start_card_sent"
        assert outcome["case_created"] is True
        assert outcome["case_id"]
        assert outcome.get("h5_task_link_masked")
        assert count_stored_cases() == 1

    def test_start_click_creates_draft_case(self, monkeypatch) -> None:
        """Track B0.2 supersedes the old B0.1-only "no case" expectation for
        this specific click — see TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md §12
        milestone table (B0.2: "Draft Case creation on Start")."""
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        def pull(_cfg, *, token, open_kf_id):
            return [_click_msg("m_start_click", menu_id="start_add_car", content="Start / 开始")]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert len(results) == 1
        outcome = results[0]
        assert outcome["internal_intent"] == "start_add_car_click"
        assert outcome["active_case_outcome"] == "start_add_car_click"
        assert outcome["case_created"] is True
        assert outcome["case_id"]
        assert count_stored_cases() == 1

    def test_start_click_db_failure_does_not_crash_callback_or_block_batch(
        self, monkeypatch
    ) -> None:
        """P0 regression: a DB exception (e.g. Postgres cold-start / transient
        network failure) while creating the Draft Case on "Start" must not
        propagate out of `process_kf_msg_or_event` — the module's own
        docstring promises "Never raises". Before this fix, an unhandled
        exception here 500'd the whole callback (no reply sent for the
        failed message, WeCom retries the callback -> duplicate sends for
        *other* messages), which is exactly what was observed in production
        on 2026-07-04: Start click -> no visible follow-up reply.

        Also asserts the failure is scoped to the one message: a second,
        unrelated message in the same sync_msg batch still gets a reply.
        """
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        def _boom(_normalized):
            raise RuntimeError("connection is bad: simulated Postgres unreachable")

        monkeypatch.setattr(
            "services.fiqa_api.wecom.slice.create_or_attach_draft_case_for_start_click",
            _boom,
        )

        def pull(_cfg, *, token, open_kf_id):
            return [
                _click_msg("m_start_click_fail", menu_id="start_add_car", content="Start / 开始"),
                _text_only_msg("m_after_fail", "你好"),
            ]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert len(results) == 2
        failed, other = results[0], results[1]
        assert failed["msg_id"] == "m_start_click_fail"
        assert failed["reply_sent"] is False
        assert "processing_error" in failed
        assert "simulated Postgres unreachable" in failed["processing_error"]
        assert count_stored_cases() == 0

        # The batch keeps going — the next message is unaffected.
        assert other["msg_id"] == "m_after_fail"
        assert other.get("reply_send_error") is None

    def test_later_click_friendly_ack_no_case(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        def pull(_cfg, *, token, open_kf_id):
            return [
                _click_msg("m_later_click", menu_id="start_add_car_decline", content="Later / 稍后")
            ]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert len(results) == 1
        outcome = results[0]
        assert outcome["internal_intent"] == "start_add_car_decline_click"
        assert outcome["case_created"] is False
        assert outcome["case_id"] is None
        assert count_stored_cases() == 0
        assert "没关系" in outcome["reply_text"] or "No problem" in outcome["reply_text"]

    def test_broker_click_friendly_ack_no_case(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        def pull(_cfg, *, token, open_kf_id):
            return [
                _click_msg(
                    "m_broker_click", menu_id="start_add_car_broker", content="Talk to Broker / 联系经纪人"
                )
            ]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert len(results) == 1
        outcome = results[0]
        assert outcome["internal_intent"] == "start_add_car_broker_click"
        assert outcome["case_created"] is False
        assert outcome["case_id"] is None
        assert count_stored_cases() == 0
        assert "经纪人" in outcome["reply_text"]

    def test_start_card_send_is_not_duplicated_on_repeat_delivery(self, monkeypatch) -> None:
        """P0: Start Card trigger path has no case to dedup against, so it
        must rely on the msg_id reply guard directly — same msg_id processed
        twice (callback retry / sync_msg replay) must send the Start Card
        menu exactly once."""
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)
        monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
        menu_calls: list[dict] = []

        def fake_send_menu_reply(cfg, *, external_userid, open_kf_id, menu):
            menu_calls.append({"external_userid": external_userid, "menu": menu})
            return {"errcode": 0}

        monkeypatch.setattr("services.fiqa_api.wecom.slice.send_menu_reply", fake_send_menu_reply)

        def pull(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_start_card_retry", "我想加车")]

        first = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )
        second = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert first[0]["active_case_outcome"] == "start_card_sent"
        assert first[0]["reply_sent"] is True
        assert second[0]["reply_sent"] is False
        assert second[0].get("processing_skipped") is True
        assert second[0].get("skip_reason") == "already_processed"
        assert len(menu_calls) == 1
        assert count_stored_cases() == 1

    def test_later_click_ack_sent_once_on_repeat_delivery(self, monkeypatch) -> None:
        """"Later" click creates no case either — same coverage as above for
        the friendly-ack-only click path."""
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)
        monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
        text_calls: list[dict] = []

        def fake_send_text_reply(cfg, *, external_userid, open_kf_id, content):
            text_calls.append({"external_userid": external_userid, "content": content})
            return {"errcode": 0}

        monkeypatch.setattr("services.fiqa_api.wecom.slice.send_text_reply", fake_send_text_reply)

        def pull(_cfg, *, token, open_kf_id):
            return [
                _click_msg("m_later_retry", menu_id="start_add_car_decline", content="Later / 稍后")
            ]

        first = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )
        second = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert first[0]["reply_sent"] is True
        assert second[0]["reply_sent"] is False
        assert len(text_calls) == 1

    def test_flag_off_preserves_track_a_behavior(self, monkeypatch) -> None:
        """Default OFF must be a no-op: today's immediate-create path is untouched."""
        _setup_json_store()
        monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
        monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
        monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
        monkeypatch.setenv("WECOM_KF_SECRET", "secret")
        monkeypatch.delenv("WECOM_B0_ACTIVE_WORKSPACE", raising=False)
        load_wecom_kf_config.cache_clear()
        cfg = load_wecom_kf_config()
        assert cfg is not None

        def pull(_cfg, *, token, open_kf_id):
            return [SYNTHETIC_ADD_CAR_WITH_PHONE]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert len(results) == 1
        assert results[0]["active_case_outcome"] == "created"
        assert results[0]["case_created"] is True
        assert count_stored_cases() == 1


class TestTrackB0DraftCase:
    """Track B0.2 — "Start" creates ONE Draft Case bound to external_userid;
    subsequent messages reuse the existing triage merge to update it.

    Governed by docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md §4.1/§9 and
    P16_CUSTOMER_FIRST_CONSTITUTION.md Rule 7 (one active case) and Rule 8
    (one business flow at a time). No Broker Confirm, no Done Card, no claim
    flag here — that is B0.3/B0.4 scope.
    """

    def test_start_click_creates_draft_case(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        def pull(_cfg, *, token, open_kf_id):
            return [_click_msg("m_start_1", menu_id="start_add_car", content="Start / 开始")]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert len(results) == 1
        outcome = results[0]
        assert outcome["case_created"] is True
        assert outcome["case_id"]
        assert count_stored_cases() == 1

        stored = get_case_by_id(outcome["case_id"])
        assert stored is not None
        assert stored.get("case_status") == "new"
        assert stored.get("service_lane") == "add_car"
        assert stored.get("quote_ready_status") == "need_more"

    def test_conversation_stores_active_case_id(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        def pull(_cfg, *, token, open_kf_id):
            return [_click_msg("m_start_2", menu_id="start_add_car", content="Start / 开始")]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )
        case_id = results[0]["case_id"]

        assert find_open_draft_case_by_external_userid("wmexternal001") == case_id

    def test_vin_zip_driver_date_update_same_draft(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        def start(_cfg, *, token, open_kf_id):
            return [_click_msg("m_start_3", menu_id="start_add_car", content="Start / 开始")]

        started = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=start
        )
        case_id = started[0]["case_id"]

        def vin_turn(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_vin", "VIN 5YJ3E1EA8PF123456")]

        vin_result = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=vin_turn
        )
        assert vin_result[0]["case_id"] == case_id
        assert count_stored_cases() == 1
        stored = get_case_by_id(case_id)
        assert "vin" in [f.lower() for f in stored.get("collected_fields") or []]
        assert stored.get("vehicle_key") == "5YJ3E1EA8PF123456"

        def zip_turn(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_zip", "邮编 91101")]

        process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=zip_turn)
        stored = get_case_by_id(case_id)
        assert "zip" in [f.lower() for f in stored.get("collected_fields") or []]

        def driver_turn(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_driver", "primary driver is Jane Smith")]

        process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=driver_turn
        )
        stored = get_case_by_id(case_id)
        assert "primary_driver" in [f.lower() for f in stored.get("collected_fields") or []]

        def date_turn(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_date", "delivery date 2026-08-01")]

        process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=date_turn)
        stored = get_case_by_id(case_id)
        assert "delivery_date" in [f.lower() for f in stored.get("collected_fields") or []]

        # VIN captured on turn 1 must survive later turns that don't repeat it.
        assert stored.get("vehicle_key") == "5YJ3E1EA8PF123456"
        assert count_stored_cases() == 1

    def test_still_needed_fields_shrink_and_quote_ready_when_complete(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        def start(_cfg, *, token, open_kf_id):
            return [_click_msg("m_start_4", menu_id="start_add_car", content="Start / 开始")]

        started = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=start
        )
        case_id = started[0]["case_id"]
        stored = get_case_by_id(case_id)
        assert set(stored.get("still_needed_fields") or []) == {
            "vin",
            "zip",
            "delivery_date",
            "primary_driver",
        }
        assert stored.get("quote_ready_status") == "need_more"

        turns = [
            "VIN 5YJ3E1EA8PF123456",
            "邮编 91101",
            "primary driver is Jane Smith",
        ]
        for i, content in enumerate(turns):
            def pull(_cfg, *, token, open_kf_id, _content=content, _i=i):
                return [_text_only_msg(f"m_turn_{_i}", _content)]

            process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)

        stored = get_case_by_id(case_id)
        assert set(stored.get("still_needed_fields") or []) == {"delivery_date"}
        assert stored.get("quote_ready_status") == "almost_ready"

        def last_turn(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_turn_last", "delivery date 2026-08-01")]

        process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=last_turn)
        stored = get_case_by_id(case_id)
        assert stored.get("still_needed_fields") == []
        assert stored.get("quote_ready_status") == "quote_ready"
        assert count_stored_cases() == 1

    def test_double_start_click_creates_no_second_draft(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        def first_click(_cfg, *, token, open_kf_id):
            return [_click_msg("m_start_5a", menu_id="start_add_car", content="Start / 开始")]

        first = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=first_click
        )
        case_id = first[0]["case_id"]
        assert first[0]["case_created"] is True

        def second_click(_cfg, *, token, open_kf_id):
            return [_click_msg("m_start_5b", menu_id="start_add_car", content="Start / 开始")]

        second = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=second_click
        )
        assert second[0]["case_created"] is False
        assert second[0]["case_id"] == case_id
        assert count_stored_cases() == 1

    def test_add_car_mention_after_start_does_not_create_second_draft(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        def start(_cfg, *, token, open_kf_id):
            return [_click_msg("m_start_6", menu_id="start_add_car", content="Start / 开始")]

        started = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=start
        )
        case_id = started[0]["case_id"]

        def add_car_again(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_add_car_again", "我想加车")]

        result = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=add_car_again
        )
        assert result[0]["active_case_outcome"] != "start_card_sent"
        assert result[0]["case_created"] is False
        assert result[0]["case_id"] == case_id
        assert count_stored_cases() == 1

    def test_small_talk_after_start_does_not_create_second_draft(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)

        def start(_cfg, *, token, open_kf_id):
            return [_click_msg("m_start_7", menu_id="start_add_car", content="Start / 开始")]

        started = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=start
        )
        case_id = started[0]["case_id"]
        messages_before = len(get_case_by_id(case_id).get("case_messages") or [])

        def hello(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_hello_after_start", "你好")]

        result = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=hello
        )
        assert result[0]["case_created"] is False
        assert result[0]["guided_menu_required"] is True
        assert result[0]["active_case_outcome"] == "intent_not_actionable"
        assert count_stored_cases() == 1
        stored = get_case_by_id(case_id)
        assert stored is not None
        assert stored.get("collected_fields") == []
        assert len(stored.get("case_messages") or []) == messages_before

    def test_flag_off_no_draft_case_behavior(self, monkeypatch) -> None:
        """Default OFF must be a no-op: Start click text is treated like any Track A message."""
        _setup_json_store()
        monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
        monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
        monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
        monkeypatch.setenv("WECOM_KF_SECRET", "secret")
        monkeypatch.delenv("WECOM_B0_ACTIVE_WORKSPACE", raising=False)
        load_wecom_kf_config.cache_clear()
        cfg = load_wecom_kf_config()
        assert cfg is not None

        def pull(_cfg, *, token, open_kf_id):
            return [_click_msg("m_start_off", menu_id="start_add_car", content="Start / 开始")]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert len(results) == 1
        assert results[0]["case_created"] is False
        assert count_stored_cases() == 0
        assert find_open_draft_case_by_external_userid("wmexternal001") is None


class TestTrackB0BrokerConfirm:
    """Track B0.3 — Broker Confirm + Done Card.

    Governed by docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md §7/§9 and
    P16_CUSTOMER_FIRST_CONSTITUTION.md Rule 6 (Broker Confirms Identity) and
    Rule 7 (One Customer = One Active Case). No resolver changes
    (`active_case_resolver.py` untouched) — only the additive
    `broker_confirmed_at` flag (case_store) plus a Done Card send through the
    existing `wecom/send_msg.py` API.
    """

    @staticmethod
    def _start_draft(monkeypatch, *, msg_id: str = "m_confirm_start") -> str:
        cfg = _b0_cfg(monkeypatch)

        def pull(_cfg, *, token, open_kf_id):
            return [_click_msg(msg_id, menu_id="start_add_car", content="Start / 开始")]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )
        return results[0]["case_id"]

    @staticmethod
    def _enable_done_card_send(monkeypatch) -> list[dict]:
        monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
        sent: list[dict] = []

        def fake_send_text_reply(cfg, *, external_userid, open_kf_id, content):
            sent.append(
                {"external_userid": external_userid, "open_kf_id": open_kf_id, "content": content}
            )
            return {"errcode": 0}

        monkeypatch.setattr(
            "services.fiqa_api.wecom.active_case_bridge.send_text_reply", fake_send_text_reply
        )
        return sent

    def test_broker_confirm_blocked_without_phone(self, monkeypatch) -> None:
        _setup_json_store()
        case_id = self._start_draft(monkeypatch)
        stored = get_case_by_id(case_id)
        assert not (stored.get("customer_phone") or "").strip()

        with pytest.raises(BrokerConfirmError):
            confirm_case_by_broker(case_id)

        stored = get_case_by_id(case_id)
        assert stored.get("broker_confirmed_at") is None

    def test_broker_confirm_sets_flag_and_sends_done_card(self, monkeypatch) -> None:
        _setup_json_store()
        case_id = self._start_draft(monkeypatch)
        update_case_customer(case_id, customer_phone="6265550101")
        sent = self._enable_done_card_send(monkeypatch)

        result = confirm_case_by_broker(case_id)

        assert result["outcome"] == "confirmed"
        assert result["already_confirmed"] is False
        assert result["done_card_sent"] is True
        assert len(sent) == 1
        assert "Chen Kui's team has received your request." in sent[0]["content"]
        assert "Insurance updated" not in sent[0]["content"]
        assert "Completed successfully" not in sent[0]["content"]

        stored = get_case_by_id(case_id)
        assert stored.get("broker_confirmed_at")
        activity_types = [a.get("activity_type") for a in stored.get("case_activity") or []]
        assert activity_types.count("broker_confirmed") == 1
        assert count_stored_cases() == 1

    def test_second_confirm_is_idempotent_no_duplicate_send(self, monkeypatch) -> None:
        _setup_json_store()
        case_id = self._start_draft(monkeypatch)
        update_case_customer(case_id, customer_phone="6265550101")
        sent = self._enable_done_card_send(monkeypatch)

        first = confirm_case_by_broker(case_id)
        second = confirm_case_by_broker(case_id)

        assert first["done_card_sent"] is True
        assert second["already_confirmed"] is True
        assert second["done_card_sent"] is False
        assert len(sent) == 1  # exactly ONE Done Card, ever
        assert first["case"]["broker_confirmed_at"] == second["case"]["broker_confirmed_at"]

        stored = get_case_by_id(case_id)
        activity_types = [a.get("activity_type") for a in stored.get("case_activity") or []]
        assert activity_types.count("broker_confirmed") == 1
        assert count_stored_cases() == 1

    def test_followup_message_after_confirm_attaches_same_case_no_duplicate(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)
        case_id = self._start_draft(monkeypatch, msg_id="m_confirm_followup_start")
        update_case_customer(case_id, customer_phone="6265550101")
        confirm_case_by_broker(case_id)

        def followup(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_confirm_followup_1", "VIN 5YJ3E1EA8PF123456")]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=followup
        )

        assert results[0]["case_id"] == case_id
        assert results[0]["case_created"] is False
        assert count_stored_cases() == 1

        stored = get_case_by_id(case_id)
        assert stored.get("broker_confirmed_at")  # still confirmed, unchanged by follow-up
        assert "vin" in [f.lower() for f in stored.get("collected_fields") or []]

    def test_new_add_car_mention_after_confirm_does_not_resend_start_card(self, monkeypatch) -> None:
        _setup_json_store()
        cfg = _b0_cfg(monkeypatch)
        case_id = self._start_draft(monkeypatch, msg_id="m_confirm_no_start_card_start")
        update_case_customer(case_id, customer_phone="6265550101")
        confirm_case_by_broker(case_id)

        def add_car_again(_cfg, *, token, open_kf_id):
            return [_text_only_msg("m_confirm_no_start_card_1", "我想再加一辆车")]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=add_car_again
        )

        assert results[0]["active_case_outcome"] != "start_card_sent"
        assert results[0]["case_created"] is False
        assert results[0]["case_id"] == case_id
        assert count_stored_cases() == 1

    def test_track_a_unchanged_when_flag_off(self, monkeypatch) -> None:
        """Confirm/Done Card are additive; Track A's immediate-create path is
        untouched regardless of WECOM_B0_ACTIVE_WORKSPACE."""
        _setup_json_store()
        monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
        monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
        monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
        monkeypatch.setenv("WECOM_KF_SECRET", "secret")
        monkeypatch.delenv("WECOM_B0_ACTIVE_WORKSPACE", raising=False)
        load_wecom_kf_config.cache_clear()
        cfg = load_wecom_kf_config()
        assert cfg is not None

        def pull(_cfg, *, token, open_kf_id):
            return [SYNTHETIC_ADD_CAR_WITH_PHONE]

        results = process_kf_msg_or_event(
            cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
        )

        assert len(results) == 1
        assert results[0]["active_case_outcome"] == "created"
        assert results[0]["case_created"] is True
        assert count_stored_cases() == 1

        stored = get_case_by_id(results[0]["case_id"])
        assert stored.get("broker_confirmed_at") is None


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
