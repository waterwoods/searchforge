"""Unit tests for WeCom vertical slice orchestrator."""

from __future__ import annotations

import json

import pytest

from services.fiqa_api.wecom.config import WeComKfConfig, load_wecom_kf_config
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event
from services.fiqa_api.wecom.sync_cursor import reset_sync_cursor_memory_for_tests


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


@pytest.fixture(autouse=True)
def _reset_reply_dedup(monkeypatch):
    """Deterministic in-process dedup guard for every test in this module.

    Strips any host DATABASE_URL so the claim guard exercises the
    in-process path (not a real Postgres connection) and resets state
    between tests so msg_id reuse across test functions cannot leak.

    Also clears flags that `services.fiqa_api.app_main` (imported by other
    test modules collected in the same pytest session) loads from a local
    `.env.cloudrun` via `load_dotenv(override=False)` — if that file exists
    on disk (e.g. a developer sandbox with real deploy config), those real
    values would otherwise leak into these tests and silently flip
    send-enabled / production-mode behavior depending on collection order.
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


@pytest.fixture
def cfg(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    load_wecom_kf_config.cache_clear()
    loaded = load_wecom_kf_config()
    assert loaded is not None
    return loaded


def _fake_pull(_cfg, *, token, open_kf_id):
    assert token == "callback_token_abc"
    assert open_kf_id == "wktest001"
    return [
        {
            "msgid": "msg001",
            "open_kfid": "wktest001",
            "external_userid": "wmexternal001",
            "origin": 3,
            "msgtype": "text",
            "text": {"content": "I was in an accident"},
        }
    ]


def test_slice_pipeline_logs_intent_and_reply(cfg, caplog):
    with caplog.at_level("INFO"):
        results = process_kf_msg_or_event(
            cfg,
            callback_token="callback_token_abc",
            open_kf_id="wktest001",
            pull_messages=_fake_pull,
        )

    assert len(results) == 1
    assert results[0]["detected_intent"] == "claim"
    assert results[0]["internal_intent"] == "claim_intake"
    assert results[0]["guided_menu_required"] is False
    assert results[0]["reply_sent"] is False
    assert results[0]["case_created"] is True
    assert results[0]["service_lane"] == "claim_lite"
    assert "broker" in results[0]["reply_text"].lower() or "陈总" in results[0]["reply_text"]

    stages = [r.message for r in caplog.records if r.message.startswith("wecom_slice_")]
    assert any("wecom_slice_sync_msg_ok_v1" in s for s in stages)
    assert any("wecom_event_normalized_v1" in r.message for r in caplog.records)
    assert any("wecom_slice_minimal_lane_v1" in s for s in stages)
    assert any("wecom_slice_reply_generated_v1" in s for s in stages)
    assert any("wecom_slice_reply_logged_only_v1" in s for s in stages)


def test_kf_secret_fallback_order(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    for key in (
        "WECOM_KF_SECRET",
        "WECOM_CORP_SECRET",
        "WECOM_SECRET",
        "WECOM_AGENT_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)
    load_wecom_kf_config.cache_clear()
    assert load_wecom_kf_config().kf_secret == ""

    monkeypatch.setenv("WECOM_AGENT_SECRET", "agent-only")
    load_wecom_kf_config.cache_clear()
    assert load_wecom_kf_config().kf_secret == "agent-only"

    monkeypatch.setenv("WECOM_SECRET", "generic")
    load_wecom_kf_config.cache_clear()
    assert load_wecom_kf_config().kf_secret == "generic"

    monkeypatch.setenv("WECOM_CORP_SECRET", "corp")
    load_wecom_kf_config.cache_clear()
    assert load_wecom_kf_config().kf_secret == "corp"

    monkeypatch.setenv("WECOM_KF_SECRET", "kf")
    load_wecom_kf_config.cache_clear()
    assert load_wecom_kf_config().kf_secret == "kf"


def test_slice_uses_agent_secret_fallback(monkeypatch, caplog):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_AGENT_SECRET", "agent-secret")
    for key in ("WECOM_KF_SECRET", "WECOM_CORP_SECRET", "WECOM_SECRET"):
        monkeypatch.delenv(key, raising=False)
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()
    assert cfg.kf_secret == "agent-secret"

    with caplog.at_level("INFO"):
        results = process_kf_msg_or_event(
            cfg,
            callback_token="callback_token_abc",
            open_kf_id="wktest001",
            pull_messages=_fake_pull,
        )

    assert len(results) == 1
    assert any("wecom_slice_sync_msg_ok_v1" in r.message for r in caplog.records)
    assert not any("wecom_slice_skipped_v1" in r.message for r in caplog.records)


def test_slice_skips_without_secret(monkeypatch, caplog):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    for key in (
        "WECOM_KF_SECRET",
        "WECOM_CORP_SECRET",
        "WECOM_SECRET",
        "WECOM_AGENT_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()
    assert cfg is not None

    with caplog.at_level("INFO"):
        results = process_kf_msg_or_event(
            cfg,
            callback_token="tok",
            open_kf_id="wk1",
        )

    assert results == []
    assert any("wecom_slice_skipped_v1" in r.message for r in caplog.records)


def test_unclear_message_triggers_guided_menu(cfg, caplog):
    def pull(_cfg, *, token, open_kf_id):
        return [
            {
                "msgid": "m2",
                "open_kfid": "wktest001",
                "external_userid": "wmexternal001",
                "origin": 3,
                "msgtype": "text",
                "text": {"content": "hi"},
            }
        ]

    results = process_kf_msg_or_event(
        cfg,
        callback_token="t",
        open_kf_id="wktest001",
        pull_messages=pull,
    )
    assert results[0]["guided_menu_required"] is True
    assert "【加车资料补充】" in results[0]["reply_text"]
    assert "加车" in results[0]["reply_text"]
    assert "1." not in results[0]["reply_text"]
    assert "Reply with the number" not in results[0]["reply_text"]


# ---------------------------------------------------------------------------
# P0 — Reply idempotency: one WeCom msg_id must never trigger more than one
# outbound send, however many times process_kf_msg_or_event runs for it.
# ---------------------------------------------------------------------------


def _send_enabled_cfg(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()
    assert cfg is not None
    return cfg


def _patch_sends(monkeypatch):
    """Patch both send APIs used by slice._dispatch_reply; return call-count trackers."""
    text_calls: list[dict] = []
    menu_calls: list[dict] = []

    def fake_text(cfg, *, external_userid, open_kf_id, content):
        text_calls.append({"external_userid": external_userid, "content": content})
        return {"errcode": 0}

    def fake_menu(cfg, *, external_userid, open_kf_id, menu):
        menu_calls.append({"external_userid": external_userid, "menu": menu})
        return {"errcode": 0}

    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_text_reply", fake_text)
    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_menu_reply", fake_menu)
    return text_calls, menu_calls


def _one_message_pull(msg_id: str, content: str = "hello there unrelated chit chat"):
    def pull(_cfg, *, token, open_kf_id):
        return [
            {
                "msgid": msg_id,
                "open_kfid": "wktest001",
                "external_userid": "wmexternal001",
                "origin": 3,
                "msgtype": "text",
                "text": {"content": content},
            }
        ]

    return pull


def test_same_msg_id_processed_three_times_sends_once(monkeypatch, caplog) -> None:
    """Simulates the same message being fed through the pipeline 3x in a row
    (e.g. a burst of callback retries all landing before the first send
    completes) — only one outbound send must occur."""
    cfg = _send_enabled_cfg(monkeypatch)
    text_calls, menu_calls = _patch_sends(monkeypatch)
    pull = _one_message_pull("m_dup_001", "hi")  # low confidence -> guided menu

    with caplog.at_level("INFO"):
        for _ in range(3):
            process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)

    assert len(text_calls) + len(menu_calls) == 1
    skipped = [r for r in caplog.records if "wecom_slice_message_skipped_already_processed_v1" in r.message]
    assert len(skipped) == 2


def test_callback_retry_with_same_msg_id_sends_once(monkeypatch) -> None:
    """WeCom callback retry: two independent process_kf_msg_or_event calls,
    each simulating a full callback delivery for the exact same msg_id."""
    cfg = _send_enabled_cfg(monkeypatch)
    text_calls, menu_calls = _patch_sends(monkeypatch)
    pull = _one_message_pull("m_retry_001", "I was in an accident")

    first = process_kf_msg_or_event(cfg, callback_token="t1", open_kf_id="wktest001", pull_messages=pull)
    second = process_kf_msg_or_event(cfg, callback_token="t2", open_kf_id="wktest001", pull_messages=pull)

    assert len(text_calls) + len(menu_calls) == 1
    assert first[0]["reply_sent"] is True
    assert second[0]["reply_sent"] is False
    assert second[0].get("processing_skipped") is True
    assert second[0].get("skip_reason") == "already_processed"


def test_sync_msg_replay_with_same_msg_id_sends_once(monkeypatch) -> None:
    """sync_msg has no persisted cursor, so an already-processed message can
    be re-delivered on a later, otherwise-unrelated callback. Simulated here
    as pull_messages returning the same already-seen msg_id again."""
    cfg = _send_enabled_cfg(monkeypatch)
    text_calls, menu_calls = _patch_sends(monkeypatch)

    def pull_batch_1(_cfg, *, token, open_kf_id):
        return [
            {
                "msgid": "m_replay_001",
                "open_kfid": "wktest001",
                "external_userid": "wmexternal001",
                "origin": 3,
                "msgtype": "text",
                "text": {"content": "hi"},
            }
        ]

    def pull_batch_2_replays_old_plus_new(_cfg, *, token, open_kf_id):
        # sync_msg without a persisted cursor re-returns the old message
        # alongside a genuinely new one.
        return [
            {
                "msgid": "m_replay_001",
                "open_kfid": "wktest001",
                "external_userid": "wmexternal001",
                "origin": 3,
                "msgtype": "text",
                "text": {"content": "hi"},
            },
            {
                "msgid": "m_replay_002",
                "open_kfid": "wktest001",
                "external_userid": "wmexternal001",
                "origin": 3,
                "msgtype": "text",
                "text": {"content": "hi again"},
            },
        ]

    process_kf_msg_or_event(cfg, callback_token="t1", open_kf_id="wktest001", pull_messages=pull_batch_1)
    results2 = process_kf_msg_or_event(
        cfg, callback_token="t2", open_kf_id="wktest001", pull_messages=pull_batch_2_replays_old_plus_new
    )

    # Two distinct msg_ids across the two calls -> exactly two sends total,
    # the replayed m_replay_001 must not cause a second send.
    assert len(text_calls) + len(menu_calls) == 2
    assert results2[0]["msg_id"] == "m_replay_001"
    assert results2[0]["reply_sent"] is False
    assert results2[0].get("processing_skipped") is True
    assert results2[1]["msg_id"] == "m_replay_002"
    assert results2[1]["reply_sent"] is True


def test_greeting_path_sends_once(monkeypatch) -> None:
    """Unclear/greeting message (guided menu reply) sends exactly once, and
    repeat delivery of the same msg_id does not resend the guided menu."""
    cfg = _send_enabled_cfg(monkeypatch)
    text_calls, menu_calls = _patch_sends(monkeypatch)
    pull = _one_message_pull("m_greeting_001", "你好")

    first = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    second = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)

    assert first[0]["guided_menu_required"] is True
    assert first[0]["reply_sent"] is True
    assert second[0]["reply_sent"] is False
    assert len(menu_calls) == 1
    assert len(text_calls) == 0


def test_flag_off_reply_behavior_unchanged_across_repeats(monkeypatch, caplog) -> None:
    """WECOM_SLICE_SEND_REPLY off: no sends are ever attempted. Repeat delivery
    of the same msg_id is skipped at the message-processed guard (Q0.10)."""
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.delenv("WECOM_SLICE_SEND_REPLY", raising=False)
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()
    assert cfg is not None

    text_calls, menu_calls = _patch_sends(monkeypatch)
    pull = _one_message_pull("m_flag_off_001", "hi")

    all_results = []
    with caplog.at_level("INFO"):
        for _ in range(3):
            all_results.append(
                process_kf_msg_or_event(
                    cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
                )
            )

    assert len(text_calls) + len(menu_calls) == 0
    assert all_results[0][0]["reply_sent"] is False
    assert all_results[1][0].get("processing_skipped") is True
    assert all_results[2][0].get("processing_skipped") is True
    logged_only = [r for r in caplog.records if "wecom_slice_reply_logged_only_v1" in r.message]
    assert len(logged_only) == 1
    skipped = [r for r in caplog.records if "wecom_slice_message_skipped_already_processed_v1" in r.message]
    assert len(skipped) == 2
