"""P19D-2 — H5 task token tests."""

from __future__ import annotations

import time

import pytest

from services.fiqa_api.inbox_triage.h5_task_token import (
    DEFAULT_TTL_SECONDS,
    issue_h5_flow_token,
    issue_h5_task_token,
    verify_h5_task_token,
)


def test_issue_and_verify_token():
    token = issue_h5_task_token(case_id="case_test1", lane="add_car", slot="vin_photo")
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.case_id == "case_test1"
    assert claims.lane == "add_car"
    assert claims.slot == "vin_photo"
    assert claims.nonce


def test_token_includes_user_ref_not_full_external_userid():
    token = issue_h5_task_token(
        case_id="case_test2",
        external_userid="wm_full_secret_external_userid_12345",
    )
    assert "wm_full_secret" not in token
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.user_ref
    assert len(claims.user_ref) == 8


def test_expired_token_rejected():
    now = time.time()
    token = issue_h5_task_token(
        case_id="case_exp",
        ttl_seconds=60,
        now=now - 120,
    )
    claims = verify_h5_task_token(token, now=now)
    assert claims is None


def test_tampered_token_rejected():
    token = issue_h5_task_token(case_id="case_tamper")
    bad = token[:-4] + "xxxx"
    assert verify_h5_task_token(bad) is None


def test_wrong_slot_rejected_at_issue():
    with pytest.raises(ValueError, match="unsupported_slot"):
        issue_h5_task_token(case_id="case_x", slot="not_a_slot")


def test_flow_token_issue_and_verify():
    token = issue_h5_flow_token(case_id="case_flow")
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.is_flow_token
    assert claims.slots == ("vin_photo", "registration_photo", "insurance_card_photo")


def test_token_case_id_immutable():
    token = issue_h5_task_token(case_id="case_orig")
    # Tamper payload case_id by flipping a char in b64 segment
    prefix, rest = token.split("h5t1.", 1)
    b64, sig = rest.rsplit(".", 1)
    flipped = ("A" if b64[0] != "A" else "B") + b64[1:]
    tampered = f"h5t1.{flipped}.{sig}"
    claims = verify_h5_task_token(tampered)
    assert claims is None or claims.case_id != "case_orig"


def test_default_ttl_is_24h():
    now = time.time()
    token = issue_h5_task_token(case_id="case_ttl", now=now)
    claims = verify_h5_task_token(token, now=now + DEFAULT_TTL_SECONDS - 10)
    assert claims is not None
    assert verify_h5_task_token(token, now=now + DEFAULT_TTL_SECONDS + 120) is None
