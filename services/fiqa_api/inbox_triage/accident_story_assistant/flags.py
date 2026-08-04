"""Server-side feature flags / kill switches for Accident Story Assistant.

Defaults are safe for restricted pilot:
- Assistant ON (guided path remains available) but can be killed instantly
- LLM OFF (deterministic extraction only)
- Tracing OFF unless LangSmith key present AND explicit flag allows it
- Deterministic fallback always ON (cannot invent facts when AI fails)
- Optional office allowlist (empty = all offices in non-Production)

Never trust client flags. Never expose secrets in diagnostics.
"""

from __future__ import annotations

import os
from typing import Any


def _truthy(name: str, *, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return default


def assistant_enabled() -> bool:
    """Master kill switch. When False, propose returns manual-intake fallback."""
    return _truthy("ACCIDENT_STORY_ASSISTANT_ENABLED", default=True)


def llm_extraction_enabled() -> bool:
    """Optional LLM merge. Default OFF — deterministic rules only."""
    return _truthy("ACCIDENT_STORY_LLM", default=False)


def langsmith_tracing_enabled() -> bool:
    """Explicit accident-story tracing gate (AND LangSmith package/key)."""
    # Default True when key exists so existing lab tracing keeps working;
    # set ACCIDENT_STORY_LANGSMITH_TRACING=0 to kill traces without removing key.
    return _truthy("ACCIDENT_STORY_LANGSMITH_TRACING", default=True)


def langsmith_pilot_project() -> str:
    """Optional clean project for restricted-pilot traces (QA only).

    When set, accident-story @maybe_traceable runs target this project instead of
    the shared lab project. Empty = inherit LANGSMITH_PROJECT / LANGCHAIN_PROJECT.
    """
    return (
        os.getenv("ACCIDENT_STORY_LANGSMITH_PROJECT")
        or os.getenv("ACCIDENT_STORY_LANGSMITH_PILOT_PROJECT")
        or ""
    ).strip()


def deterministic_fallback_enabled() -> bool:
    """Always treat as enabled — safety contract forbids disabling fallback."""
    return True


def office_allowlist() -> frozenset[str]:
    """Comma-separated office ids. Empty = unrestricted (non-Production)."""
    raw = (os.getenv("ACCIDENT_STORY_OFFICE_ALLOWLIST") or "").strip()
    if not raw:
        return frozenset()
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


def office_allowed(office_id: str | None) -> bool:
    allowed = office_allowlist()
    if not allowed:
        return True
    oid = str(office_id or "").strip()
    return bool(oid) and oid in allowed


def max_story_chars() -> int:
    try:
        return max(200, min(int(os.getenv("ACCIDENT_STORY_MAX_STORY_CHARS") or "2000"), 8000))
    except Exception:
        return 2000


def max_followup_questions() -> int:
    return 3


def llm_timeout_seconds() -> float:
    try:
        return max(0.5, min(float(os.getenv("ACCIDENT_STORY_LLM_TIMEOUT_SECONDS") or "8"), 30.0))
    except Exception:
        return 8.0


def llm_max_retries() -> int:
    try:
        return max(0, min(int(os.getenv("ACCIDENT_STORY_LLM_MAX_RETRIES") or "1"), 2))
    except Exception:
        return 1


def max_payload_bytes() -> int:
    try:
        return max(4096, min(int(os.getenv("ACCIDENT_STORY_MAX_PAYLOAD_BYTES") or "32768"), 131072))
    except Exception:
        return 32768


CUSTOMER_MSG_FALLBACK_ZH = "AI暂时无法整理这段描述，请继续填写事故信息。不影响提交。"
CUSTOMER_MSG_DISABLED_ZH = "当前请直接填写事故信息。不影响提交。"
CUSTOMER_MSG_TIMEOUT_ZH = "整理稍慢，请继续填写事故信息。不影响提交。"
CUSTOMER_MSG_CONFLICT_ZH = "部分信息需要您确认，请继续填写。"


def customer_message_for_category(category: str) -> str:
    cat = str(category or "").strip().lower()
    if cat in ("timeout", "provider_timeout"):
        return CUSTOMER_MSG_TIMEOUT_ZH
    if cat in ("disabled", "office_not_allowlisted"):
        return CUSTOMER_MSG_DISABLED_ZH
    if cat in ("conflict", "conflicting_facts"):
        return CUSTOMER_MSG_CONFLICT_ZH
    return CUSTOMER_MSG_FALLBACK_ZH


def accident_story_flags_public() -> dict[str, Any]:
    """Non-secret posture for support diagnostics / deployment-manifest."""
    from services.fiqa_api.observability.langsmith_tracing import tracing_enabled

    key_present = bool(
        (os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY") or "").strip()
    )
    pilot_project = langsmith_pilot_project()
    return {
        "assistant_enabled": assistant_enabled(),
        "llm_extraction_enabled": llm_extraction_enabled(),
        "langsmith_tracing_flag": langsmith_tracing_enabled(),
        "langsmith_key_configured": key_present,
        "langsmith_tracing_active": bool(
            langsmith_tracing_enabled() and tracing_enabled() and key_present
        ),
        "langsmith_pilot_project_configured": bool(pilot_project),
        "langsmith_pilot_project_name_len": len(pilot_project),
        "deterministic_fallback_enabled": deterministic_fallback_enabled(),
        "office_allowlist_configured": bool(office_allowlist()),
        "office_allowlist_count": len(office_allowlist()),
        "max_story_chars": max_story_chars(),
        "max_followup_questions": max_followup_questions(),
        "llm_timeout_seconds": llm_timeout_seconds(),
        "llm_max_retries": llm_max_retries(),
        "max_payload_bytes": max_payload_bytes(),
        "emergency_disable_env": "ACCIDENT_STORY_ASSISTANT_ENABLED=0",
    }
