"""Draft-only Request More wording service.

Plain Python on purpose: one bounded model call, one validation pass, one
deterministic fallback. No routing, no state machine, no persistence — the
broker's existing SaveRequestDraft / SendRequest commands remain the only
writers, and the broker remains the only sender.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Callable
from uuid import uuid4

from services.fiqa_api.inbox_triage.request_more_assistant.contract import (
    AUTHORITY_AI_DRAFT,
    AUTHORITY_TEMPLATE,
    LANGUAGE_ZH,
    NOTHING_MISSING_ZH,
    build_safe_context,
    build_template_draft,
    derive_request_more_missing_items,
)
from services.fiqa_api.inbox_triage.request_more_assistant.edit_signal import (
    build_draft_receipt,
)
from services.fiqa_api.inbox_triage.request_more_assistant.flags import (
    assistant_enabled,
    llm_api_key,
    llm_drafting_enabled,
    llm_max_retries,
    llm_model,
    llm_timeout_seconds,
    office_allowed,
)
from services.fiqa_api.inbox_triage.request_more_assistant.guardrails import (
    OUTCOME_PASSED,
    validate_ai_draft,
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

ERROR_ACTIVE_REQUEST_MORE = "active_request_more_exists"

SYSTEM_PROMPT = (
    "You improve the wording of a Chinese follow-up message that a California auto "
    "insurance broker sends to a customer to collect missing claim intake items. "
    "You are given office_template_draft as the baseline; rewrite it so it reads "
    "naturally, and keep its meaning. "
    "Return ONLY a JSON object: "
    '{"draft_text": string, "items": [{"field_key": string, "label": string, "instructions": string}]}. '
    "draft_text MUST be the complete message the customer receives — an opening line, "
    "a numbered list naming every requested item, and a short closing. Do not stop at "
    "an introduction; the list belongs inside draft_text. "
    "Rules: use exactly the field_key values given, never add or drop an item; "
    "Simplified Chinese, polite and concise, under 200 characters; plain and warm, "
    "not marketing language; never mention coverage, liability, fault, payment, "
    "reimbursement or approval; never state case facts outside the provided context; "
    "never include links, emails, phone numbers or long numbers."
)


def _now_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _call_openai(context: dict[str, Any]) -> dict[str, Any]:
    """Bounded model call. Raises on missing credentials, timeout, invalid JSON."""
    import concurrent.futures

    api_key = llm_api_key()
    if not api_key:
        raise RuntimeError("missing_credentials:request_more_assistant")
    model = llm_model()

    def _invoke() -> dict[str, Any]:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            max_tokens=500,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
        )
        try:
            content = str(resp.choices[0].message.content or "").strip()
        except Exception as exc:  # noqa: BLE001
            raise ValueError("invalid_model_json") from exc
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        try:
            parsed = json.loads(content)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("invalid_model_json") from exc
        if not isinstance(parsed, dict):
            raise ValueError("invalid_model_json")
        parsed["_provider"] = "openai"
        parsed["_model"] = model
        return parsed

    last_exc: Exception | None = None
    for _ in range(max(1, 1 + int(llm_max_retries()))):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(_invoke).result(timeout=float(llm_timeout_seconds()))
        except concurrent.futures.TimeoutError:
            last_exc = TimeoutError("provider_timeout")
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if "missing_credentials" in str(exc).lower() or "auth" in str(exc).lower():
                break
    assert last_exc is not None
    raise last_exc


def _failure_reason(exc: Exception) -> str:
    if isinstance(exc, TimeoutError):
        return "timeout"
    text = str(exc).lower()
    if "missing_credentials" in text:
        return "missing_credentials"
    if "invalid_model_json" in text:
        return "invalid_json"
    return f"provider_error:{type(exc).__name__}"


def draft_request_more(
    *,
    case: dict[str, Any] | None,
    checklist: list[dict[str, Any]] | None,
    case_id: str | None = None,
    office_id: str | None = None,
    open_request_more: Any = None,
    prefer_template: bool = False,
    llm_caller: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Draft customer-facing wording for the deterministic missing set.

    Never writes. Never sends. Returns the office template whenever the model is
    disabled, slow, malformed, or off-contract.
    """
    started = time.monotonic()
    cid = str(case_id or (case or {}).get("case_id") or "").strip() or None

    if open_request_more:
        return {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "case_id": cid,
            "error_code": ERROR_ACTIVE_REQUEST_MORE,
            "message": "已有未完成的补充请求，请先等待客户完成或核对后再起草。",
            "drafting_available": False,
            "lifecycle_mutated": False,
        }

    items = derive_request_more_missing_items(checklist)
    missing_item_count = len(items)

    if missing_item_count == 0:
        return {
            "ok": True,
            "schema_version": SCHEMA_VERSION,
            "case_id": cid,
            "drafting_available": False,
            "missing_item_count": 0,
            "items": [],
            "draft_text": "",
            "message": NOTHING_MISSING_ZH,
            "language": LANGUAGE_ZH,
            "authority": AUTHORITY_TEMPLATE,
            "draft_used_ai": False,
            "used_fallback": False,
            "lifecycle_mutated": False,
        }

    template = build_template_draft(items)
    context = build_safe_context(
        case=case, items=items, office_template_draft=template["draft_text"]
    )

    def _template_result(
        reason: str | None,
        guardrail_outcome: str,
        *,
        used_fallback: bool = True,
    ) -> dict[str, Any]:
        return _result(
            cid=cid,
            draft=template,
            items=items,
            authority=AUTHORITY_TEMPLATE,
            draft_used_ai=False,
            used_fallback=used_fallback,
            fallback_reason=reason,
            guardrail_outcome=guardrail_outcome,
            provider="none",
            model="deterministic_template_v1",
            latency_ms=_now_ms(started),
        )

    if prefer_template:
        # Broker explicitly chose the office template — not an AI failure.
        return _template_result(None, "not_evaluated", used_fallback=False)

    if not assistant_enabled() or not office_allowed(office_id):
        return _template_result("assistant_disabled", "not_evaluated")

    caller = llm_caller
    if caller is None:
        if not llm_drafting_enabled():
            return _template_result("llm_disabled", "not_evaluated")
        caller = _call_openai

    try:
        raw = caller(context)
    except Exception as exc:  # noqa: BLE001
        return _template_result(_failure_reason(exc), "not_evaluated")

    validated, outcome = validate_ai_draft(raw, required_items=items)
    if validated is None or outcome != OUTCOME_PASSED:
        return _template_result("guardrail_rejected", outcome)

    _backfill_blank_instructions(validated, template)
    provider = str((raw or {}).get("_provider") or "openai")[:32]
    model = str((raw or {}).get("_model") or llm_model())[:64]
    return _result(
        cid=cid,
        draft=validated,
        items=items,
        authority=AUTHORITY_AI_DRAFT,
        draft_used_ai=True,
        used_fallback=False,
        fallback_reason=None,
        guardrail_outcome=outcome,
        provider=provider,
        model=model,
        latency_ms=_now_ms(started),
    )


def _backfill_blank_instructions(
    validated: dict[str, Any], template: dict[str, Any]
) -> None:
    """Keep the office "how to find it" hint when the model returns none.

    The customer reads per-item instructions in the H5 task, so an AI draft must
    never be less helpful there than the template it replaced.
    """
    template_by_key = {
        str(item.get("field_key")): str(item.get("instructions") or "")
        for item in template.get("items") or []
    }
    for item in validated.get("items") or []:
        if not str(item.get("instructions") or "").strip():
            item["instructions"] = template_by_key.get(str(item.get("field_key")), "")


def _result(
    *,
    cid: str | None,
    draft: dict[str, Any],
    items: list[dict[str, Any]],
    authority: str,
    draft_used_ai: bool,
    used_fallback: bool,
    fallback_reason: str | None,
    guardrail_outcome: str,
    provider: str,
    model: str,
    latency_ms: int,
) -> dict[str, Any]:
    receipt = build_draft_receipt(
        assist_id=f"assist_{uuid4().hex[:16]}",
        items=draft["items"],
        draft_used_ai=draft_used_ai,
        used_fallback=used_fallback,
        fallback_reason=fallback_reason,
        authority=authority,
        guardrail_outcome=guardrail_outcome,
        model_provider=provider,
        model_name=model,
        missing_item_count=len(items),
    )
    out = {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "case_id": cid,
        "drafting_available": True,
        "missing_item_count": len(items),
        "draft_text": draft["draft_text"],
        "items": draft["items"],
        "language": LANGUAGE_ZH,
        "authority": authority,
        "draft_used_ai": draft_used_ai,
        "used_fallback": used_fallback,
        "fallback_reason": fallback_reason,
        "guardrail_outcome": guardrail_outcome,
        "model_provider": provider,
        "model_name": model,
        "latency_ms": latency_ms,
        "lifecycle_mutated": False,
        # Echoed back on SaveRequestDraft so the send can measure broker edits.
        "ai_draft_receipt": receipt,
    }
    # Bounded metadata only — no case facts, no customer text, no draft body.
    # Rendered into the message because the app formatter drops `extra` fields.
    logger.info(
        "request_more_ai_draft %s",
        json.dumps(
            {
                "case_id_present": bool(cid),
                "assist_id": receipt["assist_id"],
                "missing_item_count": out["missing_item_count"],
                "draft_used_ai": draft_used_ai,
                "used_fallback": used_fallback,
                "fallback_reason": fallback_reason,
                "guardrail_outcome": guardrail_outcome,
                "model_provider": provider,
                "model_name": model,
                "latency_ms": latency_ms,
            },
            sort_keys=True,
        ),
    )
    return out
