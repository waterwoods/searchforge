import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.routes import inbox_triage
from tests.route_request_stub import minimal_route_request


def test_append_message_blocks_mutation_on_new_issue(monkeypatch):
    case = {
        "case_id": "case_1",
        "source_text": "[客户] 老案子内容",
        "lifecycle_status": "office_followup",
        "client_id": "chen_kui",
    }

    monkeypatch.setattr(inbox_triage, "get_case_for_read", lambda _case_id: case)
    monkeypatch.setattr(
        inbox_triage,
        "triage_for_append",
        lambda **_kwargs: {
            "issue_category": "claim_intake",
            "urgency": "medium",
            "manual_followup_needed": True,
            "client_prep": "N/A",
            "case_boundary": "new_issue",
            "case_boundary_action": "requires_new_case",
            "boundary_reason": "Detected clear matter separation from current case.",
            "broker_next_step": "Case boundary: possible new issue in the same thread—confirm whether to split.",
            "client_reply_draft": "这是新事项，请新开服务记录。",
            "conversation_summary": "Boundary: new_issue",
            "service_type": "claim_intake",
            "vehicle_key": None,
            "collected_fields": [],
            "still_needed_fields": [],
            "handoff_ready": True,
            "triage_mode": "append",
        },
    )

    def _should_not_call_append(*_args, **_kwargs):
        raise AssertionError("append_follow_up_message must not be called on new_issue boundary")

    monkeypatch.setattr(inbox_triage, "append_follow_up_message", _should_not_call_append)

    body = asyncio.run(
        inbox_triage.append_case_message(
            "case_1",
            inbox_triage.AppendMessageRequest(new_message="我还有一个理赔新问题"),
            minimal_route_request(),
        )
    )
    assert body["append_blocked_new_issue"] is True
    assert body["case_boundary_action"] == "requires_new_case"
    assert body["case_boundary"] == "new_issue"
    assert body["boundary_reason"] == "Detected clear matter separation from current case."
    assert body["service_type"] == "claim_intake"
    assert body["vehicle_key"] is None
    assert body["old_case_mutated"] is False
    assert body["case_id"] == "case_1"
    assert body.get("triage_mode") == "append"
    assert body.get("handoff_ready") is False
    assert body.get("assist") is not None


def test_append_message_borderline_still_updates(monkeypatch):
    """Borderline signals requires_confirmation but does not block mutation (append API)."""
    case = {
        "case_id": "case_bl",
        "source_text": "[客户] 加车线程",
        "lifecycle_status": "office_followup",
        "client_id": "chen_kui",
    }
    appended = {
        "case_id": "case_bl",
        "case_boundary": "borderline",
        "case_boundary_action": "requires_confirmation",
    }

    monkeypatch.setattr(inbox_triage, "get_case_for_read", lambda _case_id: case)
    monkeypatch.setattr(
        inbox_triage,
        "triage_for_append",
        lambda **_kwargs: {
            "case_boundary": "borderline",
            "case_boundary_action": "requires_confirmation",
            "client_reply_draft": "收到。",
        },
    )
    monkeypatch.setattr(inbox_triage, "append_follow_up_message", lambda **_kwargs: appended)

    body = asyncio.run(
        inbox_triage.append_case_message(
            "case_bl",
            inbox_triage.AppendMessageRequest(new_message="顺便问下办公室收到没？"),
            minimal_route_request(),
        )
    )
    assert body.get("append_blocked_new_issue") is None
    assert body["case_boundary"] == "borderline"


def test_append_message_same_case_still_updates(monkeypatch):
    case = {
        "case_id": "case_2",
        "source_text": "[客户] 这是同一件加车",
        "lifecycle_status": "office_followup",
        "client_id": "chen_kui",
    }
    appended_case = {
        "case_id": "case_2",
        "source_text": "[客户] 这是同一件加车\n\n[客户] 我补充了ZIP 90210",
        "case_boundary": "same_case",
    }

    monkeypatch.setattr(inbox_triage, "get_case_for_read", lambda _case_id: case)
    monkeypatch.setattr(
        inbox_triage,
        "triage_for_append",
        lambda **_kwargs: {"case_boundary": "same_case", "client_reply_draft": "收到，继续同案跟进。"},
    )
    monkeypatch.setattr(inbox_triage, "append_follow_up_message", lambda **_kwargs: appended_case)

    body = asyncio.run(
        inbox_triage.append_case_message(
            "case_2",
            inbox_triage.AppendMessageRequest(new_message="我补充了ZIP 90210"),
            minimal_route_request(),
        )
    )
    assert body["case_id"] == "case_2"
    assert body.get("append_blocked_new_issue") is None
    assert "source_text" in body
