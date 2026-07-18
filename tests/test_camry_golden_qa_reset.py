"""P24G — Camry Golden QA reset: deterministic seed + Constitution verification."""

from __future__ import annotations

import json

import pytest

from scripts.camry_golden_qa import (
    DEMO_NAME,
    EXPECTED_BROKER,
    EXPECTED_CUSTOMER,
    configure_ephemeral_local,
    list_golden_case_ids,
    mint_golden_token,
    remove_golden_cases,
    reset_golden_qa,
    seed_golden_case,
    verify_via_apis,
)


@pytest.fixture()
def golden_local(monkeypatch):
    path = configure_ephemeral_local()
    yield path


def test_reset_is_idempotent_and_deterministic(golden_local):
    first = reset_golden_qa(target="local", reseed=True, dry_run=False)
    assert first.get("case_id")
    assert first.get("token")
    assert first["verification"]["ok"] is True

    case_id_1 = first["case_id"]
    second = reset_golden_qa(target="local", reseed=True, dry_run=False)
    assert second["verification"]["ok"] is True
    assert second["case_id"] != case_id_1  # fresh case id invalidates prior token binding
    assert second["token"] != first["token"]

    ids = list_golden_case_ids("local")
    assert ids == [second["case_id"]]


def test_seed_matches_golden_constitution(golden_local):
    case = seed_golden_case(target="local", dry_run=False)
    case_id = str(case["case_id"])
    assert case.get("demo_name") == DEMO_NAME
    assert bool(case.get("workbench_test")) is True

    token = str(mint_golden_token(case_id)["token"])
    report = verify_via_apis(case_id, token, prefer_live_slice1=False)
    assert report["ok"] is True, report["defects"]
    assert report["checks"]["constitution_pure"] == "PASS"
    assert report["checks"]["customer_api"] == "PASS"
    assert report["checks"]["case_detail"] == "PASS"
    assert report["checks"]["case_list"] == "PASS"

    cust = report["constitution_projection"]["customer"]
    broker = report["constitution_projection"]["broker"]
    assert cust["today"] == EXPECTED_CUSTOMER["today"]
    assert cust["why"] == EXPECTED_CUSTOMER["why"]
    assert cust["after"] == EXPECTED_CUSTOMER["after"]
    assert cust["current_stage"] == EXPECTED_CUSTOMER["current_stage"]
    assert broker["next_action"]["label"] == EXPECTED_BROKER["next_label"]
    assert broker["next_action"]["enabled"] is False
    assert broker["next_action"]["note"] == EXPECTED_BROKER["next_note"]
    assert broker["priority"]["band"] == EXPECTED_BROKER["priority_band"]
    assert broker["queue_summary"]["why_attention"] == EXPECTED_BROKER["why_attention"]


def test_remove_only_touches_golden_tag(golden_local):
    from services.fiqa_api.inbox_triage.case_store import list_all_cases, save_case
    from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

    other = save_case(
        "unrelated case",
        {
            "issue_category": "claim_intake",
            "urgency": "low",
            "manual_followup_needed": False,
            "broker_next_step": "n/a",
            "client_prep": "",
            "client_reply_draft": "",
        },
        service_lane=SERVICE_LANE_CLAIM,
    )
    other_id = str(other["case_id"])
    seed_golden_case(target="local", dry_run=False)
    removed = remove_golden_cases(target="local", dry_run=False)
    assert removed
    remaining_ids = {str(c.get("case_id")) for c in list_all_cases()}
    assert other_id in remaining_ids
    assert not list_golden_case_ids("local")


def test_fail_closed_when_verify_impossible(golden_local, monkeypatch):
    # Force verify to always fail after seed
    monkeypatch.setattr(
        "scripts.camry_golden_qa.verify_via_apis",
        lambda *a, **k: {"ok": False, "checks": {}, "defects": ["forced_fail"]},
    )
    with pytest.raises(RuntimeError, match="golden_reset_failed_closed"):
        reset_golden_qa(target="local", reseed=True, dry_run=False)
    # Recovery remove+reseed still ends fail-closed; no half-success handoff required
    assert list_golden_case_ids("local")  # case may exist but must not be treated ready


def test_handoff_json_shape(golden_local, tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.camry_golden_qa.ARTIFACT_DIR", tmp_path)
    handoff = reset_golden_qa(target="local", reseed=True, dry_run=False)
    path = tmp_path / "handoff.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["case_id"] == handoff["case_id"]
    assert data["token"]
    assert data["devtools_launch_query"].startswith("token=")
    assert data["verification"]["ok"] is True
