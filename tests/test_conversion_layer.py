"""Quote-ready conversion layer: progression, intent routing, workflow fields."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.inbox_triage.triage import triage_conversation

_FULL_ADD_CAR_ZH = (
    "我想加车。VIN 1HGCM82633A004352 zip 95014 delivery May 15 2026 primary driver is my wife "
    "2021 Toyota Camry"
)


def test_first_quote_ready_moment_compact_no_all_complete_wording():
    """V5: turn 1 = case confirmation; conversion runs after handoff (turn 2+)."""
    r = triage_conversation(_FULL_ADD_CAR_ZH, [], client_id="chen_kui")
    assert r.get("quote_ready_status") == "quote_ready"
    assert r.get("handoff_ready") is False
    assert r.get("conversion_layer_active") is not True
    draft = str(r.get("client_reply_draft") or "")
    assert "信息已经齐全" not in draft
    # Turn-1: either compact confirmation (整理 / look right) or short identity ask when name/phone still needed.
    assert (
        "整理" in draft
        or "look right" in draft.lower()
        or "姓名" in draft
    )
    nb = str(r.get("next_best_question") or "").strip()
    assert not nb or "整理" in nb or "look right" in nb.lower() or "姓名" in nb


def test_timeline_followup_no_full_block_repeat():
    r1 = triage_conversation(_FULL_ADD_CAR_ZH, [], client_id="chen_kui")
    assert r1.get("conversion_layer_active") is not True
    r2 = triage_conversation(
        "好",
        [{"role": "customer", "text": _FULL_ADD_CAR_ZH}],
        client_id="chen_kui",
        prior_workflow_state={
            "conversion_stage": r1.get("conversion_stage"),
            "last_conversion_turn_index": r1.get("last_conversion_turn_index"),
        },
    )
    assert r2.get("conversion_layer_active") is True
    full = str(r2.get("client_reply_draft") or "")
    r3 = triage_conversation(
        "多久能出报价？",
        [
            {"role": "customer", "text": _FULL_ADD_CAR_ZH},
            {"role": "customer", "text": "好"},
        ],
        client_id="chen_kui",
        prior_workflow_state={
            "conversion_stage": r2.get("conversion_stage"),
            "last_conversion_turn_index": r2.get("last_conversion_turn_index"),
        },
    )
    assert r3.get("post_quote_followup_intent") == "timeline_question"
    d3 = str(r3.get("client_reply_draft") or "")
    assert d3 != full
    assert "我们只会用这些信息来帮你做报价" not in d3
    assert "几分钟" in d3 or "minute" in d3.lower()


def test_short_acknowledgement_followup():
    r1 = triage_conversation(_FULL_ADD_CAR_ZH, [], client_id="chen_kui")
    r2 = triage_conversation(
        "好的",
        [{"role": "customer", "text": _FULL_ADD_CAR_ZH}],
        client_id="chen_kui",
        prior_workflow_state={
            "conversion_stage": r1.get("conversion_stage"),
            "last_conversion_turn_index": r1.get("last_conversion_turn_index"),
        },
    )
    full = str(r2.get("client_reply_draft") or "")
    r3 = triage_conversation(
        "好的",
        [
            {"role": "customer", "text": _FULL_ADD_CAR_ZH},
            {"role": "customer", "text": "好的"},
        ],
        client_id="chen_kui",
        prior_workflow_state={
            "conversion_stage": r2.get("conversion_stage"),
            "last_conversion_turn_index": r2.get("last_conversion_turn_index"),
        },
    )
    assert r3.get("post_quote_followup_intent") == "confirmation"
    d3 = str(r3.get("client_reply_draft") or "")
    assert len(d3) < len(full)
    assert "开始报价了 👍" not in d3


def test_single_token_hao_is_confirmation_not_silence():
    r1 = triage_conversation(_FULL_ADD_CAR_ZH, [], client_id="chen_kui")
    r2 = triage_conversation(
        "好",
        [{"role": "customer", "text": _FULL_ADD_CAR_ZH}],
        client_id="chen_kui",
        prior_workflow_state={
            "conversion_stage": r1.get("conversion_stage"),
            "last_conversion_turn_index": r1.get("last_conversion_turn_index"),
        },
    )
    r3 = triage_conversation(
        "好",
        [
            {"role": "customer", "text": _FULL_ADD_CAR_ZH},
            {"role": "customer", "text": "好"},
        ],
        client_id="chen_kui",
        prior_workflow_state={
            "conversion_stage": r2.get("conversion_stage"),
            "last_conversion_turn_index": r2.get("last_conversion_turn_index"),
        },
    )
    assert r3.get("post_quote_followup_intent") == "confirmation"


def test_deferral_maps_to_defer_ack_not_unrelated():
    r1 = triage_conversation(_FULL_ADD_CAR_ZH, [], client_id="chen_kui")
    r2 = triage_conversation(
        "好",
        [{"role": "customer", "text": _FULL_ADD_CAR_ZH}],
        client_id="chen_kui",
        prior_workflow_state={
            "conversion_stage": r1.get("conversion_stage"),
            "last_conversion_turn_index": r1.get("last_conversion_turn_index"),
        },
    )
    r3 = triage_conversation(
        "等等再说",
        [
            {"role": "customer", "text": _FULL_ADD_CAR_ZH},
            {"role": "customer", "text": "好"},
        ],
        client_id="chen_kui",
        prior_workflow_state={
            "conversion_stage": r2.get("conversion_stage"),
            "last_conversion_turn_index": r2.get("last_conversion_turn_index"),
        },
    )
    assert r3.get("post_quote_followup_intent") == "defer_ack"
    d3 = str(r3.get("client_reply_draft") or "")
    assert "有空随时发我" in d3 or "whenever works" in d3.lower()


def test_multiple_followups_do_not_repeat_identical():
    r1 = triage_conversation(_FULL_ADD_CAR_ZH, [], client_id="chen_kui")
    r2 = triage_conversation(
        "好",
        [{"role": "customer", "text": _FULL_ADD_CAR_ZH}],
        client_id="chen_kui",
        prior_workflow_state={
            "conversion_stage": r1.get("conversion_stage"),
            "last_conversion_turn_index": r1.get("last_conversion_turn_index"),
        },
    )
    pw2 = {
        "conversion_stage": r2.get("conversion_stage"),
        "last_conversion_turn_index": r2.get("last_conversion_turn_index"),
    }
    r3 = triage_conversation(
        "多久能出？",
        [
            {"role": "customer", "text": _FULL_ADD_CAR_ZH},
            {"role": "customer", "text": "好"},
        ],
        client_id="chen_kui",
        prior_workflow_state=pw2,
    )
    r4 = triage_conversation(
        "谢谢",
        [
            {"role": "customer", "text": _FULL_ADD_CAR_ZH},
            {"role": "customer", "text": "好"},
            {"role": "customer", "text": "多久能出？"},
        ],
        client_id="chen_kui",
        prior_workflow_state={
            "conversion_stage": r3.get("conversion_stage"),
            "last_conversion_turn_index": r3.get("last_conversion_turn_index"),
        },
    )
    assert str(r3.get("client_reply_draft") or "").strip() != str(r4.get("client_reply_draft") or "").strip()


def test_quote_ready_with_missing_contact_uses_soft_block_not_all_complete_zh():
    """After V5 confirm (turn 2), conversion asks for contact without 资料齐全 tone."""
    r1 = triage_conversation(_FULL_ADD_CAR_ZH, [], client_id="chen_kui")
    assert r1.get("quote_ready_status") == "quote_ready"
    assert r1.get("handoff_ready") is False
    r2 = triage_conversation(
        "好",
        [{"role": "customer", "text": _FULL_ADD_CAR_ZH}],
        client_id="chen_kui",
        prior_workflow_state={
            "conversion_stage": r1.get("conversion_stage"),
            "last_conversion_turn_index": r1.get("last_conversion_turn_index"),
        },
    )
    assert r2.get("quote_ready_status") == "quote_ready"
    assert r2.get("handoff_ready") is True
    still = [str(x).lower() for x in (r2.get("still_needed_fields") or [])]
    assert "name" in still or "phone" in still
    draft = str(r2.get("client_reply_draft") or "")
    assert r2.get("conversion_layer_active") is True
    assert "资料齐全" not in draft
    assert "手机" in draft or "电话" in draft or "mobile" in draft.lower()


def test_conversion_does_not_change_quote_gates():
    out = triage_conversation(
        "zip 95014 delivery next week my spouse drives",
        [{"role": "customer", "text": "I want to add a car"}],
        client_id="chen_kui",
    )
    assert out.get("quote_ready_status") != "quote_ready"
    assert out.get("conversion_layer_active") is not True
