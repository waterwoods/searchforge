"""Server-side flags / kill switches for AI Request More drafting.

Defaults are safe for restricted pilot:
- Drafting helper ON but instantly killable
- LLM OFF (office template only) until explicitly enabled
- Deterministic template fallback can never be disabled

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
    """Master kill switch. When False the broker still gets the office template."""
    return _truthy("REQUEST_MORE_ASSISTANT_ENABLED", default=True)


def llm_drafting_enabled() -> bool:
    """Optional LLM wording. Default OFF — deterministic template only."""
    return _truthy("REQUEST_MORE_ASSISTANT_LLM", default=False)


def deterministic_fallback_enabled() -> bool:
    """Always treated as enabled — safety contract forbids disabling fallback."""
    return True


def office_allowlist() -> frozenset[str]:
    raw = (os.getenv("REQUEST_MORE_ASSISTANT_OFFICE_ALLOWLIST") or "").strip()
    if not raw:
        return frozenset()
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


def office_allowed(office_id: str | None) -> bool:
    allowed = office_allowlist()
    if not allowed:
        return True
    oid = str(office_id or "").strip()
    return bool(oid) and oid in allowed


def llm_timeout_seconds() -> float:
    try:
        return max(0.5, min(float(os.getenv("REQUEST_MORE_ASSISTANT_TIMEOUT_SECONDS") or "8"), 30.0))
    except Exception:
        return 8.0


def llm_max_retries() -> int:
    try:
        return max(0, min(int(os.getenv("REQUEST_MORE_ASSISTANT_MAX_RETRIES") or "1"), 2))
    except Exception:
        return 1


def llm_model() -> str:
    return (
        os.getenv("REQUEST_MORE_ASSISTANT_MODEL")
        or os.getenv("OPENAI_MODEL")
        or "gpt-4o-mini"
    ).strip()


def llm_api_key() -> str:
    return (
        os.getenv("REQUEST_MORE_ASSISTANT_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    ).strip()


def request_more_assistant_flags_public() -> dict[str, Any]:
    """Non-secret posture for support diagnostics / deployment manifest."""
    return {
        "assistant_enabled": assistant_enabled(),
        "llm_drafting_enabled": llm_drafting_enabled(),
        "llm_credentials_configured": bool(llm_api_key()),
        "deterministic_fallback_enabled": deterministic_fallback_enabled(),
        "office_allowlist_configured": bool(office_allowlist()),
        "office_allowlist_count": len(office_allowlist()),
        "llm_timeout_seconds": llm_timeout_seconds(),
        "llm_max_retries": llm_max_retries(),
        "emergency_disable_env": "REQUEST_MORE_ASSISTANT_LLM=0",
    }
