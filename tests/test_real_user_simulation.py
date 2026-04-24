"""
Real-user-style Add-Car simulation: fragmented input, routing, continuity, and concurrency.

Uses triage_conversation / triage_for_append and the inbox triage route (async) with targeted
monkeypatches — no core logic changes in production modules.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.inbox_triage.add_car_field_contract import quote_ready_matches_still_needed
from services.fiqa_api.inbox_triage.case_binding import resolve_active_case
from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_for_append
from services.fiqa_api.routes import inbox_triage
from services.fiqa_api.routes.inbox_triage import (
    TriageRequest,
    _attach_case_lifecycle,
    _finalize_triage_api_result,
    triage_inbox,
)


def _run_triage(req: TriageRequest) -> dict:
    return asyncio.run(triage_inbox(req))


def _api_finalize(result: dict, *, persisted_case: dict | None = None) -> dict:
    """Mirror POST /api/inbox/triage attachment after triage_conversation."""
    r = dict(result)
    _attach_case_lifecycle(r, persisted_case=persisted_case)
    _finalize_triage_api_result(r)
    return r


def _assert_stable_add_car_contract(
    r: dict,
    *,
    expect_case_id: bool = False,
) -> None:
    """Fields the route layer keeps stable for Add-Car clients (after finalize)."""
    assert isinstance(r.get("collected_fields"), list)
    assert isinstance(r.get("still_needed_fields"), list)
    assert str(r.get("quote_ready_status") or "") in ("", "need_more", "almost_ready", "quote_ready")
    assert isinstance(r.get("next_best_question"), str)
    assert r.get("append_allowed") is True or r.get("append_allowed") is False
    assert isinstance(r.get("case_lifecycle"), str) and r.get("case_lifecycle")
    if str(r.get("service_type") or "").lower() == "add_car":
        assert quote_ready_matches_still_needed(
            str(r.get("quote_ready_status") or ""),
            r.get("still_needed_fields"),
        )
    if expect_case_id:
        assert str(r.get("case_id") or "").strip()


# --- PART 1 — Pre-production checks ---


def test_check1_ui_contract_first_turn_mid_flow_append_blocked():
    """CHECK 2 — UI contract: core keys after API-style finalize across representative states."""
    t1 = _api_finalize(triage_conversation("I want to add a car", [], client_id="chen_kui"))
    _assert_stable_add_car_contract(t1)

    turns = [{"role": "customer", "text": "I want to add a car"}]
    t2 = _api_finalize(triage_conversation("VIN is 1HGCM82633A004352", turns, client_id="chen_kui"))
    _assert_stable_add_car_contract(t2)

    ctx = {
        "formal_submitted_at": "2026-03-01T12:00:00Z",
        "service_record_append": True,
        "vehicle_key": "vin:1HGCM82633A004352",
    }
    thread = (
        "[客户] 我想加车，2024 Toyota Camry，ZIP 90210，下周提车，我自己开\n\n"
        "[系统] 已记录加车信息，会继续整理。"
    )
    append_ok = _api_finalize(
        triage_for_append(thread, "same VIN 1HGCM82633A004352", client_id="chen_kui", reply_truth_context=ctx)
    )
    _assert_stable_add_car_contract(append_ok)

    blocked = _api_finalize(
        triage_for_append(
            thread,
            "same as my other car",
            client_id="chen_kui",
            reply_truth_context=ctx,
        )
    )
    _assert_stable_add_car_contract(blocked)
    assert blocked.get("append_allowed") is False

    new_issue = _api_finalize(
        triage_for_append(
            thread,
            "I also have another car VIN 1HGBH41JXMN109186",
            client_id="chen_kui",
            reply_truth_context=ctx,
        )
    )
    _assert_stable_add_car_contract(new_issue)
    assert new_issue.get("append_allowed") is False


def test_check1_session_same_browser_continues_case(monkeypatch, tmp_path):
    """CHECK 1 — With session + active_case_id, same case loads for a follow-up zip line."""
    from services.fiqa_api.inbox_triage import session_store as session_store_mod

    cid = "case-sim-1"
    vin = "1HGCM82633A004352"
    fake_case = {
        "case_id": cid,
        "case_status": "new",
        "workbench_archived": False,
        "formal_submitted_at": "2026-01-01T00:00:00Z",
        "lifecycle_status": "office_followup",
        "vehicle_key": f"vin:{vin}",
        "collected_fields": ["vin"],
        "still_needed_fields": ["zip"],
        "client_id": "chen_kui",
    }
    session_store_mod.patch_session_case_binding("sess-same-browser", active_case_id=cid)
    monkeypatch.setattr(inbox_triage, "get_case_for_read", lambda _id: fake_case if _id == cid else None)
    monkeypatch.setattr(inbox_triage, "list_recent_cases_for_read", lambda **_: [fake_case])

    req = TriageRequest(
        text="zip is 95014",
        session_id="sess-same-browser",
        client_id="chen_kui",
    )
    out = _run_triage(req)
    _finalize_triage_api_result(out)
    assert out.get("case_id") == cid


def test_check1_no_session_safe_when_multiple_open_cases(monkeypatch):
    """CHECK 1 — No session: two open cases + zip-only line should not pick a wrong binding."""
    a = {
        "case_id": "c-a",
        "case_status": "new",
        "workbench_archived": False,
        "vehicle_key": "vin:1HGCM82633A004352",
    }
    b = {
        "case_id": "c-b",
        "case_status": "new",
        "workbench_archived": False,
        "vehicle_key": "vin:1HGBH41JXMN109186",
    }
    monkeypatch.setattr(inbox_triage, "list_recent_cases_for_read", lambda **_: [a, b])
    monkeypatch.setattr(inbox_triage, "get_case_for_read", lambda _id: None)

    req = TriageRequest(text="zip is 95014", client_id="chen_kui")
    out = _run_triage(req)
    _finalize_triage_api_result(out)
    assert not out.get("case_id")


def test_check3_case_binding_log(caplog):
    """CHECK 3 — case_binding_decision appears for session_active binding."""
    import logging

    with caplog.at_level(logging.INFO, logger="services.fiqa_api.inbox_triage.case_binding"):
        resolve_active_case({"active_case_id": "case-z"}, [], "vin:ANY")
    assert any("case_binding_decision" in r.getMessage() for r in caplog.records)


def test_check3_append_blocked_log(caplog, monkeypatch, tmp_path):
    """CHECK 3 — append_blocked_reason when new vehicle clears session binding."""
    from services.fiqa_api.inbox_triage import session_store as session_store_mod

    cid = "case-block"
    vin_a = "1HGCM82633A004352"
    fake_case = {
        "case_id": cid,
        "case_status": "new",
        "workbench_archived": False,
        "formal_submitted_at": "2026-01-01T00:00:00Z",
        "vehicle_key": f"vin:{vin_a}",
        "client_id": "chen_kui",
    }
    session_store_mod.patch_session_case_binding("sess-block", active_case_id=cid)
    monkeypatch.setattr(inbox_triage, "get_case_for_read", lambda _id: fake_case if _id == cid else None)
    monkeypatch.setattr(inbox_triage, "list_recent_cases_for_read", lambda **_: [fake_case])

    import logging

    with caplog.at_level(logging.INFO, logger="services.fiqa_api.routes.inbox_triage"):
        req = TriageRequest(
            text=f"actually the VIN is 1HGBH41JXMN109186 not {vin_a}",
            session_id="sess-block",
            client_id="chen_kui",
        )
        _run_triage(req)
    assert any("append_blocked_reason" in r.getMessage() for r in caplog.records)


def test_check3_new_case_created_log(caplog, monkeypatch):
    """CHECK 3 — new_case_created when persist path saves a case."""

    def _fake_save(_source: str, result: dict, **kwargs):
        return {
            "case_id": "case-persist-1",
            "client_id": kwargs.get("client_id") or "chen_kui",
            "lifecycle_status": "handoff_pending",
            "vehicle_key": result.get("vehicle_key") or "vin:1HGCM82633A004352",
            "collected_fields": result.get("collected_fields") or [],
            "still_needed_fields": result.get("still_needed_fields") or [],
            "quote_ready_status": result.get("quote_ready_status") or "quote_ready",
        }

    monkeypatch.setattr(inbox_triage, "save_case", _fake_save)
    monkeypatch.setattr(inbox_triage, "save_session_binding_after_case_created", lambda *a, **k: None)

    import logging

    with caplog.at_level(logging.INFO, logger="services.fiqa_api.routes.inbox_triage"):
        text = (
            "VIN 1HGCM82633A004352 zip 90210 delivery May 10 2026 primary driver is me "
            "2020 Honda Civic"
        )
        req = TriageRequest(
            text=text,
            persist_case=True,
            formal_submit=True,
            client_id="chen_kui",
        )
        _run_triage(req)
    assert any("new_case_created" in r.getMessage() for r in caplog.records)


# --- PART 2 — Scenarios ---


def test_scenario1_fragmented_add_car_accumulates():
    """SCENARIO 1 — Multi-turn fragmented add-car: fields accumulate without reset."""
    vin = "1HGCM82633A004352"
    t1 = triage_conversation("I want to add a car", [], client_id="chen_kui")
    assert t1.get("service_type") == "add_car"

    turns = [{"role": "customer", "text": "I want to add a car"}]
    t2 = triage_conversation(f"VIN is {vin}", turns, client_id="chen_kui")
    assert "vin" in {str(x).lower() for x in (t2.get("collected_fields") or [])}

    turns.append({"role": "customer", "text": f"VIN is {vin}"})
    t3 = triage_conversation("zip is 95014", turns, client_id="chen_kui")
    coll = {str(x).lower() for x in (t3.get("collected_fields") or [])}
    assert "vin" in coll and "zip" in coll

    turns.append({"role": "customer", "text": "zip is 95014"})
    t4 = triage_conversation("primary driver is my wife", turns, client_id="chen_kui")
    coll4 = {str(x).lower() for x in (t4.get("collected_fields") or [])}
    assert "vin" in coll4 and "zip" in coll4
    assert "primary_driver" in coll4 or "driver" in coll4

    turns.append({"role": "customer", "text": "primary driver is my wife"})
    t5 = triage_conversation("delivery next week", turns, client_id="chen_kui")
    assert t5.get("service_type") == "add_car"
    assert quote_ready_matches_still_needed(
        str(t5.get("quote_ready_status") or ""),
        t5.get("still_needed_fields"),
    )


def test_scenario2_short_replies_stay_add_car_lane():
    """SCENARIO 2 — Short acks do not reset add-car lane."""
    turns = [{"role": "customer", "text": "I want to add a car"}]
    t2 = triage_conversation("ok", turns, client_id="chen_kui")
    assert t2.get("service_type") == "add_car"

    turns.extend(
        [
            {"role": "customer", "text": "ok"},
        ]
    )
    t3 = triage_conversation("VIN later", turns, client_id="chen_kui")
    assert t3.get("service_type") == "add_car"

    turns.append({"role": "customer", "text": "VIN later"})
    t4 = triage_conversation("here is VIN 1HGCM82633A004352", turns, client_id="chen_kui")
    assert t4.get("service_type") == "add_car"
    assert "vin" in {str(x).lower() for x in (t4.get("collected_fields") or [])}


def test_scenario3_multi_vehicle_split():
    """SCENARIO 3 — Second distinct VIN requires new case (append disallowed)."""
    prior = (
        "[客户] I want to add a car\n\n"
        "[系统] Sure — please send VIN when you have it.\n\n"
        "[客户] VIN 1HGCM82633A004352"
    )
    ctx = {
        "formal_submitted_at": "2026-03-01T12:00:00Z",
        "service_record_append": True,
        "vehicle_key": "vin:1HGCM82633A004352",
    }
    out = triage_for_append(
        prior,
        "I also have another car VIN 1HGBH41JXMN109186",
        client_id="chen_kui",
        reply_truth_context=ctx,
    )
    assert out.get("case_boundary_action") == "requires_new_case"
    assert out.get("append_allowed") is False


def test_scenario4_ambiguous_vehicle_requires_confirmation():
    """SCENARIO 4 — Ambiguous reference blocks append."""
    thread = (
        "[客户] 我想加车，2024 Toyota Camry，ZIP 90210，下周提车，我自己开\n\n"
        "[系统] 已记录加车信息，会继续整理。"
    )
    out = triage_for_append(
        thread,
        "same as my other car",
        client_id="chen_kui",
        reply_truth_context={
            "formal_submitted_at": "2026-03-01T12:00:00Z",
            "service_record_append": True,
            "vehicle_key": "vin:1HGCM82633A004352",
        },
    )
    assert out.get("case_boundary_action") == "requires_confirmation"
    assert out.get("append_allowed") is False


def test_scenario5_return_user_zip_with_session(monkeypatch, tmp_path):
    """SCENARIO 5 — Return user with session continues same case."""
    from services.fiqa_api.inbox_triage import session_store as session_store_mod

    cid = "case-ret"
    vin = "1HGCM82633A004352"
    fake_case = {
        "case_id": cid,
        "case_status": "new",
        "workbench_archived": False,
        "formal_submitted_at": "2026-01-02T00:00:00Z",
        "lifecycle_status": "office_followup",
        "vehicle_key": f"vin:{vin}",
        "collected_fields": ["vin"],
        "still_needed_fields": ["zip"],
        "client_id": "chen_kui",
    }
    session_store_mod.patch_session_case_binding("sess-ret", active_case_id=cid)
    monkeypatch.setattr(inbox_triage, "get_case_for_read", lambda _id: fake_case if _id == cid else None)
    monkeypatch.setattr(inbox_triage, "list_recent_cases_for_read", lambda **_: [fake_case])

    out = _run_triage(
        TriageRequest(text="zip is 95014", session_id="sess-ret", client_id="chen_kui")
    )
    _finalize_triage_api_result(out)
    assert out.get("case_id") == cid


def test_scenario6_full_completion_quote_ready_and_handoff():
    """SCENARIO 6 — Full structural slots → quote_ready; V5 defers handoff to post-confirmation turn."""
    msg = (
        "VIN 1HGCM82633A004352 zip 95014 delivery May 15 2026 primary driver is my wife "
        "2021 Toyota Camry"
    )
    r1 = triage_conversation(msg, [], client_id="chen_kui")
    assert r1.get("quote_ready_status") == "quote_ready"
    assert r1.get("handoff_ready") is False
    r2 = triage_conversation(
        "OK",
        [{"role": "customer", "text": msg}],
        client_id="chen_kui",
        prior_workflow_state={
            "conversion_stage": r1.get("conversion_stage"),
            "last_conversion_turn_index": r1.get("last_conversion_turn_index"),
        },
    )
    assert r2.get("quote_ready_status") == "quote_ready"
    assert r2.get("handoff_ready") is True
    assert r2.get("case_lifecycle") == "ready_for_handoff"


# --- PART 3 — Stress ---


def test_stress_50_concurrent_sessions_distinct_vehicle_keys():
    """PART 3 — Concurrent triage calls do not cross-pollute vehicle keys."""

    async def _gather_all():
        async def _one(i: int) -> str | None:
            vin = f"1HGBH41JXMN{i:06d}"
            m = f"VIN {vin} zip {90000 + (i % 999)} delivery June {1 + (i % 28)} 2026 driver is me"
            out = await asyncio.to_thread(triage_conversation, m, [], "chen_kui")
            return out.get("vehicle_key")

        return await asyncio.gather(*(_one(i) for i in range(50)))

    keys = asyncio.run(_gather_all())
    assert len(set(keys)) == len(keys)


# --- PART 4 — Edge cases ---


def _zh_add_car_thread() -> str:
    return (
        "[客户] 我想加车，2024 Toyota Camry，ZIP 90210，下周提车，我自己开\n\n"
        "[系统] 已记录加车信息，会继续整理。"
    )


def test_edge_wrong_correction_routes_new_vehicle():
    """PART 4 — Explicit corrected VIN differs from persisted scope → new case (matches routing matrix)."""
    ctx = {
        "formal_submitted_at": "2026-03-01T12:00:00Z",
        "service_record_append": True,
        "vehicle_key": "vin:1HGCM82633A004352",
    }
    out = triage_for_append(
        _zh_add_car_thread(),
        "更正：VIN 是 1HGBH41JXMN109186",
        client_id="chen_kui",
        reply_truth_context=ctx,
    )
    assert out.get("case_boundary_action") == "requires_new_case"
    assert out.get("append_allowed") is False
    vk = str(out.get("vehicle_key") or "")
    assert "1HGBH41JXMN109186" in vk


def test_edge_no_vin_never_quote_ready():
    """PART 4 — Without VIN, quote_ready_status must not be quote_ready."""
    out = triage_conversation(
        "zip 95014 delivery next week my spouse drives",
        [{"role": "customer", "text": "I want to add a car"}],
        client_id="chen_kui",
    )
    assert out.get("quote_ready_status") != "quote_ready"


def test_edge_rapid_vin_spam_stable():
    """PART 4 — Repeated identical VIN lines stay stable (deduped lists)."""
    vin = "1HGCM82633A004352"
    turns: list[dict] = [{"role": "customer", "text": "add a car"}]
    last = triage_conversation(f"VIN {vin}", turns, client_id="chen_kui")
    turns.append({"role": "customer", "text": f"VIN {vin}"})
    last = triage_conversation(f"VIN {vin} again", turns, client_id="chen_kui")
    turns.append({"role": "customer", "text": f"VIN {vin} again"})
    last = triage_conversation(f"VIN {vin} again", turns, client_id="chen_kui")
    c = [str(x).lower() for x in (last.get("collected_fields") or [])]
    assert c.count("vin") <= 1


# --- IMAGE-FIRST (Auto Evolution V2) ---


def test_scenario_image_vin_only_minimal_followup():
    """OCR yields VIN only → add-car lane + one targeted ask (ZIP), not long V4 confirmation."""
    vin = "1HGCM82633A004352"
    v6 = {
        "structured_fields": {
            "vin": {"value": vin, "confidence": 0.78, "source": "ocr_regex"},
        },
        "last_raw_text": vin,
        "last_engine": "unit_test",
        "attachment_history": [{"attachment_id": "inline_image", "engine": "unit_test", "raw_len": 17}],
    }
    r = triage_conversation("[image intake]", [], client_id="chen_kui", v6_ocr_signals=v6)
    assert r.get("service_type") == "add_car"
    draft = r.get("client_reply_draft") or ""
    dl = draft.lower()
    # VIN-only: next ask is year/make (office record) before ZIP — still a single targeted prompt.
    assert "year" in dl or "make" in dl or "车型" in draft or "zip" in dl or "邮编" in draft
    assert "我先根据" not in draft
    assert "image intake" not in dl
    assert "thanks for the photo" in dl or "收到您发的图片" in draft


def test_scenario_blurry_image_fallback_question():
    """Unreadable inline image → one clarification (no add_car lane until intent or strong OCR/VIN)."""
    v6 = {
        "structured_fields": {},
        "last_raw_text": "",
        "last_engine": "none",
        "attachment_history": [{"attachment_id": "inline_image", "engine": "none", "raw_len": 0}],
    }
    r = triage_conversation("[image intake]", [], client_id="chen_kui", v6_ocr_signals=v6)
    assert r.get("service_type") != "add_car"
    draft = r.get("client_reply_draft") or ""
    dl = draft.lower()
    assert "重拍" in draft or "清晰" in draft or "retake" in dl or "photo" in dl or "readable" in dl
    assert r.get("handoff_ready") is False


def test_scenario_image_plus_short_text_combines():
    """Short typed intent + OCR VIN merges into one add-car turn; VIN collected."""
    vin = "1HGCM82633A004352"
    v6 = {
        "structured_fields": {
            "vin": {"value": vin, "confidence": 0.8, "source": "ocr_regex"},
        },
        "last_raw_text": f"VIN {vin}",
        "last_engine": "unit_test",
        "attachment_history": [{"attachment_id": "inline_image", "engine": "unit_test", "raw_len": 30}],
    }
    r = triage_conversation("add car quote please", [], client_id="chen_kui", v6_ocr_signals=v6)
    assert r.get("service_type") == "add_car"
    assert "vin" in {str(x).lower() for x in (r.get("collected_fields") or [])}


def test_scenario_image_vin_in_raw_ocr_only_no_structured_vin_slim_next_ask():
    """VIN appears in OCR raw text (parser did not emit structured_fields.vin) → truth layer collects VIN, slim next ask, no VIN re-ask."""
    vin = "1HGCM82633A004352"
    v6 = {
        "structured_fields": {
            "zip": {"value": "92602", "confidence": 0.6, "source": "ocr_regex"},
        },
        "last_raw_text": f"VIN {vin}",
        "last_engine": "unit_test",
        "attachment_history": [{"attachment_id": "inline_image", "engine": "unit_test", "raw_len": 30}],
    }
    r = triage_conversation("[image intake]", [], client_id="chen_kui", v6_ocr_signals=v6)
    assert r.get("service_type") == "add_car"
    assert "vin" in {str(x).lower() for x in (r.get("collected_fields") or [])}
    draft = r.get("client_reply_draft") or ""
    dl = draft.lower()
    assert "17位" not in draft and "17-digit" not in dl
    assert "我先根据" not in draft
    assert "image intake" not in dl


def test_scenario_typed_intent_plus_dense_ocr_merges_stronger_collected():
    """Typed year/make in customer text + OCR VIN + structured ZIP merge into one collected set (OCR supplements typed facts)."""
    vin = "1HGCM82633A004352"
    v6 = {
        "structured_fields": {
            "zip": {"value": "92602", "confidence": 0.6, "source": "ocr_regex"},
        },
        "last_raw_text": f"VIN {vin}",
        "last_engine": "unit_test",
        "attachment_history": [{"attachment_id": "inline_image", "engine": "unit_test", "raw_len": 30}],
    }
    r = triage_conversation("add car 2020 Toyota Camry", [], client_id="chen_kui", v6_ocr_signals=v6)
    assert r.get("service_type") == "add_car"
    coll = {str(x).lower() for x in (r.get("collected_fields") or [])}
    assert "vin" in coll and "zip" in coll and "year" in coll and "make_model" in coll


# --- AUTO_EVOLUTION_V2_5 — case_usable acceleration (complex simulations) ---


def test_evolution_v25_scenario_a_image_heavy_min_core_usable():
    """A: OCR VIN + ZIP + vehicle hint; one zh line supplies driver — broker-usable without long ladder."""
    vin = "1HGCM82633A004352"
    v6 = {
        "structured_fields": {
            "zip": {"value": "92602", "confidence": 0.74, "source": "ocr_regex"},
        },
        "last_raw_text": f"VIN {vin} 2021 Toyota Camry",
        "last_engine": "unit_test",
        "attachment_history": [{"attachment_id": "inline_image", "engine": "unit_test", "raw_len": 48}],
    }
    r = triage_conversation(
        "[image intake] 想加车，主要驾驶人是我本人",
        [],
        client_id="chen_kui",
        v6_ocr_signals=v6,
    )
    assert r.get("service_type") == "add_car"
    assert r.get("case_usable") is True
    assert r.get("action_ready") is True
    assert r.get("intake_flow_milestone") == "action_ready"
    draft = r.get("client_reply_draft") or ""
    # Turn 1 action_ready → auto-progress toward quote, not redundant confirm / slot chase.
    assert "我先根据" not in draft
    assert "我已经帮你整理好" in draft or "推进报价" in draft
    assert "提车日期发我" not in draft


def test_evolution_v25_scenario_b_mixed_noisy_two_turns_no_question_loop():
    """B: Weak image then messy text — reach usable in ≤2 customer turns without multi-question churn."""
    v6_weak = {
        "structured_fields": {},
        "last_raw_text": "",
        "last_engine": "none",
        "attachment_history": [{"attachment_id": "inline_image", "engine": "none", "raw_len": 0}],
    }
    t1 = triage_conversation("[image intake]", [], client_id="chen_kui", v6_ocr_signals=v6_weak)
    assert t1.get("service_type") != "add_car"
    messy = (
        "加车啦 VIN 1HGCM82633A004352 那个 z i p 是 90210 吧 "
        "2026年4月25日提车 主驾驶人是我本人"
    )
    t2 = triage_conversation(
        messy,
        [{"role": "customer", "text": "[image intake]"}],
        client_id="chen_kui",
        v6_ocr_signals=None,
    )
    assert t2.get("service_type") == "add_car"
    assert t2.get("case_usable") is True
    assert t2.get("action_ready") is True
    # Single follow-up turn: do not stack many distinct slot questions in one reply.
    draft = (t2.get("client_reply_draft") or "").lower()
    assert draft.count("?") <= 3


def test_evolution_v25_scenario_c_fragmented_partial_reaches_usable_fast():
    """C: VIN + ZIP + noise + partial answers — minimal churn; usable once delivery is explicit."""
    vin = "1HGCM82633A004352"
    t1 = triage_conversation(
        f"加车 随便问问保费 VIN {vin} 对了还有别的事晚点说",
        [],
        client_id="chen_kui",
    )
    assert t1.get("service_type") == "add_car"
    assert t1.get("case_usable") is not True
    turns = [{"role": "customer", "text": f"加车 随便问问保费 VIN {vin} 对了还有别的事晚点说"}]
    t2 = triage_conversation("邮编90210 下周提车 就这样吧", turns, client_id="chen_kui")
    assert "zip" in {str(x).lower() for x in (t2.get("collected_fields") or [])}
    turns.append({"role": "customer", "text": "邮编90210 下周提车 就这样吧"})
    t3 = triage_conversation("主驾驶人是我本人", turns, client_id="chen_kui")
    assert t3.get("case_usable") is True
    assert t3.get("action_ready") is True
    assert t3.get("quote_ready_status") in ("need_more", "almost_ready", "quote_ready")


# --- AUTO_EVOLUTION_V2_6 — action_ready auto-close + conversion-oriented reply ---


def test_evolution_v26_scenario_d_perfect_en_auto_progress_no_question():
    """D: VIN + ZIP + driver in one EN turn → action_ready, no question, auto-progress copy."""
    vin = "1HGCM82633A004352"
    msg = f"Add car — VIN {vin}, ZIP 90210, I'm the primary driver."
    r = triage_conversation(msg, [], client_id="chen_kui")
    assert r.get("service_type") == "add_car"
    assert r.get("action_ready") is True
    assert r.get("intake_flow_milestone") == "action_ready"
    draft = r.get("client_reply_draft") or ""
    assert "?" not in draft
    assert (
        "I've got everything I need to get started" in draft
        or "I've pulled your details together" in draft
    )


def test_evolution_v26_scenario_e_image_partial_plus_driver_no_slot_chase():
    """E: OCR VIN/ZIP + one line for driver (still almost_ready) → action_ready; auto-progress, no slot chase."""
    vin = "1HGCM82633A004352"
    v6 = {
        "structured_fields": {
            "zip": {"value": "92602", "confidence": 0.74, "source": "ocr_regex"},
        },
        "last_raw_text": f"VIN {vin}",
        "last_engine": "unit_test",
        "attachment_history": [{"attachment_id": "inline_image", "engine": "unit_test", "raw_len": 24}],
    }
    r = triage_conversation(
        "[image intake] I am the main driver.",
        [],
        client_id="chen_kui",
        v6_ocr_signals=v6,
    )
    assert r.get("service_type") == "add_car"
    assert r.get("quote_ready_status") == "almost_ready"
    assert r.get("action_ready") is True
    assert r.get("intake_flow_milestone") == "action_ready"
    draft = r.get("client_reply_draft") or ""
    assert "提车日期发我" not in draft
    assert "我先根据" not in draft
    assert (
        "I've got everything I need to get started" in draft
        or "I've pulled your details together" in draft
        or "推进报价" in draft
    )


def test_evolution_v26_scenario_f_noisy_single_turn_still_action_ready():
    """F: Noisy blob but min-core satisfied → proceed, no multi-ask loop."""
    vin = "1HGCM82633A004352"
    blob = (
        f"加车啦乱七八糟 VIN {vin} zip 90210 吧大概 "
        "提车就下周五 主驾驶人本人 别一个个问了"
    )
    r = triage_conversation(blob, [], client_id="chen_kui")
    assert r.get("service_type") == "add_car"
    assert r.get("action_ready") is True
    draft = r.get("client_reply_draft") or ""
    assert draft.count("？") + draft.count("?") <= 1
    assert "我先根据" not in draft
