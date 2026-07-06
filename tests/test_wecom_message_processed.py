"""Tests for WeCom msg_id processed guard and sync_msg replay hardening (Q0.10)."""

from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage.case_store import count_stored_cases
from services.fiqa_api.wecom.config import WeComKfConfig, load_wecom_kf_config
from services.fiqa_api.wecom.message_processed import (
    claim_message_processed,
    reset_message_processed_memory_for_tests,
)
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.reply_outbox import reset_wecom_reply_outbox_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event
from services.fiqa_api.wecom.sync_cursor import reset_sync_cursor_memory_for_tests
from services.fiqa_api.wecom.sync_msg import SyncPullResult


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


@pytest.fixture(autouse=True)
def _reset_guards(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("WECOM_SLICE_SEND_REPLY", raising=False)
    monkeypatch.delenv("WECOM_B0_ACTIVE_WORKSPACE", raising=False)
    monkeypatch.delenv("WECOM_REPLY_OUTBOX", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_JSON_READ_FALLBACK", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_PG_DUAL_WRITE", raising=False)
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    reset_sync_cursor_memory_for_tests()
    reset_wecom_reply_outbox_memory_for_tests()
    yield
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    reset_sync_cursor_memory_for_tests()
    reset_wecom_reply_outbox_memory_for_tests()


def _cfg(monkeypatch) -> WeComKfConfig:
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    load_wecom_kf_config.cache_clear()
    loaded = load_wecom_kf_config()
    assert loaded is not None
    return loaded


def _text_msg(msg_id: str, text: str, *, external_userid: str = "wmexternal001") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": external_userid,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": text},
    }


def _setup_json_store() -> None:
    from tests.test_wecom_active_case import _setup_json_store as setup

    setup()


def _b0_cfg(monkeypatch):
    cfg = _cfg(monkeypatch)
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    load_wecom_kf_config.cache_clear()
    return cfg


def test_claim_message_processed_is_idempotent() -> None:
    assert claim_message_processed("m1", open_kf_id="wk1", external_userid="wm1") is True
    assert claim_message_processed("m1", open_kf_id="wk1", external_userid="wm1") is False


def test_sync_msg_replay_only_new_msg_id_gets_reply(monkeypatch) -> None:
    """Ten historical msg_ids plus one new — only the new message sends."""
    cfg = _cfg(monkeypatch)
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    menu_calls: list[dict] = []

    def fake_send_menu(cfg, *, external_userid, open_kf_id, menu):
        menu_calls.append({"external_userid": external_userid})
        return {"errcode": 0}

    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_menu_reply", fake_send_menu)

    historical = [_text_msg(f"hist_{i}", f"old message {i}") for i in range(10)]
    new_msg = _text_msg("new_001", "smoke test q0.10 only new")

    def pull_first(_cfg, *, token, open_kf_id):
        return historical + [new_msg]

    first = process_kf_msg_or_event(
        cfg, callback_token="t1", open_kf_id="wktest001", pull_messages=pull_first
    )
    assert len(first) == 11
    assert len(menu_calls) == 11

    def pull_replay(_cfg, *, token, open_kf_id):
        return historical + [new_msg]

    second = process_kf_msg_or_event(
        cfg, callback_token="t2", open_kf_id="wktest001", pull_messages=pull_replay
    )
    assert len(second) == 11
    assert all(r.get("processing_skipped") for r in second[:10])
    assert second[10].get("processing_skipped") is True
    assert len(menu_calls) == 11


def test_repeated_drain_does_not_enqueue_additional_outbox(monkeypatch) -> None:
    """Second process run with same msg_ids must not enqueue new outbox rows."""
    cfg = _cfg(monkeypatch)
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    monkeypatch.setenv("WECOM_REPLY_OUTBOX", "1")
    enqueued: list[str] = []

    def fake_enqueue(**kwargs):
        enqueued.append(str(kwargs.get("msg_id")))
        return True

    monkeypatch.setattr("services.fiqa_api.wecom.slice.enqueue_wecom_reply", fake_enqueue)

    msg = _text_msg("drain_once", "hello there")

    def pull(_cfg, *, token, open_kf_id):
        return [msg]

    process_kf_msg_or_event(cfg, callback_token="t1", open_kf_id="wktest001", pull_messages=pull)
    process_kf_msg_or_event(cfg, callback_token="t2", open_kf_id="wktest001", pull_messages=pull)

    assert enqueued == ["drain_once"]


def test_generic_guide_menu_does_not_create_draft_case(monkeypatch) -> None:
    _setup_json_store()
    cfg = _b0_cfg(monkeypatch)
    menu_calls: list[dict] = []

    def fake_send_menu(cfg, *, external_userid, open_kf_id, menu):
        menu_calls.append({})
        return {"errcode": 0}

    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_menu_reply", fake_send_menu)

    def pull(_cfg, *, token, open_kf_id):
        return [_text_msg("generic_smoke", "smoke test q0.9.7 final cloud sql private ip")]

    results = process_kf_msg_or_event(
        cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
    )

    assert len(results) == 1
    assert results[0]["guided_menu_required"] is True
    assert results[0]["case_created"] is False
    assert results[0]["case_id"] is None
    assert count_stored_cases() == 0
    assert len(menu_calls) == 1


def test_generic_guide_menu_does_not_merge_into_open_draft(monkeypatch) -> None:
    """Open Draft exists but generic smoke text must not append to it (Q0.11)."""
    from services.fiqa_api.inbox_triage.case_store import get_case_by_id
    from tests.test_wecom_active_case import _click_msg

    _setup_json_store()
    cfg = _b0_cfg(monkeypatch)
    ext = "wm_q011_open_draft"
    smoke_text = "smoke test q0.11 sync cursor final"
    menu_calls: list[dict] = []

    def fake_send_menu(cfg, *, external_userid, open_kf_id, menu):
        menu_calls.append({})
        return {"errcode": 0}

    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_menu_reply", fake_send_menu)

    def pull_start(_cfg, *, token, open_kf_id):
        msg = _click_msg("m_start_open", menu_id="start_add_car", content="Start / 开始")
        msg["external_userid"] = ext
        return [msg]

    started = process_kf_msg_or_event(
        cfg, callback_token="t1", open_kf_id="wktest001", pull_messages=pull_start
    )
    case_id = started[0]["case_id"]
    assert case_id
    before = get_case_by_id(case_id)
    assert before is not None
    messages_before = len(before.get("case_messages") or [])
    source_before = str(before.get("source_text") or "")

    def pull_smoke(_cfg, *, token, open_kf_id):
        return [_text_msg("smoke_open_draft", smoke_text, external_userid=ext)]

    results = process_kf_msg_or_event(
        cfg, callback_token="t2", open_kf_id="wktest001", pull_messages=pull_smoke
    )

    assert len(results) == 1
    assert results[0]["guided_menu_required"] is True
    assert results[0]["active_case_outcome"] == "intent_not_actionable"
    assert results[0]["case_id"] is None
    assert len(menu_calls) == 1

    after = get_case_by_id(case_id)
    assert after is not None
    assert len(after.get("case_messages") or []) == messages_before
    assert smoke_text not in str(after.get("source_text") or "")
    assert str(after.get("source_text") or "") == source_before


def test_add_vehicle_start_flow_still_creates_draft_on_start_click(monkeypatch) -> None:
    _setup_json_store()
    cfg = _b0_cfg(monkeypatch)
    ext = "wm_q010_start_flow"

    def pull_add_car(_cfg, *, token, open_kf_id):
        return [_text_msg("m_add_car", "我想加车", external_userid=ext)]

    def pull_start_click(_cfg, *, token, open_kf_id):
        from tests.test_wecom_active_case import _click_msg

        msg = _click_msg("m_start", menu_id="start_add_car", content="Start / 开始")
        msg["external_userid"] = ext
        return [msg]

    process_kf_msg_or_event(
        cfg, callback_token="t1", open_kf_id="wktest001", pull_messages=pull_add_car
    )
    assert count_stored_cases() == 0

    results = process_kf_msg_or_event(
        cfg, callback_token="t2", open_kf_id="wktest001", pull_messages=pull_start_click
    )

    assert len(results) == 1
    assert results[0]["case_created"] is True
    assert results[0]["case_id"]
    assert count_stored_cases() == 1


def test_pull_customer_text_messages_uses_start_cursor(monkeypatch) -> None:
    cfg = _cfg(monkeypatch)
    calls: list[str] = []

    def fake_sync(_cfg, *, token, open_kf_id, cursor="", limit=50):
        calls.append(cursor)
        return {
            "errcode": 0,
            "msg_list": [
                _text_msg("curs_1", "new only"),
            ],
            "has_more": 0,
            "next_cursor": "cursor_after_batch",
        }

    monkeypatch.setattr("services.fiqa_api.wecom.sync_msg.sync_kf_messages", fake_sync)

    from services.fiqa_api.wecom.sync_msg import pull_customer_text_messages

    result = pull_customer_text_messages(
        cfg, token="tok", open_kf_id="wktest001", start_cursor="stored_cursor"
    )

    assert calls == ["stored_cursor"]
    assert len(result.messages) == 1
    assert result.next_cursor == "cursor_after_batch"


def test_slice_persists_sync_cursor_after_successful_batch(monkeypatch) -> None:
    cfg = _cfg(monkeypatch)
    saved: list[tuple[str, str]] = []

    def fake_pull(_cfg, *, token, open_kf_id, start_cursor=""):
        return SyncPullResult(
            messages=[_text_msg("c1", "hi")],
            next_cursor="next_abc",
        )

    def fake_save(open_kf_id, cursor):
        saved.append((open_kf_id, cursor))

    monkeypatch.setattr("services.fiqa_api.wecom.slice.pull_customer_text_messages", fake_pull)
    monkeypatch.setattr("services.fiqa_api.wecom.slice.save_sync_cursor", fake_save)
    monkeypatch.setattr("services.fiqa_api.wecom.slice.load_sync_cursor", lambda _kf: "")

    process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001")

    assert saved == [("wktest001", "next_abc")]
