"""QA Fast Lane V1 — invite order + Production hard-block (no network)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "qa_fast_lane", ROOT / "scripts" / "qa_fast_lane.py"
)
assert SPEC and SPEC.loader
qfl = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qfl)


def test_evaluate_invite_pass_requires_active_zero_uses_and_expiry():
    issued = {
        "scenario_id": "chen_camry",
        "expires_at": 2_000_000_000,
        "use_count": 0,
        "token": "di_x",
    }
    ok, reason = qfl.evaluate_invite_pass(
        issued,
        {
            "ok": True,
            "status": "active",
            "invite": {
                "scenario_id": "chen_camry",
                "use_count": 0,
                "expires_at": 2_000_000_000,
            },
        },
        "chen_camry",
        now=1_700_000_000,
    )
    assert ok and reason == "ok"

    bad, why = qfl.evaluate_invite_pass(
        issued,
        {"ok": False, "status": "revoked"},
        "chen_camry",
        now=1_700_000_000,
    )
    assert not bad and why == "validation_not_ok"


def test_prepare_invite_sequence_order_fresh_before_issue():
    calls: list[str] = []

    def fake_http(method, path, body=None):
        if "presets/fresh" in path:
            calls.append("fresh")
            return 200, {"ok": True}
        if "reset-office" in path:
            calls.append("reset")
            return 200, {"ok": True, "invites_revoked": 0}
        if path.endswith("/issue"):
            calls.append("issue")
            return 200, {
                "invite_id": "dinv_1",
                "token": "di_abcdefghijklmnopqrstuvwxyz012345",
                "scenario_id": "chen_camry",
                "expires_at": 2_000_000_000,
                "use_count": 0,
            }
        if path.endswith("/validate"):
            calls.append("validate")
            return 200, {
                "ok": True,
                "status": "active",
                "invite": {
                    "scenario_id": "chen_camry",
                    "use_count": 0,
                    "expires_at": 2_000_000_000,
                },
            }
        return 500, {"error": path}

    res = qfl.prepare_invite_sequence(
        api=qfl.CLOUD_QA_API,
        scenario_id="chen_camry",
        session_id="wx_08af8e4deadbeef01",
        headers={"X-Unified-Intake-Support-Key": "test"},
        call=fake_http,
    )
    assert res["ok"] is True
    assert res["verdict"] == "PASS"
    assert calls == ["fresh", "reset", "issue", "validate"]
    assert res["steps"] == ["p35_fresh", "office_reset", "issue", "validate"]


def test_invite_never_issued_if_fresh_fails():
    calls: list[str] = []

    def fake_http(method, path, body=None):
        if "presets/fresh" in path:
            calls.append("fresh")
            return 400, {"detail": "confirm_fresh_required"}
        if path.endswith("/issue"):
            calls.append("issue")
            return 200, {"token": "di_should_not"}
        return 200, {"ok": True}

    res = qfl.prepare_invite_sequence(
        api=qfl.CLOUD_QA_API,
        scenario_id="chen_camry",
        session_id="wx_08af8e4deadbeef01",
        headers={},
        call=fake_http,
    )
    assert res["ok"] is False
    assert "issue" not in calls


def test_assert_cloud_qa_blocks_production():
    with pytest.raises(SystemExit):
        qfl._assert_cloud_qa(qfl.PRODUCTION_API)
    with pytest.raises(SystemExit):
        qfl._assert_cloud_qa("https://evil.example.com")
    qfl._assert_cloud_qa(qfl.CLOUD_QA_API)


def test_phone_prompt_constant():
    assert qfl.PHONE_PROMPT == "请在手机完成客户提交，然后输入 PHONE COMPLETE"
    assert qfl.PHONE_COMPLETE == "PHONE COMPLETE"


def test_shell_wrapper_exists():
    wrapper = (ROOT / "scripts" / "run_qa_fast_lane.sh").read_text(encoding="utf-8")
    assert "qa_fast_lane.py" in wrapper
    assert "Never targets Production" in wrapper or "Never" in wrapper
