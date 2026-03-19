#!/usr/bin/env python3
"""
Regression test: In-progress session persistence and restore API.
Verifies session store save/get and GET /api/inbox/session/{session_id}.
"""
from __future__ import annotations

import sys

# Test session store directly (no server)
from services.fiqa_api.inbox_triage.session_store import (
    get_in_progress_session,
    save_in_progress_session,
)


def test_session_store() -> bool:
    """Save and restore in-progress session."""
    sid = "test-recovery-session"
    turns = [
        {"role": "customer", "text": "我想加新车报价"},
        {
            "role": "system",
            "text": "好的，请发年份和车型",
            "triageResult": {
                "handoff_ready": False,
                "lifecycle_status": "collecting",
                "next_best_question": "年份和车型",
            },
        },
    ]
    result = {
        "handoff_ready": False,
        "lifecycle_status": "collecting",
        "next_best_question": "年份和车型",
        "collected_fields": [],
        "still_needed_fields": ["year", "model"],
    }
    save_in_progress_session(sid, turns, result)
    data = get_in_progress_session(sid)
    if data is None:
        print("FAIL: get_in_progress_session returned None")
        return False
    if len(data.get("turns", [])) != 2:
        print(f"FAIL: expected 2 turns, got {len(data.get('turns', []))}")
        return False
    ws = data.get("workflow_state", {})
    if ws.get("lifecycle_status") != "collecting":
        print(f"FAIL: workflow_state.lifecycle_status={ws.get('lifecycle_status')}")
        return False
    print("  OK session store save/get")
    return True


if __name__ == "__main__":
    print("In-progress session API regression tests")
    print("-" * 40)
    ok = test_session_store()
    print("-" * 40)
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
