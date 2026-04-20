from __future__ import annotations

import json

from services.fiqa_api.db.service_record_repository import _build_structured_payload
from services.fiqa_api.inbox_triage.case_store import (
    merge_light_identity_from_client_payload,
    save_case,
)


def test_merge_light_identity_from_client_payload_accepts_enum_and_nulls():
    out = merge_light_identity_from_client_payload(
        identity_binding_state="deferred",
        person_link_key=None,
        person_link_source="wechat",
        person_link_confidence=0.25,
    )
    assert out == {
        "identity_binding_state": "deferred",
        "person_link_source": "wechat",
        "person_link_confidence": 0.25,
    }


def test_merge_light_identity_drops_invalid_state():
    assert (
        merge_light_identity_from_client_payload(
            identity_binding_state="not_a_real_state",
            person_link_key=None,
            person_link_source=None,
            person_link_confidence=None,
        )
        == {}
    )


def test_build_structured_payload_includes_identity_keys():
    case = {
        "identity_binding_state": "unbound",
        "person_link_key": "opaque-1",
        "person_link_source": "wechat",
        "person_link_confidence": 0.5,
        "noise_key": "ignored",
    }
    sp = _build_structured_payload(case)
    assert sp["identity_binding_state"] == "unbound"
    assert sp["person_link_key"] == "opaque-1"
    assert sp["person_link_source"] == "wechat"
    assert sp["person_link_confidence"] == 0.5
    assert "noise_key" not in sp


def test_save_case_persists_identity_fields(monkeypatch, tmp_path):
    store = tmp_path / "cases.json"
    store.write_text(json.dumps({"cases": []}), encoding="utf-8")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))

    tr = {
        "issue_category": "customer_question",
        "urgency": "medium",
        "broker_next_step": "x",
        "client_prep": "y",
        "client_reply_draft": "z",
        "manual_followup_needed": False,
        "identity_binding_state": "prompted",
        "person_link_key": None,
        "person_link_source": None,
        "person_link_confidence": None,
    }
    case = save_case("[客户] hello", tr)
    assert case.get("identity_binding_state") == "prompted"
    assert case.get("person_link_key") is None
