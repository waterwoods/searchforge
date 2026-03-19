#!/usr/bin/env python3
"""
State/Workflow Backbone — Regression tests

Verifies that triage_conversation and triage_for_append return all workflow state keys
and that handoff/collection semantics are consistent.

Usage: PYTHONPATH=. python3 scripts/test_state_workflow_backbone.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import (
    WORKFLOW_STATE_KEYS,
    triage_conversation,
    triage_for_append,
)


def test_workflow_state_keys_present() -> bool:
    """All triage results must include workflow state keys."""
    cases = [
        ("First turn add-car", "我买了台宝马X5，想问下保费多少钱", []),
        ("Follow-up add-car", "2024年的，zip 90210", [{"role": "customer", "text": "我买了台宝马X5"}, {"role": "system", "text": "先把年份和车型发我"}]),
        ("Missing doc", "UW need dec page. 客户说发过了", []),
        ("Append flow", "garaging 发你了", None),  # append uses triage_for_append
    ]
    ok = True
    for name, text, turns in cases:
        if turns is not None:
            result = triage_conversation(text, turns)
        else:
            result = triage_for_append("[客户] UW need dec page\n\n[系统] 把dec page发我\n\n[客户] 发过了", text)
        missing = [k for k in WORKFLOW_STATE_KEYS if k not in result]
        if missing:
            print(f"  FAIL {name}: missing keys {missing}")
            ok = False
        else:
            print(f"  OK {name}: all workflow state keys present")
    return ok


def test_handoff_semantics() -> bool:
    """handoff_ready and case_creation_suggested consistency."""
    # Turn 1 add-car partial -> not handoff
    r1 = triage_conversation("我买了台宝马X5，想问下保费多少钱", [])
    assert not r1.get("handoff_ready"), "Turn 1 add-car partial should not hand off"
    assert r1.get("collection_stage") == "collecting"

    # Turn 2 add-car zip+delivery -> ask driver (TOP_COMMERCIAL_DEEPENING: capture driver corrections)
    turns = [
        {"role": "customer", "text": "我买了台宝马X5，想问下保费多少钱"},
        {"role": "system", "text": "先把年份和地址邮编发我"},
        {"role": "customer", "text": "2024年的，zip 90210，下周提车"},
    ]
    r2 = triage_conversation("2024年的，zip 90210，下周提车", turns[:2])
    # At T2 with delivery but not driver: ask for driver (LC-AC3 fix)
    assert not r2.get("handoff_ready"), "Turn 2 add-car zip+delivery should ask driver first"
    assert "驾驶人" in (r2.get("client_reply_draft") or ""), "Should ask for driver"

    # Turn 3 add-car with driver -> handoff
    r2b = triage_conversation("我开", turns)
    assert r2b.get("handoff_ready"), "Turn 3 add-car with driver should hand off"
    assert r2b.get("collection_stage") == "enough_for_handoff"

    # Append always handoff_ready
    r3 = triage_for_append("[客户] a\n\n[系统] b", "发你了")
    assert r3.get("handoff_ready"), "Append should always be handoff_ready"

    # Phase 2: lifecycle_status
    assert r1.get("lifecycle_status") == "collecting", "Turn 1 partial should be collecting"
    assert r2.get("lifecycle_status") == "collecting", "Turn 2 zip+delivery asks driver"
    assert r2b.get("lifecycle_status") == "handoff_pending", "Turn 3 with driver should be handoff_pending"
    assert r3.get("lifecycle_status") == "handoff_pending", "Append should be handoff_pending"
    print("  OK handoff semantics consistent")
    return True


def test_terminal_status_guardrail() -> bool:
    """closed is terminal; cannot transition to other status."""
    import os
    import tempfile
    from pathlib import Path

    from services.fiqa_api.inbox_triage.case_store import (
        save_case,
        update_case_status,
    )
    from services.fiqa_api.inbox_triage.triage import triage_message

    with tempfile.TemporaryDirectory(prefix="backbone-test-") as tmp:
        path = Path(tmp) / "cases.json"
        os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
        try:
            r = triage_message("Notice: Policy cancelled. Last notice.")
            r["handoff_ready"] = True
            case = save_case("[客户] Notice: Policy cancelled.", r)
            case_id = case["case_id"]
            update_case_status(case_id, "closed")
            try:
                update_case_status(case_id, "new")
                print("  FAIL: should reject closed→new")
                return False
            except ValueError as e:
                if "terminal" in str(e).lower():
                    print("  OK terminal status guardrail: closed→new rejected")
                    return True
                raise
        finally:
            os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)
    return True


def main() -> int:
    print("State/Workflow Backbone regression tests")
    print("-" * 50)
    ok1 = test_workflow_state_keys_present()
    ok2 = test_handoff_semantics()
    ok3 = test_terminal_status_guardrail()
    print("-" * 50)
    if ok1 and ok2 and ok3:
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
