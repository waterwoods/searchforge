"""Bounded tests for optional WeChat binding (state signing, session patch, config)."""

from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage.config_loader import get_wechat_binding_mode_for_client
from services.fiqa_api.inbox_triage.session_store import (
    get_session_light_identity_binding,
    patch_session_light_identity_binding,
)
from services.fiqa_api.inbox_triage.wechat_binding import (
    build_redirect_uri,
    opaque_person_link_key,
    sign_state,
    verify_state,
)


def test_sign_verify_state_roundtrip():
    t = sign_state("sess_integration_test_01", "socal_precision")
    parsed = verify_state(t)
    assert parsed is not None
    assert parsed["session_id"] == "sess_integration_test_01"
    assert parsed["client_id"] == "socal_precision"


def test_opaque_person_link_key_stable():
    a = opaque_person_link_key("test-openid-xyz")
    b = opaque_person_link_key("test-openid-xyz")
    assert a == b
    assert a.startswith("wx_")
    assert opaque_person_link_key("other") != a


def test_get_wechat_binding_mode_socal_live():
    assert get_wechat_binding_mode_for_client("socal_precision") == "live"


def test_get_wechat_binding_mode_default_stub():
    assert get_wechat_binding_mode_for_client("chen_kui") == "stub"
    assert get_wechat_binding_mode_for_client(None) == "stub"


def test_build_redirect_uri_explicit_wins(monkeypatch):
    monkeypatch.setenv("WECHAT_BINDING_REDIRECT_URI", "https://api.example.com/api/inbox/wechat/binding/callback")
    monkeypatch.delenv("PUBLIC_API_BASE_URL", raising=False)
    monkeypatch.delenv("API_PUBLIC_URL", raising=False)
    assert build_redirect_uri() == "https://api.example.com/api/inbox/wechat/binding/callback"


def test_build_redirect_uri_from_public_api_base(monkeypatch):
    monkeypatch.delenv("WECHAT_BINDING_REDIRECT_URI", raising=False)
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://run.app")
    assert build_redirect_uri() == "https://run.app/api/inbox/wechat/binding/callback"


def test_patch_session_light_identity_requires_session(tmp_path, monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_SESSIONS_PATH", str(tmp_path / "sess.json"))
    sid = "sess_wechat_patch_test"
    with pytest.raises(ValueError, match="session_not_found"):
        patch_session_light_identity_binding(
            sid,
            {
                "identity_binding_state": "linked",
                "person_link_key": "sim_test_key",
                "person_link_source": "wechat",
                "person_link_confidence": 0.75,
            },
        )


def test_patch_and_read_session_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_SESSIONS_PATH", str(tmp_path / "sess.json"))
    from services.fiqa_api.inbox_triage import session_store as ss

    sid = "sess_wechat_patch_ok_12"
    ss.save_in_progress_session(
        sid,
        [{"role": "customer", "text": "hello"}],
        {"lifecycle_status": "handoff_pending", "handoff_ready": True},
    )
    patch_session_light_identity_binding(
        sid,
        {
            "identity_binding_state": "linked",
            "person_link_key": "sim_abc",
            "person_link_source": "wechat",
            "person_link_confidence": 0.75,
        },
    )
    li = get_session_light_identity_binding(sid)
    assert li is not None
    assert li.get("identity_binding_state") == "linked"
    assert li.get("person_link_key") == "sim_abc"
    assert li.get("person_link_source") == "wechat"
