"""T2 / T2.1 — Demo Invite Foundation + isolation hardening.

Acceptance:
- Invite A → Customer A; Invite B → Customer B (no Active Case)
- Overlay works with CHEN_DEMO_INVITE_ENABLED only (no global mock flag)
- Normal session without invite → BLANK_DEGRADE
- Invalid/expired → BLANK_DEGRADE
- Production → hard OFF
- Active Case blocks silent scenario switch
"""

from __future__ import annotations

import os
import time

import pytest
from fastapi.testclient import TestClient

os.environ["CHEN_DEMO_INVITE_ENABLED"] = "1"
os.environ["P4_CUSTOMER_LOOKUP_MOCK"] = "0"
os.environ.pop("ENV", None)
os.environ.pop("SERVICE_NAME", None)

from services.fiqa_api.app_main import app  # noqa: E402
from services.fiqa_api.inbox_triage import demo_invite as di  # noqa: E402
from services.fiqa_api.inbox_triage.mp_customer_identity import (  # noqa: E402
    reset_mp_active_case_index_for_tests,
)
from services.fiqa_api.inbox_triage.smart_claim_start.service import (  # noqa: E402
    build_smart_claim_start_response,
)


@pytest.fixture(autouse=True)
def _demo_invite_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CHEN_DEMO_INVITE_ENABLED", "1")
    # Isolation default: global mock OFF — overlay must not need it.
    monkeypatch.setenv("P4_CUSTOMER_LOOKUP_MOCK", "0")
    monkeypatch.delenv("P4_CUSTOMER_LOOKUP_FORCE_UNAVAILABLE", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("SERVICE_NAME", raising=False)
    di.reset_demo_invite_store_for_tests()
    reset_mp_active_case_index_for_tests()
    yield
    di.reset_demo_invite_store_for_tests()
    reset_mp_active_case_index_for_tests()


def _chip_name(plan: dict) -> str | None:
    for chip in plan.get("known_chips") or []:
        if chip.get("field_key") == "customer_name":
            return str(chip.get("value") or "")
    return None


def test_catalog_has_three_allowlisted_fictional_customers():
    rows = di.list_catalog()
    assert len(rows) >= 3
    ids = {r["scenario_id"] for r in rows}
    assert "chen_camry" in ids
    assert "li_multi" in ids
    assert "wang_stale" in ids
    for row in rows:
        assert row["is_demo"] is True
        assert row["demo_name"] == di.DEMO_NAME


def test_unknown_scenario_rejected():
    with pytest.raises(ValueError, match="scenario_not_allowlisted"):
        di.issue_demo_invite(office_id="office_demo_a", scenario_id="not_a_real_customer")


def test_invite_a_and_invite_b_show_distinct_customers():
    a = di.issue_demo_invite(office_id="office_demo_a", scenario_id="chen_camry")
    b = di.issue_demo_invite(office_id="office_demo_a", scenario_id="li_multi")
    assert a["customer_display_name"] == "陈明"
    assert b["customer_display_name"] == "李娜"

    session = "wx_demo_invite_same_user_aaaa"
    ra = di.redeem_demo_invite(token=a["token"], session_id=session, office_id="office_demo_a")
    assert ra["ok"] is True
    plan_a = build_smart_claim_start_response(session_id=session)["plan"]
    assert plan_a["mode"] == "MATCHED_KNOWN"
    assert _chip_name(plan_a) == "陈明"

    rb = di.redeem_demo_invite(token=b["token"], session_id=session, office_id="office_demo_a")
    assert rb["ok"] is True
    plan_b = build_smart_claim_start_response(session_id=session)["plan"]
    assert plan_b["mode"] == "MATCHED_CONFIRM_VEHICLE"
    assert _chip_name(plan_b) == "李娜" or any(
        "李娜" in str(c) for c in (plan_b.get("known_chips") or [])
    )


def test_demo_flag_on_valid_overlay_without_global_mock():
    """T2.1 isolation #1: CHEN_DEMO_INVITE_ENABLED + overlay → chips; P4 mock OFF."""
    issued = di.issue_demo_invite(office_id="office_demo_a", scenario_id="chen_camry")
    session = "wx_demo_invite_iso_overlay_1111"
    assert di.redeem_demo_invite(
        token=issued["token"], session_id=session, office_id="office_demo_a"
    )["ok"]

    res = build_smart_claim_start_response(session_id=session)
    assert res["identity_source"] == "demo_invite_overlay"
    assert res["lookup_enabled"] is True
    assert res["plan"]["mode"] == "MATCHED_KNOWN"
    assert _chip_name(res["plan"]) == "陈明"
    assert res.get("demo_invite_overlay") is True


def test_demo_flag_on_no_overlay_blank_degrade():
    """T2.1 isolation #2: demo flag ON, no invite → blank; no global mock leak."""
    res = build_smart_claim_start_response(session_id="wx_demo_invite_iso_blank_2222")
    assert res["identity_source"] == "session_id"
    assert res["plan"]["mode"] == "BLANK_DEGRADE"
    assert res["plan"].get("known_chips") == []
    assert res.get("demo_invite_overlay") is not True

    # Client-supplied mock_scenario must NOT activate without P4 flag.
    res2 = build_smart_claim_start_response(
        session_id="wx_demo_invite_iso_blank_2222",
        mock_scenario="S3",
    )
    assert res2["plan"]["mode"] == "BLANK_DEGRADE"
    assert res2["identity_source"] != "mock_scenario"
    assert res2["identity_source"] != "demo_invite_overlay"


def test_invalid_and_expired_invite_blank_degrade():
    """T2.1 isolation #3."""
    session = "wx_demo_invite_iso_bad_3333"
    good = di.issue_demo_invite(office_id="office_demo_a", scenario_id="chen_camry")
    di.redeem_demo_invite(token=good["token"], session_id=session, office_id="office_demo_a")
    assert di.resolve_overlay_mock_scenario(session) == "S3"

    bad = di.redeem_demo_invite(
        token="di_not_a_real_token_xxxxxxxxxx",
        session_id=session,
        office_id="office_demo_a",
    )
    assert bad["ok"] is False
    assert bad["fallback"] == "blank_claim"
    assert di.resolve_overlay_mock_scenario(session) is None
    assert build_smart_claim_start_response(session_id=session)["plan"]["mode"] == "BLANK_DEGRADE"

    from services.fiqa_api.inbox_triage.demo_invite.store import get_demo_invite_store

    issued = di.issue_demo_invite(
        office_id="office_demo_a", scenario_id="chen_camry", ttl_seconds=60
    )
    invite = get_demo_invite_store().get_by_invite_id(issued["invite_id"])
    assert invite is not None
    invite.expires_at = time.time() - 10
    expired = di.redeem_demo_invite(
        token=issued["token"],
        session_id="wx_demo_invite_iso_exp_3334",
        office_id="office_demo_a",
    )
    assert expired["ok"] is False
    assert expired["status"] == "expired"
    assert expired["fallback"] == "blank_claim"
    assert (
        build_smart_claim_start_response(session_id="wx_demo_invite_iso_exp_3334")["plan"][
            "mode"
        ]
        == "BLANK_DEGRADE"
    )


def test_production_deployment_hard_off(monkeypatch: pytest.MonkeyPatch):
    """T2.1 isolation #4."""
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("SERVICE_NAME", "fiqa-api")
    assert di.demo_invite_enabled() is False
    with pytest.raises(ValueError, match="demo_invite_disabled_production"):
        di.issue_demo_invite(office_id="office_demo_a", scenario_id="chen_camry")


def test_same_wx_user_no_durable_person_link_remap():
    """Overlay swaps presentation; resolve never returns/mutates person_link."""
    issued = di.issue_demo_invite(office_id="office_demo_a", scenario_id="wang_stale")
    session = "wx_demo_invite_identity_bbbb"
    result = di.redeem_demo_invite(
        token=issued["token"], session_id=session, office_id="office_demo_a"
    )
    blob = str(result).lower()
    assert "openid" not in blob
    assert "person_link_key" not in blob

    res = build_smart_claim_start_response(session_id=session)
    assert res["identity_source"] == "demo_invite_overlay"
    assert "person_link_key" not in str(res)
    assert res.get("demo_invite_overlay") is True

    di.reset_session_overlay(session)
    assert di.resolve_overlay_mock_scenario(session) is None


def test_office_scope_mismatch_rejected():
    issued = di.issue_demo_invite(office_id="office_alpha", scenario_id="chen_camry")
    result = di.redeem_demo_invite(
        token=issued["token"],
        session_id="wx_demo_invite_office_ffff",
        office_id="office_beta",
    )
    assert result["ok"] is False
    assert result["error_code"] == "office_mismatch"


def test_revoke_and_office_reset():
    issued = di.issue_demo_invite(office_id="office_demo_a", scenario_id="chen_camry")
    session = "wx_demo_invite_revoke_gggg"
    assert di.redeem_demo_invite(
        token=issued["token"], session_id=session, office_id="office_demo_a"
    )["ok"]

    revoked = di.revoke_demo_invite(invite_id=issued["invite_id"])
    assert revoked["ok"] is True
    assert revoked.get("overlays_cleared", 0) >= 1
    assert di.resolve_overlay_mock_scenario(session) is None

    again = di.redeem_demo_invite(
        token=issued["token"],
        session_id="wx_demo_invite_revoke_hhhh",
        office_id="office_demo_a",
    )
    assert again["ok"] is False
    assert again["status"] == "revoked"

    issued2 = di.issue_demo_invite(office_id="office_demo_a", scenario_id="li_multi")
    session2 = "wx_demo_invite_revoke_iiii"
    di.redeem_demo_invite(
        token=issued2["token"], session_id=session2, office_id="office_demo_a"
    )
    reset = di.reset_office_demo_invites("office_demo_a")
    assert reset["overlays_cleared"] >= 1
    assert di.resolve_overlay_mock_scenario(session2) is None


def test_active_case_blocks_scenario_switch(monkeypatch: pytest.MonkeyPatch):
    """Active Case remains authoritative; switching scenarios requires support reset."""
    import services.fiqa_api.inbox_triage.demo_invite.service as di_svc

    session = "wx_demo_invite_active_jjjj"
    a = di.issue_demo_invite(office_id="office_demo_a", scenario_id="chen_camry")
    b = di.issue_demo_invite(office_id="office_demo_a", scenario_id="li_multi")

    assert di.redeem_demo_invite(
        token=a["token"], session_id=session, office_id="office_demo_a"
    )["ok"]
    assert _chip_name(build_smart_claim_start_response(session_id=session)["plan"]) == "陈明"

    fake_case = {
        "case_id": "case_demo_active_preserve",
        "record_id": "case_demo_active_preserve",
        "case_status": "new",
    }
    monkeypatch.setattr(di_svc, "_active_case_for_session", lambda _sid: fake_case)

    blocked = di.redeem_demo_invite(
        token=b["token"], session_id=session, office_id="office_demo_a"
    )
    assert blocked["ok"] is False
    assert blocked["error_code"] == "active_case_blocks_scenario_switch"
    assert blocked.get("requires_support_reset") is True
    assert blocked.get("fallback") == "continue_active_case"
    # Overlay for 陈明 preserved — no silent relabel to 李娜.
    assert di.resolve_overlay_mock_scenario(session) == "S3"
    assert _chip_name(build_smart_claim_start_response(session_id=session)["plan"]) == "陈明"

    # Idempotent same-scenario redeem still OK.
    again = di.redeem_demo_invite(
        token=a["token"], session_id=session, office_id="office_demo_a"
    )
    assert again["ok"] is True
    assert again.get("status") == "redeemed_idempotent"
    assert again.get("active_case_preserved") is True

    # After support clears Active Case + overlay, scenario switch is allowed.
    monkeypatch.setattr(di_svc, "_active_case_for_session", lambda _sid: None)
    di.reset_session_overlay(session)
    switched = di.redeem_demo_invite(
        token=b["token"], session_id=session, office_id="office_demo_a"
    )
    assert switched["ok"] is True
    assert di.resolve_overlay_mock_scenario(session) == "S2"


def test_http_issue_redeem_smart_claim_start_roundtrip():
    client = TestClient(app)
    issue = client.post(
        "/api/inbox/support/demo-invite/issue",
        json={"office_id": "office_demo_a", "scenario_id": "chen_camry"},
    )
    assert issue.status_code == 200, issue.text
    token = issue.json()["token"]
    assert token.startswith("di_")

    session = "wx_demo_invite_http_iiii"
    redeem = client.post(
        "/api/h5/demo-invite/redeem",
        json={"token": token, "session_id": session, "office_id": "office_demo_a"},
    )
    assert redeem.status_code == 200
    assert redeem.json()["ok"] is True
    assert "openid" not in redeem.text.lower()
    assert "person_link" not in redeem.text.lower()

    start = client.post(
        "/api/h5/customer/smart-claim-start",
        json={"session_id": session},
    )
    assert start.status_code == 200
    body = start.json()
    assert body["identity_source"] == "demo_invite_overlay"
    assert body["plan"]["mode"] == "MATCHED_KNOWN"
    assert body.get("demo_invite_overlay") is True

    bad = client.post(
        "/api/h5/demo-invite/redeem",
        json={
            "token": "di_bogus_token_yyyyyyyyyyyy",
            "session_id": session,
            "office_id": "office_demo_a",
        },
    )
    assert bad.status_code == 200
    assert bad.json()["ok"] is False
    assert bad.json()["fallback"] == "blank_claim"

    start2 = client.post(
        "/api/h5/customer/smart-claim-start",
        json={"session_id": session},
    )
    assert start2.json()["plan"]["mode"] == "BLANK_DEGRADE"


def test_http_flag_off_blocks_issue(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CHEN_DEMO_INVITE_ENABLED", "0")
    client = TestClient(app)
    r = client.post(
        "/api/inbox/support/demo-invite/issue",
        json={"office_id": "office_demo_a", "scenario_id": "chen_camry"},
    )
    assert r.status_code == 403
