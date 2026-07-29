"""Chen Demo — Known-Customer Demo Invite foundation.

Temporary mock_scenario overlay for real WeChat sessions.
Identity SoR remains person_link_key (P29B). No Customers table.
"""

from __future__ import annotations

from services.fiqa_api.inbox_triage.demo_invite.catalog import (
    DEMO_NAME,
    get_approved_scenario,
    is_scenario_allowlisted,
    list_approved_scenarios,
)
from services.fiqa_api.inbox_triage.demo_invite.service import (
    FLAG_ENV,
    assert_demo_invite_allowed,
    demo_invite_enabled,
    issue_demo_invite,
    list_catalog,
    peek_session_overlay,
    redeem_demo_invite,
    reset_office_demo_invites,
    reset_session_overlay,
    resolve_overlay_mock_scenario,
    revoke_demo_invite,
    validate_demo_invite,
)
from services.fiqa_api.inbox_triage.demo_invite.store import reset_demo_invite_store_for_tests

__all__ = [
    "DEMO_NAME",
    "FLAG_ENV",
    "assert_demo_invite_allowed",
    "demo_invite_enabled",
    "get_approved_scenario",
    "is_scenario_allowlisted",
    "issue_demo_invite",
    "list_approved_scenarios",
    "list_catalog",
    "peek_session_overlay",
    "redeem_demo_invite",
    "reset_demo_invite_store_for_tests",
    "reset_office_demo_invites",
    "reset_session_overlay",
    "resolve_overlay_mock_scenario",
    "revoke_demo_invite",
    "validate_demo_invite",
]
