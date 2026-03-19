#!/usr/bin/env python3
"""
Broker Inbox Triage — API test script

Tests POST /api/inbox/triage via HTTP when server is running.
Usage:
  # With server running (restart server to pick up new route):
  curl -X POST http://localhost:8001/api/inbox/triage -H "Content-Type: application/json" -d '{"text": "..."}'

  # Run this script (hits localhost:8001):
  PYTHONPATH=. python3 scripts/test_inbox_triage_api.py
  python3 scripts/test_inbox_triage_api.py --url http://localhost:8001
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

REQUIRED_FIELDS = (
    "issue_category",
    "urgency",
    "broker_next_step",
    "client_prep",
    "client_reply_draft",
    "manual_followup_needed",
)

VALID_CASE_STATUSES = {"new", "reviewing", "waiting_client", "done"}
VALID_WAITING_ON_VALUES = {"none", "client", "broker", "carrier", "underwriting"}
DRAFT_TONE_BLOCKLIST = {"dear ", "best regards", "sincerely", "尊敬的", "期待您的回复"}


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def test_via_http(base_url: str, verbose: bool) -> int:
    """Test API via HTTP. Returns 0 on success, 1 on failure."""
    try:
        import httpx
    except ImportError:
        print("httpx not installed. Use: pip install httpx")
        print("Or test manually: curl -X POST http://localhost:8001/api/inbox/triage -H 'Content-Type: application/json' -d '{\"text\": \"Notice: Policy will be cancelled in 7 days.\"}'")
        return 1

    url = f"{base_url.rstrip('/')}/api/inbox/triage"
    errors = []

    # Test 1: cancellation scenario
    try:
        resp = httpx.post(url, json={"text": "Notice: Policy will be cancelled in 7 days due to non-payment. Last notice."}, timeout=10.0)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        for k in REQUIRED_FIELDS:
            assert k in data, f"Missing field: {k}"
        assert data["issue_category"] == "cancellation_warning"
        assert data["urgency"] == "critical"
        assert data["manual_followup_needed"] is True
        if verbose:
            print("cancellation:", json.dumps(data, indent=2))
        print("PASS: cancellation_warning scenario")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: cancellation_warning:", e)

    # Test 2: empty text -> 400
    try:
        resp = httpx.post(url, json={"text": ""}, timeout=10.0)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("PASS: empty text returns 400")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: empty text:", e)

    # Test 2b: talk_to_agent soft_route -> immediate handoff
    try:
        resp = httpx.post(
            url,
            json={"text": "我想联系陈奎办公室", "soft_route": "talk_to_agent"},
            timeout=10.0,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["issue_category"] == "customer_requested_human", f"Expected customer_requested_human, got {data['issue_category']}"
        assert data["handoff_ready"] is True
        assert "Customer requested human contact" in (data.get("broker_next_step") or "")
        assert "陈奎" in (data.get("client_reply_draft") or "") or "联系" in (data.get("client_reply_draft") or "")
        print("PASS: talk_to_agent soft_route")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: talk_to_agent:", e)

    # Test 2c: talk_to_agent free-text (no soft_route) -> immediate handoff (SALES_READINESS_HARDENING)
    try:
        for text in ("联系人工", "我要找人工", "我想直接跟人说"):
            resp = httpx.post(url, json={"text": text}, timeout=10.0)
            assert resp.status_code == 200, f"Expected 200 for '{text}', got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert data["issue_category"] == "customer_requested_human", f"Expected customer_requested_human for '{text}', got {data['issue_category']}"
            assert data["handoff_ready"] is True
        print("PASS: talk_to_agent free-text detection")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: talk_to_agent free-text:", e)

    # Test 3: informational scenario
    try:
        resp = httpx.post(url, json={"text": "Your proof of insurance has been emailed to the DMV. No further action required."}, timeout=10.0)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["issue_category"] == "informational"
        assert data["urgency"] == "low"
        assert data["manual_followup_needed"] is False
        if verbose:
            print("informational:", json.dumps(data, indent=2))
        print("PASS: informational scenario")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: informational:", e)

    # Test 4: realistic fragmented document chase
    try:
        resp = httpx.post(url, json={"text": "需要驾照 copy 客户说上周寄了"}, timeout=10.0)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["issue_category"] == "missing_document", f"Expected missing_document, got {data['issue_category']}"
        assert data["manual_followup_needed"] is True
        assert len((data.get("client_reply_draft") or "").strip()) > 0, "client_reply_draft must be non-empty for copy"
        if verbose:
            print("realistic fragmented:", json.dumps(data, indent=2))
        print("PASS: realistic fragmented scenario")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: realistic fragmented:", e)

    # Test 5: mixed shorthand document chase
    try:
        resp = httpx.post(
            url,
            json={"text": "UW follow up - need dec page + garaging proof. 客户说上周发过了"},
            timeout=10.0,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["issue_category"] == "missing_document", f"Expected missing_document, got {data['issue_category']}"
        assert data["urgency"] == "medium", f"Expected medium, got {data['urgency']}"
        assert data["manual_followup_needed"] is True
        draft_text = data.get("client_reply_draft") or ""
        draft = draft_text.lower()
        assert _contains_chinese(draft_text), "Expected Chinese draft for mixed-language document chase"
        assert any(phrase in draft for phrase in ("declaration page", "garaging proof")) or "核对" in draft_text
        if verbose:
            print("mixed doc chase:", json.dumps(data, indent=2, ensure_ascii=False))
        print("PASS: mixed shorthand document chase")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: mixed shorthand document chase:", e)

    # Test 6: broken payment / interruption wording
    try:
        resp = httpx.post(
            url,
            json={"text": "AutoPay failed again, please update card to avoid interruption in coverage"},
            timeout=10.0,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["issue_category"] == "payment_lapse_expiration", (
            f"Expected payment_lapse_expiration, got {data['issue_category']}"
        )
        assert data["urgency"] == "high", f"Expected high, got {data['urgency']}"
        assert data["manual_followup_needed"] is True
        assert "payment" in (data.get("client_reply_draft") or "").lower() or "coverage" in (data.get("client_reply_draft") or "").lower()
        if verbose:
            print("broken payment wording:", json.dumps(data, indent=2, ensure_ascii=False))
        print("PASS: broken payment wording")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: broken payment wording:", e)

    # Test 7: mixed-language payment risk question
    try:
        resp = httpx.post(
            url,
            json={"text": "客户问 这个是不是保单要停了? 他说昨天收到账单 overdue"},
            timeout=10.0,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["issue_category"] == "payment_lapse_expiration", (
            f"Expected payment_lapse_expiration, got {data['issue_category']}"
        )
        assert data["urgency"] == "high", f"Expected high, got {data['urgency']}"
        assert data["manual_followup_needed"] is True
        assert _contains_chinese(data.get("client_reply_draft") or ""), "Expected Chinese draft for mixed-language payment risk"
        if verbose:
            print("mixed payment risk:", json.dumps(data, indent=2, ensure_ascii=False))
        print("PASS: mixed-language payment risk question")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: mixed-language payment risk question:", e)

    # Test 8: English notice with Chinese client question should answer in Chinese
    try:
        resp = httpx.post(
            url,
            json={"text": "客户问：这个英文 notice 说 payment failed，我现在怎么办？"},
            timeout=10.0,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["issue_category"] == "payment_lapse_expiration", (
            f"Expected payment_lapse_expiration, got {data['issue_category']}"
        )
        assert data["urgency"] == "high", f"Expected high, got {data['urgency']}"
        assert _contains_chinese(data.get("client_reply_draft") or ""), "Expected Chinese draft for English notice + Chinese question"
        if verbose:
            print("english notice with chinese question:", json.dumps(data, indent=2, ensure_ascii=False))
        print("PASS: English notice with Chinese client question")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: English notice with Chinese client question:", e)

    # Test 9: DMV / suspension help wording should stay broker-natural
    try:
        resp = httpx.post(
            url,
            json={"text": "Need SR-22 filing proof for DMV suspension clearance, what should client bring?"},
            timeout=10.0,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["issue_category"] == "customer_question", f"Expected customer_question, got {data['issue_category']}"
        assert data["urgency"] == "medium", f"Expected medium, got {data['urgency']}"
        assert data["manual_followup_needed"] is True
        draft = (data.get("client_reply_draft") or "").lower()
        assert not any(marker in draft for marker in DRAFT_TONE_BLOCKLIST), f"Draft tone too formal: {draft}"
        if verbose:
            print("dmv suspension help:", json.dumps(data, indent=2, ensure_ascii=False))
        print("PASS: DMV suspension help wording")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: DMV suspension help wording:", e)

    # Test 10: premium-too-high message should no longer fall into unclear
    try:
        resp = httpx.post(
            url,
            json={"text": "客户说这个月保费太高了，能不能看看怎么降一点"},
            timeout=10.0,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["issue_category"] == "customer_question", f"Expected customer_question, got {data['issue_category']}"
        assert data["urgency"] == "medium", f"Expected medium, got {data['urgency']}"
        assert _contains_chinese(data.get("client_reply_draft") or ""), "Expected Chinese draft for premium review case"
        assert "保费" in (data.get("client_reply_draft") or ""), "Expected premium-specific Chinese wording"
        print("PASS: premium-too-high review request")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: premium-too-high review request:", e)

    # Test 11: add-car quote request should ask for concrete vehicle details
    try:
        resp = httpx.post(
            url,
            json={"text": "客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价"},
            timeout=10.0,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["issue_category"] == "customer_question", f"Expected customer_question, got {data['issue_category']}"
        assert data["urgency"] == "medium", f"Expected medium, got {data['urgency']}"
        draft_text = data.get("client_reply_draft") or ""
        assert _contains_chinese(draft_text), "Expected Chinese draft for add-car quote request"
        assert "报价" in draft_text or "VIN" in draft_text or "车型" in draft_text
        print("PASS: add-car quote request")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: add-car quote request:", e)

    # Test 12: persisted case path + recent cases + status update
    # MULTI_TURN_CONTINUITY: Only persist when handoff_ready. Use 2-turn flow for missing_document.
    try:
        # Turn 1: incomplete -> no persist, no case_id
        t1_resp = httpx.post(
            url,
            json={
                "text": "Underwriting requested driver's license copy.",
                "persist_case": True,
            },
            timeout=10.0,
        )
        assert t1_resp.status_code == 200, f"Expected 200, got {t1_resp.status_code}: {t1_resp.text}"
        t1_data = t1_resp.json()
        assert t1_data.get("handoff_ready") is False, "Turn 1 should not hand off (multi-turn)"
        assert "case_id" not in t1_data or not t1_data.get("case_id"), "Turn 1 should not persist case"

        # Turn 2: client says already sent -> handoff, persist
        t2_resp = httpx.post(
            url,
            json={
                "text": "I already sent it last week.",
                "persist_case": True,
                "conversation_turns": [
                    {"role": "customer", "text": "Underwriting requested driver's license copy."},
                    {"role": "system", "text": t1_data.get("client_reply_draft", "Please send the document.")},
                ],
            },
            timeout=10.0,
        )
        assert t2_resp.status_code == 200, f"Expected 200, got {t2_resp.status_code}: {t2_resp.text}"
        data = t2_resp.json()
        for k in REQUIRED_FIELDS:
            assert k in data, f"Missing field on persisted case response: {k}"
        case_id = data.get("case_id")
        assert isinstance(case_id, str) and case_id.strip(), "persisted case should include case_id (after handoff)"
        assert data.get("case_status") == "new", f"expected new case status, got {data.get('case_status')}"
        assert data.get("waiting_on") == "none", f"expected default waiting_on=none, got {data.get('waiting_on')}"
        assert data.get("next_contact_by") == "", "expected next_contact_by to default to empty string"
        assert isinstance(data.get("case_notes"), list), "persisted case should include case_notes list"
        assert isinstance(data.get("case_activity"), list), "persisted case should include case_activity list"
        assert data["case_notes"] == [], "newly saved case should start with no broker notes"
        assert len(data["case_activity"]) >= 1, "newly saved case should include activity trail"
        # Missing document structured intake: collected_fields and still_needed_fields
        assert "collected_fields" in data, "missing_document should include collected_fields"
        assert "still_needed_fields" in data, "missing_document should include still_needed_fields"
        assert len(data.get("collected_fields", [])) > 0, "missing_document should have at least one collected field"
        assert "verify_carrier_received" in (data.get("still_needed_fields") or []), "already-sent case should suggest verify_carrier_received"

        recent_resp = httpx.get(f"{base_url.rstrip('/')}/api/inbox/cases", params={"limit": 5}, timeout=10.0)
        assert recent_resp.status_code == 200, f"Expected 200 from recent cases, got {recent_resp.status_code}: {recent_resp.text}"
        recent_payload = recent_resp.json()
        recent_cases = recent_payload.get("cases", [])
        assert isinstance(recent_cases, list) and recent_cases, "recent cases response should be non-empty"
        matching_case = next((case for case in recent_cases if case.get("case_id") == case_id), None)
        assert matching_case is not None, "saved case should appear in recent cases"

        patch_resp = httpx.patch(
            f"{base_url.rstrip('/')}/api/inbox/cases/{case_id}/status",
            json={"status": "waiting_client"},
            timeout=10.0,
        )
        assert patch_resp.status_code == 200, f"Expected 200 from status update, got {patch_resp.status_code}: {patch_resp.text}"
        patched_case = patch_resp.json()
        assert patched_case.get("case_status") == "waiting_client"
        assert patched_case.get("case_status") in VALID_CASE_STATUSES
        assert patched_case.get("case_activity", [{}])[0].get("activity_type") == "status_changed"

        follow_up_resp = httpx.patch(
            f"{base_url.rstrip('/')}/api/inbox/cases/{case_id}/follow-up",
            json={"waiting_on": "client", "next_contact_by": "2026-03-09"},
            timeout=10.0,
        )
        assert follow_up_resp.status_code == 200, f"Expected 200 from follow-up update, got {follow_up_resp.status_code}: {follow_up_resp.text}"
        follow_up_case = follow_up_resp.json()
        assert follow_up_case.get("waiting_on") == "client"
        assert follow_up_case.get("waiting_on") in VALID_WAITING_ON_VALUES
        assert follow_up_case.get("next_contact_by") == "2026-03-09"
        assert follow_up_case.get("case_activity", [{}])[0].get("activity_type") == "follow_up_updated"

        note_resp = httpx.post(
            f"{base_url.rstrip('/')}/api/inbox/cases/{case_id}/notes",
            json={"note": "Client said they can resend the document tomorrow morning."},
            timeout=10.0,
        )
        assert note_resp.status_code == 200, f"Expected 200 from note create, got {note_resp.status_code}: {note_resp.text}"
        noted_case = note_resp.json()
        assert len(noted_case.get("case_notes", [])) == 1, "saved case should include one broker note"
        assert noted_case["case_notes"][0]["body"] == "Client said they can resend the document tomorrow morning."
        assert noted_case.get("case_activity", [{}])[0].get("activity_type") == "note_added"
        if verbose:
            print("persisted case:", json.dumps(data, indent=2))
            print("patched case:", json.dumps(patched_case, indent=2))
            print("follow-up case:", json.dumps(follow_up_case, indent=2))
            print("noted case:", json.dumps(noted_case, indent=2))
        print("PASS: persisted case flow")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: persisted case flow:", e)

    # Test 13: append follow-up message to existing case
    try:
        create_resp = httpx.post(
            url,
            json={
                "text": "客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价",
                "persist_case": True,
            },
            timeout=10.0,
        )
        assert create_resp.status_code == 200, f"Expected 200, got {create_resp.status_code}: {create_resp.text}"
        created = create_resp.json()
        case_id = created.get("case_id")
        assert case_id, "need case_id for append test"

        append_resp = httpx.post(
            f"{base_url.rstrip('/')}/api/inbox/cases/{case_id}/append-message",
            json={"new_message": "我发了ZIP 90210，下周一提车"},
            timeout=10.0,
        )
        assert append_resp.status_code == 200, f"Expected 200 from append, got {append_resp.status_code}: {append_resp.text}"
        appended = append_resp.json()
        assert appended.get("case_id") == case_id
        assert "[客户]" in (appended.get("source_text") or ""), "source_text should include [客户] labels"
        assert "90210" in (appended.get("source_text") or ""), "source_text should include new message"
        assert appended.get("broker_next_step"), "broker_next_step should be refreshed"
        collected = appended.get("collected_fields") or []
        assert "zip" in [c.lower() for c in collected], f"Expected zip in collected_fields, got {collected}"
        activity_types = [a.get("activity_type") for a in appended.get("case_activity", [])]
        assert "follow_up_added" in activity_types, f"Expected follow_up_added in activity, got {activity_types}"
        if verbose:
            print("appended case:", json.dumps(appended, indent=2, ensure_ascii=False))
        print("PASS: append follow-up message to existing case")
    except Exception as e:
        errors.append(str(e))
        print("FAIL: append follow-up message:", e)

    if errors:
        print(f"\n{len(errors)} test(s) failed. Ensure server is running with the new route: bash scripts/run_demo_local.sh")
        return 1
    print("\nAll API tests passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Test Broker Inbox Triage API")
    ap.add_argument("--url", default="http://localhost:8001", help="Base URL of API server")
    ap.add_argument("--verbose", "-v", action="store_true", help="Print response details")
    args = ap.parse_args()
    return test_via_http(args.url, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
