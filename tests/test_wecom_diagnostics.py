"""Unit tests for WeCom admin diagnostics (no network)."""

from __future__ import annotations

import pytest

from services.fiqa_api.wecom.diagnostics import (
    GETTOKEN_AGENT_FALLBACK_WARNING,
    SYNC_MSG_AGENT_FALLBACK_WARNING,
    gettoken_agent_fallback_warning,
    map_sync_msg_errcode,
    parse_sync_msg_response,
    resolve_secret,
    secret_fingerprint,
    sync_msg_agent_fallback_warning,
)


def test_secret_fingerprint_does_not_expose_full_secret():
    secret = "abcdefghijklmnopqrstuvwxyz0123456789"
    fp = secret_fingerprint(secret)
    assert secret not in fp
    assert fp.startswith("abcd")
    assert "6789" in fp
    assert "len=36" in fp


def test_secret_fingerprint_unset():
    assert secret_fingerprint("") == "(unset)"


def test_resolve_secret_prefers_kf_secret():
    env = {
        "WECOM_KF_SECRET": "kf-secret-value",
        "WECOM_AGENT_SECRET": "agent-secret-value",
    }
    key, val = resolve_secret(env)
    assert key == "WECOM_KF_SECRET"
    assert val == "kf-secret-value"


def test_gettoken_validator_warns_on_agent_fallback():
    env = {"WECOM_AGENT_SECRET": "agent-only"}
    key, _ = resolve_secret(env)
    warning = gettoken_agent_fallback_warning(key, env)
    assert warning == GETTOKEN_AGENT_FALLBACK_WARNING
    assert "sync_msg" in warning


def test_gettoken_no_warning_when_kf_secret_set():
    env = {
        "WECOM_KF_SECRET": "kf",
        "WECOM_AGENT_SECRET": "agent",
    }
    key, _ = resolve_secret(env)
    assert gettoken_agent_fallback_warning(key, env) is None


def test_sync_msg_warns_on_agent_fallback():
    env = {"WECOM_AGENT_SECRET": "agent-only"}
    key, _ = resolve_secret(
        env,
        keys=("WECOM_KF_SECRET", "WECOM_AGENT_SECRET"),
    )
    warning = sync_msg_agent_fallback_warning(key, env)
    assert warning == SYNC_MSG_AGENT_FALLBACK_WARNING


@pytest.mark.parametrize(
    "errcode,needle",
    [
        (0, "SUCCESS"),
        (48002, "可调用接口的应用"),
        (48007, "通过API管理微信客服账号"),
        (95011, "联合版"),
        (95012, "独立版"),
        (60020, "企业可信IP"),
        (40001, "Invalid secret"),
    ],
)
def test_sync_msg_errcode_mapping(errcode, needle):
    diag = map_sync_msg_errcode(errcode)
    assert diag.errcode == errcode
    assert needle in diag.summary
    assert diag.next_action.strip()


def test_sync_msg_errcode_meaning_and_blocker():
    from services.fiqa_api.wecom.diagnostics import (
        sync_msg_blocker_summary,
        sync_msg_errcode_causes,
        sync_msg_errcode_meaning,
    )

    assert "permission" in sync_msg_errcode_meaning(48002).lower()
    assert sync_msg_blocker_summary(48002).category == "Admin Configuration"
    assert sum(c.probability_pct for c in sync_msg_errcode_causes(48002)) == 100


def test_parse_sync_msg_response_fields():
    data = {
        "errcode": 0,
        "errmsg": "ok",
        "msg_list": [{"msgid": "1"}, {"msgid": "2"}],
        "has_more": 1,
        "next_cursor": "CURSOR_ABC",
    }
    parsed = parse_sync_msg_response(data)
    assert parsed["message_count"] == 2
    assert parsed["has_next"] is True
    assert parsed["next_cursor"] == "CURSOR_ABC"


def test_validate_wecom_gettoken_script_warns_on_agent_fallback(capsys, monkeypatch):
    import importlib.util
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / "scripts" / "validate_wecom_gettoken.py"
    spec = importlib.util.spec_from_file_location("validate_wecom_gettoken", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    monkeypatch.setenv("WECOM_CORP_ID", "wwtestcorp0001")
    monkeypatch.delenv("WECOM_KF_SECRET", raising=False)
    monkeypatch.setenv("WECOM_AGENT_SECRET", "agentsecretvalue12345678")
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setattr(sys, "argv", ["validate_wecom_gettoken.py", "--env-file", "/dev/null"])

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"errcode": 0, "errmsg": "ok", "access_token": "tok", "expires_in": 7200}

    import httpx

    monkeypatch.setattr(httpx, "get", lambda *a, **k: _Resp())
    rc = mod.main()

    captured = capsys.readouterr()
    assert rc == 0
    assert GETTOKEN_AGENT_FALLBACK_WARNING in captured.out
    assert "agentsecretvalue12345678" not in captured.out
    assert "len=" in captured.out
