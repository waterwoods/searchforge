"""P19H-1 — Claim state machine foundation unit tests (full prompt acceptance)."""

from __future__ import annotations

import pytest

from services.fiqa_api.wecom.claim_state import (
    BROKER_NOTE_INJURY_YES_PHONE_FIRST,
    CLAIM_FORBIDDEN_AUTOMATION_CLAIMS,
    CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
    CLAIM_PHASE_BROKER_DONE,
    CLAIM_PHASE_OTHER_PARTY_COMPLETE,
    CLAIM_PHASE_PHOTOS_IN_PROGRESS,
    CLAIM_PHASE_STARTED,
    CLAIM_PHASE_SUMMARY_READY,
    CLAIM_SAFE_COPY_INVARIANTS,
    CUSTOMER_ACTION_COLLECT_ACCIDENT_BASICS,
    CUSTOMER_ACTION_COLLECT_CLAIM_PHOTOS,
    CUSTOMER_ACTION_COLLECT_INJURY_POLICE,
    CUSTOMER_ACTION_COLLECT_OTHER_PARTY_INFO,
    SERVICE_LANE_CLAIM,
    are_claim_photos_complete,
    derive_claim_phase,
    get_claim_missing_items,
    is_accident_basics_complete,
    is_claim_summary_ready,
    is_injury_police_complete,
    is_other_party_info_complete,
    is_valid_claim_required_text,
    normalize_claim_yes_no,
    suggest_next_claim_transition,
)


def _basics_case() -> dict:
    return {
        "service_lane": SERVICE_LANE_CLAIM,
        "known_facts": {
            "accident_datetime": "今天上午约10点",
            "accident_location": "Irvine Blvd & Culver",
            "accident_description": "对方变道刮蹭我左前门",
        },
        "collected_fields": ["accident_datetime", "accident_location", "accident_description"],
    }


def _damage_attachment() -> dict:
    return {
        "attachment_id": "a1",
        "source": "h5_task",
        "slot_assignment": "customer_damage_photo",
    }


def _vehicle_attachment() -> dict:
    return {
        "attachment_id": "a2",
        "source": "h5_task",
        "slot_assignment": "other_party_vehicle_photo",
    }


def _injury_police_no() -> dict:
    return {
        "known_facts": {"anyone_injured": "否", "police_involved": "否"},
        "collected_fields": ["anyone_injured", "police_involved"],
    }


def _merge_case(*parts: dict) -> dict:
    out: dict = {"service_lane": SERVICE_LANE_CLAIM}
    for part in parts:
        out.update({k: v for k, v in part.items() if k not in ("known_facts", "collected_fields", "case_attachments")})
        if "known_facts" in part:
            out.setdefault("known_facts", {}).update(part["known_facts"])
        if "collected_fields" in part:
            out.setdefault("collected_fields", []).extend(part["collected_fields"])
        if "case_attachments" in part:
            out.setdefault("case_attachments", []).extend(part["case_attachments"])
    return out


# --- 1–10 Phase predicates ---


def test_01_empty_claim_missing_three_basics():
    case = {"service_lane": SERVICE_LANE_CLAIM, "claim_phase": CLAIM_PHASE_STARTED}
    assert is_accident_basics_complete(case) is False
    missing = {m["field"] for m in get_claim_missing_items(case)}
    assert {"accident_datetime", "accident_location", "accident_description"}.issubset(missing)
    suggestion = suggest_next_claim_transition(case)
    assert suggestion["current_phase"] == CLAIM_PHASE_STARTED
    assert suggestion["customer_next_action"] == CUSTOMER_ACTION_COLLECT_ACCIDENT_BASICS


def test_02_accident_basics_complete():
    case = _basics_case()
    assert is_accident_basics_complete(case) is True


def test_03_photos_incomplete_without_damage_photo():
    case = _merge_case(_basics_case())
    assert are_claim_photos_complete(case) is False


def test_04_photos_incomplete_damage_only_no_vehicle_or_plate():
    case = _merge_case(_basics_case(), {"case_attachments": [_damage_attachment()]})
    assert are_claim_photos_complete(case) is False


def test_05_photos_complete_damage_and_vehicle_photo():
    case = _merge_case(
        _basics_case(),
        {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
    )
    assert are_claim_photos_complete(case) is True


def test_06_photos_complete_damage_and_plate_text():
    case = _merge_case(
        _basics_case(),
        {
            "case_attachments": [_damage_attachment()],
            "known_facts": {"other_party_plate": "8ABC123"},
        },
    )
    assert are_claim_photos_complete(case) is True


def test_07_other_party_complete_insurance_card_slot():
    case = _merge_case(
        _basics_case(),
        {
            "case_attachments": [
                _damage_attachment(),
                _vehicle_attachment(),
                {
                    "attachment_id": "a3",
                    "source": "h5_task",
                    "slot_assignment": "other_party_insurance_card",
                },
            ]
        },
    )
    assert is_other_party_info_complete(case) is True


def test_08_other_party_complete_phone_only():
    case = _merge_case(
        _basics_case(),
        {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
        {"known_facts": {"other_party_phone": "9491234567"}},
    )
    assert is_other_party_info_complete(case) is True


def test_09_injury_police_complete_only_when_both_set():
    partial = _merge_case(
        _basics_case(),
        {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
        {"known_facts": {"anyone_injured": "否"}, "collected_fields": ["anyone_injured"]},
    )
    assert is_injury_police_complete(partial) is False
    full = _merge_case(partial, _injury_police_no())
    assert is_injury_police_complete(full) is True


def test_10_summary_ready_only_when_all_required_true():
    almost = _merge_case(
        _basics_case(),
        {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
    )
    assert is_claim_summary_ready(almost) is False
    complete = _merge_case(
        _basics_case(),
        {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
        _injury_police_no(),
    )
    assert is_claim_summary_ready(complete) is True


# --- 11–16 Transition suggestions ---


def test_11_empty_claim_next_collect_accident_basics():
    suggestion = suggest_next_claim_transition({"claim_phase": CLAIM_PHASE_STARTED})
    assert suggestion["customer_next_action"] == CUSTOMER_ACTION_COLLECT_ACCIDENT_BASICS
    assert suggestion["next_phase"] == CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS


def test_12_basics_complete_next_collect_claim_photos():
    suggestion = suggest_next_claim_transition(_basics_case())
    assert suggestion["customer_next_action"] == CUSTOMER_ACTION_COLLECT_CLAIM_PHOTOS
    assert suggestion["next_phase"] == CLAIM_PHASE_PHOTOS_IN_PROGRESS


def test_13_photos_complete_next_collect_other_party_or_injury():
    with_vehicle = _merge_case(
        _basics_case(),
        {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
    )
    suggestion = suggest_next_claim_transition(with_vehicle)
    assert are_claim_photos_complete(with_vehicle) is True
    assert is_other_party_info_complete(with_vehicle) is True
    assert suggestion["customer_next_action"] == CUSTOMER_ACTION_COLLECT_INJURY_POLICE

    with_plate_only = _merge_case(
        _basics_case(),
        {
            "case_attachments": [_damage_attachment()],
            "known_facts": {"other_party_plate": "8ABC123"},
        },
    )
    assert suggest_next_claim_transition(with_plate_only)["customer_next_action"] == (
        CUSTOMER_ACTION_COLLECT_INJURY_POLICE
    )


def test_14_other_party_complete_next_collect_injury_police():
    case = _merge_case(
        _basics_case(),
        {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
        {"known_facts": {"other_party_name": "王先生"}},
    )
    suggestion = suggest_next_claim_transition(case)
    assert is_other_party_info_complete(case) is True
    assert suggestion["customer_next_action"] == CUSTOMER_ACTION_COLLECT_INJURY_POLICE
    assert derive_claim_phase(case) == CLAIM_PHASE_OTHER_PARTY_COMPLETE


def test_15_all_complete_ready_for_broker_review():
    case = _merge_case(
        _basics_case(),
        {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
        {"known_facts": {"other_party_phone": "9491234567"}},
        _injury_police_no(),
    )
    suggestion = suggest_next_claim_transition(case)
    assert suggestion["ready_for_broker_review"] is True
    assert suggestion["next_phase"] == CLAIM_PHASE_SUMMARY_READY
    assert derive_claim_phase(case) == CLAIM_PHASE_SUMMARY_READY


def test_16_injury_yes_manual_handle_in_snapshot():
    case = _merge_case(
        _basics_case(),
        {"known_facts": {"anyone_injured": "是"}, "collected_fields": ["anyone_injured"]},
    )
    suggestion = suggest_next_claim_transition(case)
    assert suggestion["needs_broker_manual_handle"] is True
    assert suggestion["broker_note"] == BROKER_NOTE_INJURY_YES_PHONE_FIRST
    assert derive_claim_phase(case) != CLAIM_PHASE_BROKER_DONE


# --- 17–20 Guardrails ---


def test_17_summary_ready_is_not_broker_done():
    case = _merge_case(
        _basics_case(),
        {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
        {"known_facts": {"other_party_phone": "9491234567"}},
        _injury_police_no(),
    )
    assert is_claim_summary_ready(case) is True
    assert derive_claim_phase(case) == CLAIM_PHASE_SUMMARY_READY
    assert derive_claim_phase(case) != CLAIM_PHASE_BROKER_DONE


def test_18_broker_done_is_only_true_end():
    case = _merge_case(
        _basics_case(),
        {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
        {"known_facts": {"other_party_phone": "9491234567"}},
        _injury_police_no(),
        {"broker_confirmed_at": "2026-07-07T12:00:00Z"},
    )
    assert derive_claim_phase(case) == CLAIM_PHASE_BROKER_DONE


def test_19_forbidden_phrases_constants():
    assert "已经帮您报案" in CLAIM_FORBIDDEN_AUTOMATION_CLAIMS
    assert "理赔已经提交" in CLAIM_FORBIDDEN_AUTOMATION_CLAIMS
    assert len(CLAIM_SAFE_COPY_INVARIANTS) >= 5


def test_20_module_docstring_notes_postgres_facade():
    import services.fiqa_api.wecom.claim_state as mod

    doc = mod.__doc__ or ""
    assert "get_case_for_read" in doc
    assert "forbidden" in doc.lower() or "Legacy JSON-only" in doc


# --- 21–24 Shape compatibility ---


def test_21_collected_fields_shape():
    case = {
        "collected_fields": ["accident_datetime", "accident_location", "accident_description"],
        "known_facts": {
            "accident_datetime": "10am",
            "accident_location": "Irvine",
            "accident_description": "rear-end",
        },
    }
    assert is_accident_basics_complete(case) is True


def test_22_known_facts_shape():
    case = {
        "collected_fields": ["accident_location"],
        "known_facts": {"accident_location": "Main St"},
    }
    assert is_accident_basics_complete(case) is False
    assert is_valid_claim_required_text(case["known_facts"]["accident_location"]) is True


def test_23_case_attachments_slot_metadata():
    case = {
        "case_attachments": [
            {"source": "h5_task", "slot_assignment": "customer_damage_photo"},
            {"source": "h5_task", "slot_assignment": "other_party_vehicle_photo"},
        ]
    }
    assert are_claim_photos_complete(case) is True


def test_24_missing_extra_keys_graceful():
    assert derive_claim_phase({}) == CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS
    assert suggest_next_claim_transition({})["missing_items"]
    assert normalize_claim_yes_no(None) is None
    assert normalize_claim_yes_no("是") == "yes"
    assert normalize_claim_yes_no("没受伤") == "no"


def test_explicit_phase_photos_in_progress_with_partial_upload():
    case = _merge_case(
        _basics_case(),
        {
            "case_attachments": [_damage_attachment()],
            "claim_phase": CLAIM_PHASE_PHOTOS_IN_PROGRESS,
        },
    )
    assert are_claim_photos_complete(case) is False
    assert derive_claim_phase(case) == CLAIM_PHASE_PHOTOS_IN_PROGRESS
