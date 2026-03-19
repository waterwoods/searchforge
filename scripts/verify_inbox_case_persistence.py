#!/usr/bin/env python3
"""
Unified Intake lightweight persistence check.

Verifies the local JSON case store can:
- save a triage result
- list the saved case
- update its status
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.case_store import (
    add_case_note,
    append_follow_up_message,
    list_recent_cases,
    save_case,
    update_case_customer,
    update_case_follow_up,
    update_case_status,
)
from services.fiqa_api.inbox_triage.triage import triage_for_append, triage_message


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="unified-intake-case-store-") as tmp_dir:
        store_path = Path(tmp_dir) / "cases.json"
        os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(store_path)

        source_text = "Notice: Policy will be cancelled in 7 days due to non-payment. Last notice."
        triage_result = triage_message(source_text)
        saved_case = save_case(source_text, triage_result)

        assert saved_case["case_status"] == "new"
        assert saved_case["source_text"] == source_text
        assert saved_case["issue_category"] == "cancellation_warning"
        assert saved_case["case_notes"] == []
        assert saved_case["waiting_on"] == "none"
        assert saved_case["next_contact_by"] == ""
        assert len(saved_case["case_activity"]) == 1
        assert saved_case["case_activity"][0]["activity_type"] == "case_created"
        assert saved_case["lifecycle_status"] == "handed_off", "new case should have lifecycle_status=handed_off"
        assert store_path.exists(), "case store file was not created"
        # Message-level history (Lightweight Production Case Record)
        assert "case_messages" in saved_case
        assert len(saved_case["case_messages"]) == 1
        assert saved_case["case_messages"][0]["role"] == "customer"
        assert saved_case["case_messages"][0]["text"] == source_text

        recent_cases = list_recent_cases(limit=5)
        assert len(recent_cases) == 1, f"expected 1 saved case, got {len(recent_cases)}"
        assert recent_cases[0]["case_id"] == saved_case["case_id"]

        updated_case = update_case_status(saved_case["case_id"], "waiting_client")
        assert updated_case is not None, "status update did not return a case"
        assert updated_case["case_status"] == "waiting_client"
        assert updated_case["case_activity"][0]["activity_type"] == "status_changed"

        follow_up_case = update_case_follow_up(saved_case["case_id"], "client", "2026-03-09")
        assert follow_up_case is not None, "follow-up update did not return a case"
        assert follow_up_case["waiting_on"] == "client"
        assert follow_up_case["next_contact_by"] == "2026-03-09"
        assert follow_up_case["case_activity"][0]["activity_type"] == "follow_up_updated"

        noted_case = add_case_note(saved_case["case_id"], "Client said they can resend the document tomorrow morning.")
        assert noted_case is not None, "note save did not return a case"
        assert len(noted_case["case_notes"]) == 1
        assert noted_case["case_notes"][0]["body"] == "Client said they can resend the document tomorrow morning."
        assert noted_case["case_activity"][0]["activity_type"] == "note_added"

        cust_case = update_case_customer(
            saved_case["case_id"],
            customer_name="Zhang Wei",
            customer_phone="+1-555-123-4567",
            policy_number="POL-2024-001",
        )
        assert cust_case is not None
        assert cust_case.get("customer_name") == "Zhang Wei"
        assert cust_case.get("customer_phone") == "+1-555-123-4567"
        assert cust_case.get("policy_number") == "POL-2024-001"

        refreshed_case = list_recent_cases(limit=5)[0]
        assert refreshed_case["case_status"] == "waiting_client"
        assert refreshed_case["lifecycle_status"] == "handed_off", "status update should preserve lifecycle_status"

        # Append follow-up: lifecycle_status should become office_followup (Minimal Production Backbone)
        triage_append = triage_for_append(refreshed_case["source_text"], "客户说材料明天早上重发")
        appended = append_follow_up_message(saved_case["case_id"], "客户说材料明天早上重发", triage_append)
        assert appended is not None
        assert appended["lifecycle_status"] == "office_followup", "append should set lifecycle_status=office_followup"

        refreshed_case = list_recent_cases(limit=5)[0]
        assert refreshed_case["case_status"] == "waiting_client"
        assert refreshed_case["lifecycle_status"] == "office_followup", "append persists lifecycle_status"
        assert refreshed_case["waiting_on"] == "client"
        assert refreshed_case["next_contact_by"] == "2026-03-09"
        assert len(refreshed_case["case_notes"]) == 1
        assert len(refreshed_case["case_activity"]) >= 4
        assert refreshed_case.get("customer_name") == "Zhang Wei"
        assert refreshed_case.get("policy_number") == "POL-2024-001"
        assert refreshed_case["updated_at"] >= refreshed_case["created_at"]

    print("PASS: Unified Intake case persistence + follow-up + note/activity trail")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
