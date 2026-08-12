"""Did the broker edit the AI draft before sending it?

One product signal, derived from data the broker commands already persist:

    draft_edited_before_send =
        signature(customer-facing fields the broker actually sent)
        != signature recorded when the broker adopted the AI draft

The signature is a SHA-256 digest of normalized wording, never the wording
itself: this metric must not become a second copy of customer communication.
Whitespace and unicode-width differences are normalized away so that reflowing
a textarea does not read as an edit, while any real wording change does.

The signal is only claimed for drafts that actually came from the model. A
deterministic template — chosen by the broker or reached by fallback — reports
``ai_used=False`` and leaves ``draft_edited_before_send`` unset rather than
inflating AI adoption.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

SCHEMA_VERSION = 1

SIGNAL_COMPARED = "compared"
SIGNAL_NO_RECEIPT = "no_ai_draft_receipt"
SIGNAL_AI_NOT_ADOPTED = "ai_not_adopted"

_ZERO_WIDTH = re.compile(r"[\u200b-\u200f\u2028\u2029\ufeff]")
_WHITESPACE = re.compile(r"\s+")


def normalize_customer_text(value: Any) -> str:
    """Normalize customer-facing wording for comparison only.

    NFKC folds full-width punctuation and the ideographic space that Chinese
    input methods emit, so an identical sentence typed on a different keyboard
    is not counted as a broker edit.
    """
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKC", text)
    text = _ZERO_WIDTH.sub("", text)
    return _WHITESPACE.sub(" ", text).strip()


def customer_facing_rows(items: Any) -> list[dict[str, str]]:
    """Deterministic, order-independent view of what the customer will read."""
    rows: list[dict[str, str]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        label = normalize_customer_text(item.get("label"))
        key = normalize_customer_text(item.get("field_key")) or label
        rows.append(
            {
                "key": key,
                "label": label,
                "instructions": normalize_customer_text(item.get("instructions")),
            }
        )
    rows.sort(key=lambda row: (row["key"], row["label"], row["instructions"]))
    return rows


def customer_facing_signature(items: Any) -> str:
    payload = json.dumps(customer_facing_rows(items), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_draft_receipt(
    *,
    assist_id: str,
    items: Any,
    draft_used_ai: bool,
    used_fallback: bool,
    fallback_reason: str | None,
    authority: str,
    guardrail_outcome: str,
    model_provider: str,
    model_name: str,
    missing_item_count: int,
) -> dict[str, Any]:
    """Provenance the broker client echoes back when it saves the draft.

    Carries a digest and bounded metadata only — no draft body, no case facts.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "assist_id": assist_id,
        "draft_signature": customer_facing_signature(items),
        "ai_used": bool(draft_used_ai),
        "used_fallback": bool(used_fallback),
        "fallback_reason": fallback_reason,
        "authority": authority,
        "guardrail_outcome": guardrail_outcome,
        "model_provider": model_provider,
        "model_name": model_name,
        "missing_item_count": int(missing_item_count),
    }


def _clip(value: Any, limit: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text[:limit] if text else None


def normalize_ai_provenance(raw: Any) -> dict[str, Any] | None:
    """Validate a client-echoed receipt into a bounded, storable shape.

    Everything here is metadata the server itself produced at draft time; the
    client only replays it. Unknown keys are dropped so a client can never
    smuggle free text into durable telemetry.
    """
    if not isinstance(raw, dict):
        return None
    signature = _clip(raw.get("draft_signature"), 64)
    if not signature or not re.fullmatch(r"[0-9a-f]{64}", signature):
        return None
    try:
        missing_item_count = max(0, min(int(raw.get("missing_item_count") or 0), 999))
    except (TypeError, ValueError):
        missing_item_count = 0
    return {
        "schema_version": SCHEMA_VERSION,
        "assist_id": _clip(raw.get("assist_id"), 64),
        "draft_signature": signature,
        "ai_used": bool(raw.get("ai_used")),
        "used_fallback": bool(raw.get("used_fallback")),
        "fallback_reason": _clip(raw.get("fallback_reason"), 64),
        "authority": _clip(raw.get("authority"), 32),
        "guardrail_outcome": _clip(raw.get("guardrail_outcome"), 32),
        "model_provider": _clip(raw.get("model_provider"), 32),
        "model_name": _clip(raw.get("model_name"), 64),
        "missing_item_count": missing_item_count,
    }


SIGNAL_EVIDENCE_KEY = "ai_request_more"


def extract_stored_send_signals(events: Any) -> list[dict[str, Any]]:
    """Recover recorded send signals from durable case events.

    Both the Slice 1 and intake send events carry the same payload, so the
    Slice 1 event wins and the intake copy is deduplicated by request_id.
    """
    by_request: dict[str, dict[str, Any]] = {}
    ordered: list[dict[str, Any]] = []
    for event in events or []:
        if not isinstance(event, dict):
            continue
        evidence = event.get("evidence")
        signal = evidence.get(SIGNAL_EVIDENCE_KEY) if isinstance(evidence, dict) else None
        if not isinstance(signal, dict):
            continue
        row = {
            **signal,
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "created_at": event.get("created_at"),
        }
        key = str(signal.get("request_id") or event.get("event_id") or "")
        if key in by_request:
            continue
        by_request[key] = row
        ordered.append(row)
    return ordered


def summarize_send_signals(signals: Any) -> dict[str, Any]:
    """Deterministic counters over recorded sends. Not a real broker metric."""
    rows = [row for row in (signals or []) if isinstance(row, dict)]
    ai_sends = [row for row in rows if row.get("ai_used")]
    edited = [row for row in ai_sends if row.get("draft_edited_before_send") is True]
    unchanged = [row for row in ai_sends if row.get("draft_edited_before_send") is False]
    fallback = [row for row in rows if row.get("used_fallback")]
    return {
        "schema_version": SCHEMA_VERSION,
        "sends_recorded": len(rows),
        "ai_drafts_sent": len(ai_sends),
        "sent_unchanged": len(unchanged),
        "sent_edited": len(edited),
        "fallback_sends": len(fallback),
        "non_ai_sends": len(rows) - len(ai_sends),
        "broker_edit_rate": (round(len(edited) / len(ai_sends), 4) if ai_sends else None),
    }


def evaluate_send_signal(
    *,
    provenance: Any,
    sent_items: Any,
    request_id: str | None = None,
    command_id: str | None = None,
    source_draft_id: str | None = None,
    source_draft_version: int | None = None,
) -> dict[str, Any]:
    """Telemetry recorded on the send event. Pure function, no side effects."""
    sent_rows = customer_facing_rows(sent_items)
    sent_signature = customer_facing_signature(sent_items)
    prov = provenance if isinstance(provenance, dict) else None

    matches: bool | None = None
    if prov is not None:
        matches = prov.get("draft_signature") == sent_signature

    ai_used = bool(prov and prov.get("ai_used"))
    if prov is None:
        signal_reason = SIGNAL_NO_RECEIPT
        edited: bool | None = None
    elif not ai_used:
        signal_reason = SIGNAL_AI_NOT_ADOPTED
        edited = None
    else:
        signal_reason = SIGNAL_COMPARED
        edited = not matches

    return {
        "schema_version": SCHEMA_VERSION,
        "assist_id": (prov or {}).get("assist_id"),
        "ai_used": ai_used,
        "used_fallback": bool(prov and prov.get("used_fallback")),
        "fallback_reason": (prov or {}).get("fallback_reason"),
        "authority": (prov or {}).get("authority"),
        "guardrail_outcome": (prov or {}).get("guardrail_outcome"),
        "model_provider": (prov or {}).get("model_provider"),
        "model_name": (prov or {}).get("model_name"),
        "draft_edited_before_send": edited,
        "edit_comparable": edited is not None,
        "signal_reason": signal_reason,
        "sent_matches_assist_draft": matches,
        "missing_item_count": (prov or {}).get("missing_item_count"),
        "sent_item_count": len(sent_rows),
        "assist_draft_signature": (prov or {}).get("draft_signature"),
        "sent_draft_signature": sent_signature,
        "request_id": _clip(request_id, 128),
        "command_id": _clip(command_id, 128),
        "source_draft_id": _clip(source_draft_id, 128),
        "source_draft_version": source_draft_version,
    }
