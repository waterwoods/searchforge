"""Unit tests for WeCom vertical slice orchestrator."""

from __future__ import annotations

import json

import pytest

from services.fiqa_api.wecom.config import WeComKfConfig, load_wecom_kf_config
from services.fiqa_api.wecom.slice import process_kf_msg_or_event


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
    assert results[0]["case_created"] is False
    assert "broker" in results[0]["reply_text"].lower()

    stages = [r.message for r in caplog.records if r.message.startswith("wecom_slice_")]
    assert any("wecom_slice_sync_msg_ok_v1" in s for s in stages)
    assert any("wecom_event_normalized_v1" in r.message for r in caplog.records)
    assert any("wecom_slice_intent_v1" in s for s in stages)
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
    assert "Add Vehicle" in results[0]["reply_text"]
    assert "加车" in results[0]["reply_text"]
    assert "1." not in results[0]["reply_text"]
    assert "Reply with the number" not in results[0]["reply_text"]
