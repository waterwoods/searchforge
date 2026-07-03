"""Tests for WeCom readiness report orchestration (no network)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import wecom_readiness as readiness
from scripts.validate_wecom_gettoken import (
    CallbackProbeResult,
    CredentialReadiness,
    EnvPresence,
    GettokenResult,
)
from scripts.validate_wecom_sync_msg import SyncMsgCheckResult
from services.fiqa_api.wecom.diagnostics import map_sync_msg_errcode


def _credentials(**overrides) -> CredentialReadiness:
    base = CredentialReadiness(
        cloudrun_env="PASS",
        env_file=Path(".env.cloudrun"),
        callback_keys=(
            EnvPresence("WECOM_CORP_ID", "PASS", "SET"),
            EnvPresence("WECOM_KF_TOKEN", "PASS", "SET"),
            EnvPresence("WECOM_KF_ENCODING_AES_KEY", "PASS", "SET"),
        ),
        secret_keys=(
            EnvPresence("WECOM_KF_SECRET", "WARNING", "NOT FOUND"),
            EnvPresence("WECOM_CORP_SECRET", "WARNING", "NOT FOUND"),
            EnvPresence("WECOM_SECRET", "WARNING", "NOT FOUND"),
            EnvPresence("WECOM_AGENT_SECRET", "PASS", "SET"),
        ),
        resolved_secret_key="WECOM_AGENT_SECRET",
        secret_fingerprint="agen…5678 (len=32)",
        secret_class_status="WARNING",
        secret_warning="agent fallback",
        corp_id_fingerprint="wwte…0001 (len=12)",
    )
    return base if not overrides else CredentialReadiness(**{**base.__dict__, **overrides})


def test_compute_score_warning_partial_credit():
    items = [
        ("a", "PASS", 1),
        ("b", "WARNING", 1),
        ("c", "FAIL", 1),
    ]
    assert readiness._compute_score(items) == 50


def test_build_report_stops_when_callback_unreachable(monkeypatch):
    creds = _credentials()
    probe = CallbackProbeResult(
        base_url="https://example.run.app",
        route_status="FAIL",
        verify_status="SKIP",
        decrypt_status="SKIP",
        route_detail="connection refused",
    )
    monkeypatch.setattr(readiness, "check_credentials", lambda **_: creds)
    monkeypatch.setattr(readiness, "probe_wecom_callback", lambda _: probe)

    report = readiness.build_report(base_url="https://example.run.app", env_file=Path(".env.cloudrun"))

    assert report.stopped_early == "callback route unreachable"
    assert report.gettoken is None
    assert report.sync_msg is None


def test_build_report_sync_msg_fail_48002(monkeypatch):
    creds = _credentials()
    probe = CallbackProbeResult(
        base_url="https://example.run.app",
        route_status="PASS",
        verify_status="PASS",
        decrypt_status="PASS",
    )
    gt = GettokenResult(
        status="PASS",
        errcode=0,
        errmsg="ok",
        secret_key="WECOM_AGENT_SECRET",
        secret_fingerprint="fp",
        secret_warning="warn",
        access_token="token",
    )
    sm = SyncMsgCheckResult(
        status="FAIL",
        errcode=48002,
        errmsg="api forbidden",
        message_count=0,
        has_next=False,
        next_cursor=None,
        secret_key="WECOM_AGENT_SECRET",
        secret_fingerprint="fp",
        secret_warning="warn",
        open_kf_id="wktest",
        diagnosis=map_sync_msg_errcode(48002),
        gettoken_errcode=0,
    )

    monkeypatch.setattr(readiness, "check_credentials", lambda **_: creds)
    monkeypatch.setattr(readiness, "probe_wecom_callback", lambda _: probe)
    monkeypatch.setattr(readiness, "fetch_gettoken", lambda **_: gt)
    monkeypatch.setattr(readiness, "run_sync_msg_check", lambda **_: sm)
    monkeypatch.setattr(readiness, "resolve_secret", lambda: ("WECOM_AGENT_SECRET", "secret"))
    monkeypatch.setenv("WECOM_CORP_ID", "wwtestcorp0001")

    report = readiness.build_report(base_url="https://example.run.app", env_file=Path(".env.cloudrun"))

    assert report.track_a.sync_msg == "FAIL"
    assert report.track_a_ready is False
    assert report.score_pct < 100


def test_print_report_includes_blocker_48002(capsys, monkeypatch):
    creds = _credentials()
    probe = CallbackProbeResult(
        base_url="https://example.run.app",
        route_status="PASS",
        verify_status="PASS",
        decrypt_status="PASS",
    )
    gt = GettokenResult(
        status="PASS",
        errcode=0,
        errmsg="ok",
        secret_key="WECOM_AGENT_SECRET",
        secret_fingerprint="fp",
        secret_warning=None,
        access_token="token",
    )
    sm = SyncMsgCheckResult(
        status="FAIL",
        errcode=48002,
        errmsg="api forbidden",
        message_count=0,
        has_next=False,
        next_cursor=None,
        secret_key="WECOM_AGENT_SECRET",
        secret_fingerprint="fp",
        secret_warning=None,
        open_kf_id="wktest",
        diagnosis=map_sync_msg_errcode(48002),
        gettoken_errcode=0,
    )
    report = readiness.ReadinessReport(
        credentials=creds,
        callback=probe,
        gettoken=gt,
        sync_msg=sm,
        track_a=readiness.TrackAEngineering(
            callback="PASS",
            normalize="PASS",
            bridge="PASS",
            active_case="PASS",
            sync_msg="FAIL",
        ),
        score_pct=82,
        track_a_ready=False,
        track_a_green=False,
        stopped_early=None,
    )

    readiness.print_report(report, base_url="https://example.run.app")
    out = capsys.readouterr().out

    assert "WeCom Readiness Report" in out
    assert "48002" in out
    assert "Today's Biggest Blocker" in out
    assert "可调用接口的应用" in out
    assert "Track A:" in out
    assert "NOT READY" in out


def test_track_a_green_when_messages_pulled():
    from services.fiqa_api.wecom.diagnostics import track_a_green_ready, track_a_ready

    assert track_a_ready(0) is True
    assert track_a_green_ready(0, message_count=2) is True
    assert track_a_green_ready(0, message_count=0) is False


@pytest.mark.parametrize(
    "errcode,needle",
    [
        (48002, "Wrong Secret class"),
        (48007, "KF account not bound"),
        (40001, "Secret / CorpID mismatch"),
    ],
)
def test_errcode_causes_present(errcode, needle):
    from services.fiqa_api.wecom.diagnostics import sync_msg_errcode_causes

    causes = sync_msg_errcode_causes(errcode)
    labels = " ".join(c.label for c in causes)
    assert needle in labels
