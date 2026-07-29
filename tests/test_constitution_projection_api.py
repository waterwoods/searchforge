"""P24D1 — Constitution Projection API integration contracts."""

from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_store import save_case
from services.fiqa_api.inbox_triage.constitution_projection import (
    BAND_CUSTOMER_DONE_AWAITING,
    BAND_CUSTOMER_MISSING,
    STAGE_CUSTOMER_ACTION_NEEDED,
    STAGE_WAITING_BROKER,
    attach_constitution_projection,
    attach_constitution_queue_projection,
    build_constitution_customer_projection,
    build_constitution_projection,
    build_constitution_queue_projection,
)
from services.fiqa_api.inbox_triage.h5_task_intake import intake_info_for_token
from services.fiqa_api.inbox_triage.h5_task_token import (
    issue_h5_intake_form_token,
    verify_h5_task_token,
)
from services.fiqa_api.routes.h5_task_intake import router as h5_router
from services.fiqa_api.routes.inbox_triage import router as inbox_router
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


@pytest.fixture(autouse=True)
def _json_store():
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


def _api_client() -> TestClient:
    app = FastAPI()
    app.include_router(inbox_router)
    app.include_router(h5_router)
    return TestClient(app)


def _camry_slice1_before() -> dict:
    return {
        "case_id": "case-chen-camry",
        "workflow_state": "broker_more_requested",
        "customer_next_action": {
            "action_type": "provide_evidence",
            "title": "上传保险卡",
            "required_input": "policy_or_insurance_card",
            "status": "active",
        },
        "broker_next_action": {
            "action_type": "wait_for_customer_item",
            "status": "waiting_for_customer",
        },
        "open_request": {
            "status": "open",
            "active_item": {
                "item_type": "policy_or_insurance_card",
                "label": "上传保险卡",
                "status": "active",
            },
            "queued_items": [],
            "items": [
                {
                    "item_type": "policy_or_insurance_card",
                    "label": "上传保险卡",
                    "status": "active",
                }
            ],
        },
    }


def _camry_slice1_after() -> dict:
    return {
        "case_id": "case-chen-camry",
        "workflow_state": "broker_review_ready",
        "customer_next_action": {
            "action_type": "wait_for_broker_review",
            "title": "资料已收到",
            "required_input": None,
            "status": "waiting",
        },
        "broker_next_action": {
            "action_type": "review_customer_response",
            "status": "review_ready",
        },
        "open_request": {
            "status": "completed",
            "active_item": None,
            "queued_items": [],
            "items": [
                {
                    "item_type": "policy_or_insurance_card",
                    "label": "上传保险卡",
                    "status": "satisfied",
                }
            ],
        },
    }


def _seed_camry_case(*, after_upload: bool = False) -> str:
    from services.fiqa_api.inbox_triage.case_store import (
        _read_payload,
        _write_payload,
        apply_p20_slice1_compat_projection,
        get_case_by_id,
        patch_case_known_facts,
        update_case_customer,
    )

    case = save_case(
        "Camry claim",
        {
            "issue_category": "claim_intake",
            "urgency": "high",
            "manual_followup_needed": True,
            "broker_next_step": "Review claim",
            "client_prep": "",
            "client_reply_draft": "",
        },
        service_lane=SERVICE_LANE_CLAIM,
    )
    case_id = str(case["case_id"])
    update_case_customer(case_id, customer_name="陈明")
    patch_case_known_facts(
        case_id,
        {
            "own_vehicle_info": "2020 Toyota Camry",
            "accident_location": "停车场",
            "accident_description": "倒车碰撞，前保险杠受损",
        },
        source="customer_task",
    )
    slice1 = _camry_slice1_after() if after_upload else _camry_slice1_before()
    slice1["case_id"] = case_id
    apply_p20_slice1_compat_projection(
        case_id,
        {
            "claim_phase": (
                "intake_ready_for_broker" if after_upload else "broker_needs_more_info"
            ),
            "p20_slice1_projection": slice1,
            "slice1_projection": slice1,
        },
    )
    # Persist light brief/evidence for list queue path (no builder required).
    payload = _read_payload()
    for row in payload["cases"]:
        if str(row.get("case_id")) != case_id:
            continue
        row["claim_case_brief"] = {
            "summary": "客户已提交事故经过和现场照片。",
            "missing_info": ["保险卡"] if not after_upload else ["驾驶证"],
            "brief_version": 1,
        }
        row["claim_evidence_summary"] = {
            "received_slots": ["scene_photo"],
            "missing_required_slots": [],
        }
        break
    _write_payload(payload)
    assert get_case_by_id(case_id) is not None
    return case_id


def test_detail_includes_full_constitution_customer_and_broker(monkeypatch):
    case_id = _seed_camry_case(after_upload=False)
    # Detail refreshes live Slice1 — stub to stored Camry before-upload truth.
    monkeypatch.setattr(
        "services.fiqa_api.routes.inbox_triage.default_slice1_service",
        lambda: type(
            "Svc",
            (),
            {"fetch_projection": staticmethod(lambda cid: _camry_slice1_before() | {"case_id": cid})},
        )(),
    )
    monkeypatch.setattr(
        "services.fiqa_api.routes.inbox_triage.default_case_intake_service",
        lambda: type("Svc", (), {"fetch_projection": staticmethod(lambda _cid: None)})(),
    )
    monkeypatch.setattr(
        "services.fiqa_api.routes.inbox_triage.default_send_request_service",
        lambda: type(
            "Svc",
            (),
            {"fetch_customer_access_card": staticmethod(lambda _cid: None)},
        )(),
    )

    client = _api_client()
    resp = client.get(f"/api/inbox/cases/{case_id}")
    assert resp.status_code == 200
    row = resp.json()
    # Existing fields remain present.
    assert row["case_id"] == case_id
    assert row.get("service_lane") == SERVICE_LANE_CLAIM

    cp = row["constitution_projection"]
    assert set(cp.keys()) == {
        "projection_version",
        "case_id",
        "current_stage",
        "customer",
        "broker",
    }
    assert cp["case_id"] == case_id
    assert cp["customer"]["today"] == "上传保险卡"
    assert cp["customer"]["current_stage"] == STAGE_CUSTOMER_ACTION_NEEDED
    assert cp["broker"]["priority"]["band"] == BAND_CUSTOMER_MISSING
    assert cp["broker"]["next_action"]["label"] == "暂无动作"
    assert cp["broker"]["next_action"]["enabled"] is False
    assert "case_conclusion" in cp["broker"]
    assert cp["broker"]["case_conclusion"]["customer_focus"] == "上传保险卡"


def test_detail_uses_live_slice1_state(monkeypatch):
    case_id = _seed_camry_case(after_upload=False)
    live = _camry_slice1_after()
    live["case_id"] = case_id
    monkeypatch.setattr(
        "services.fiqa_api.routes.inbox_triage.default_slice1_service",
        lambda: type(
            "Svc",
            (),
            {"fetch_projection": staticmethod(lambda _cid: live)},
        )(),
    )
    monkeypatch.setattr(
        "services.fiqa_api.routes.inbox_triage.default_case_intake_service",
        lambda: type("Svc", (), {"fetch_projection": staticmethod(lambda _cid: None)})(),
    )
    monkeypatch.setattr(
        "services.fiqa_api.routes.inbox_triage.default_send_request_service",
        lambda: type(
            "Svc",
            (),
            {"fetch_customer_access_card": staticmethod(lambda _cid: None)},
        )(),
    )

    row = _api_client().get(f"/api/inbox/cases/{case_id}").json()
    cp = row["constitution_projection"]
    assert cp["customer"]["today"] == "先不用操作"
    assert cp["customer"]["current_stage"] == STAGE_WAITING_BROKER
    assert cp["broker"]["next_action"]["label"] == "审核保险卡"
    assert cp["broker"]["priority"]["band"] == BAND_CUSTOMER_DONE_AWAITING


def test_h5_intake_includes_customer_constitution_and_keeps_fields():
    case_id = _seed_camry_case(after_upload=False)
    token = issue_h5_intake_form_token(case_id=case_id)
    claims = verify_h5_task_token(token)
    assert claims is not None

    # Avoid live Slice1 DB: put projection on case and disable feature fetch path noise
    # by stubbing fetch to return stored-shaped projection.
    import services.fiqa_api.inbox_triage.h5_task_intake as h5_mod

    before_keys = None

    def _fake_slice1(case):
        return dict(case.get("p20_slice1_projection") or {}), False

    h5_mod._slice1_projection_for_case = _fake_slice1  # type: ignore[attr-defined]

    info = intake_info_for_token(claims)  # type: ignore[arg-type]
    before_keys = set(info.keys())
    assert "task_contract" in info
    assert "constitution_projection" in info
    cp = info["constitution_projection"]
    assert set(cp.keys()) == {
        "projection_version",
        "case_id",
        "current_stage",
        "customer",
    }
    assert "broker" not in cp
    assert cp["customer"]["today"] == "上传保险卡"
    assert cp["customer"]["why"] == "事故经过和现场照片已经完成。"
    assert cp["customer"]["after"] == "陈总会尽快联系您。"
    # Existing H5 fields unchanged in presence.
    for key in (
        "lane",
        "flow",
        "case_id",
        "current_step",
        "submitted",
        "phase",
        "task_contract",
        "key_facts",
        "missing_info",
    ):
        assert key in before_keys


def test_h5_route_returns_customer_constitution(monkeypatch):
    case_id = _seed_camry_case(after_upload=True)
    token = issue_h5_intake_form_token(case_id=case_id)
    import services.fiqa_api.inbox_triage.h5_task_intake as h5_mod

    monkeypatch.setattr(
        h5_mod,
        "_slice1_projection_for_case",
        lambda case: (dict(case.get("p20_slice1_projection") or {}), False),
    )
    resp = _api_client().get(f"/api/h5/tasks/{token}/intake")
    assert resp.status_code == 200
    body = resp.json()
    assert body["case_id"] == case_id
    assert isinstance(body.get("task_contract"), dict)
    cp = body["constitution_projection"]
    assert cp["customer"]["today"] == "先不用操作"
    assert cp["customer"]["current_stage"] == STAGE_WAITING_BROKER
    assert "broker" not in cp


def test_list_includes_lightweight_queue_constitution():
    before_id = _seed_camry_case(after_upload=False)
    after_id = _seed_camry_case(after_upload=True)
    client = _api_client()
    resp = client.get("/api/inbox/cases", params={"limit": 50})
    assert resp.status_code == 200
    cases = resp.json()["cases"]
    by_id = {c["case_id"]: c for c in cases}

    before = by_id[before_id]
    after = by_id[after_id]
    for row in (before, after):
        cp = row["constitution_projection"]
        assert set(cp.keys()) == {
            "projection_version",
            "case_id",
            "current_stage",
            "broker",
        }
        assert "customer" not in cp
        assert set(cp["broker"].keys()) == {
            "queue_summary",
            "next_action",
            "priority",
            "current_stage",
        }
        assert "case_conclusion" not in cp["broker"]

    assert before["constitution_projection"]["broker"]["priority"]["band"] == BAND_CUSTOMER_MISSING
    assert before["constitution_projection"]["broker"]["next_action"]["label"] == "暂无动作"
    assert before["constitution_projection"]["broker"]["next_action"]["enabled"] is False

    assert after["constitution_projection"]["broker"]["priority"]["band"] == BAND_CUSTOMER_DONE_AWAITING
    assert after["constitution_projection"]["broker"]["next_action"]["label"] == "审核保险卡"
    assert after["constitution_projection"]["broker"]["next_action"]["enabled"] is True


def test_projection_failure_does_not_break_reads(monkeypatch):
    case_id = _seed_camry_case(after_upload=False)

    def _boom(*_a, **_k):
        raise RuntimeError("constitution_boom")

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.constitution_projection.build_constitution_projection",
        _boom,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.constitution_projection.build_constitution_queue_projection",
        _boom,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.constitution_projection.build_constitution_customer_projection",
        _boom,
    )
    monkeypatch.setattr(
        "services.fiqa_api.routes.inbox_triage.default_slice1_service",
        lambda: type(
            "Svc",
            (),
            {"fetch_projection": staticmethod(lambda cid: _camry_slice1_before() | {"case_id": cid})},
        )(),
    )
    monkeypatch.setattr(
        "services.fiqa_api.routes.inbox_triage.default_case_intake_service",
        lambda: type("Svc", (), {"fetch_projection": staticmethod(lambda _cid: None)})(),
    )
    monkeypatch.setattr(
        "services.fiqa_api.routes.inbox_triage.default_send_request_service",
        lambda: type(
            "Svc",
            (),
            {"fetch_customer_access_card": staticmethod(lambda _cid: None)},
        )(),
    )

    client = _api_client()
    detail = client.get(f"/api/inbox/cases/{case_id}")
    assert detail.status_code == 200
    assert detail.json()["case_id"] == case_id

    listing = client.get("/api/inbox/cases", params={"limit": 50})
    assert listing.status_code == 200
    assert any(c["case_id"] == case_id for c in listing.json()["cases"])

    import services.fiqa_api.inbox_triage.h5_task_intake as h5_mod

    monkeypatch.setattr(
        h5_mod,
        "_slice1_projection_for_case",
        lambda case: (dict(case.get("p20_slice1_projection") or {}), False),
    )
    token = issue_h5_intake_form_token(case_id=case_id)
    h5 = client.get(f"/api/h5/tasks/{token}/intake")
    assert h5.status_code == 200
    assert h5.json()["case_id"] == case_id


def test_attach_helpers_do_not_mutate_unrelated_fields():
    case = {
        "case_id": "case_mutate_check",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_needs_more_info",
        "p20_slice1_projection": _camry_slice1_before(),
        "claim_case_brief": {"summary": "x", "missing_info": [], "brief_version": 1},
        "claim_evidence_summary": {"received_slots": ["scene_photo"]},
        "known_facts": {"accident_description": "刮蹭"},
    }
    before = copy.deepcopy(case)
    attach_constitution_projection(case)
    for key in before:
        assert case[key] == before[key]
    assert "constitution_projection" in case

    case2 = copy.deepcopy(before)
    attach_constitution_queue_projection(case2)
    for key in before:
        assert case2[key] == before[key]
    assert "case_conclusion" not in case2["constitution_projection"]["broker"]


def test_queue_and_full_share_same_band_rules():
    from services.fiqa_api.inbox_triage.constitution_projection import ConstitutionInputs

    case = {
        "case_id": "case-rule-parity",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_needs_more_info",
        "p20_slice1_projection": _camry_slice1_before(),
        "known_facts": {
            "own_vehicle_info": "2020 Toyota Camry",
            "accident_description": "倒车碰撞",
        },
    }
    inputs = ConstitutionInputs(case=case)
    full = build_constitution_projection(inputs)
    queue = build_constitution_queue_projection(inputs)
    customer = build_constitution_customer_projection(inputs)
    assert queue["broker"]["priority"] == full["broker"]["priority"]
    assert queue["broker"]["next_action"]["label"] == full["broker"]["next_action"]["label"]
    assert customer["customer"]["today"] == full["customer"]["today"]
    assert customer["current_stage"] == full["current_stage"]
