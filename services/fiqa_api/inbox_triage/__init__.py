"""
Broker Inbox Triage Assistant — MVP

Takes pasted message text and produces:
- issue_category
- urgency
- broker_next_step
- client_prep
- client_reply_draft
- manual_followup_needed
"""

from services.fiqa_api.inbox_triage.triage import triage_message

__all__ = ["triage_message"]
