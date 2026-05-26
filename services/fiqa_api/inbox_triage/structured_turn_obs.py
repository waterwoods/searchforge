"""
Structured per-turn observability for Unified Intake (no resolver / triage logic).

Emits newline-delimited JSON to stderr when INBOX_STRUCTURED_TURN_OBS=1 (recommended in staging/prod).

Events:
  triage_turn_obs — one line per HTTP triage completion
  pg_truth_turn   — optional second line when Postgres vehicle identity exists and can be checked
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

from services.fiqa_api.db.service_record_settings import service_record_database_url
from services.fiqa_api.inbox_triage.entity_repository import get_active_vehicle
from services.fiqa_api.inbox_triage.triage import (
    _entity_payload_has_vehicle_identity,
    _primary_vehicle_summary_from_entity_payload,
    _vehicle_key_from_entity_payload,
)


def inbox_structured_obs_enabled() -> bool:
    raw = (os.environ.get("INBOX_STRUCTURED_TURN_OBS") or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    return False


def _emit_line(payload: dict[str, Any]) -> None:
    try:
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr, flush=True)
    except Exception:
        # Observability must not break responses
        return


def resolver_action_label(result: dict[str, Any]) -> str:
    """Stable string for logs: routing path + optional clarify marker (read-only)."""
    tp = str(result.get("triage_path") or "").strip()
    if result.get("active_vehicle_clarify_prompt"):
        return f"{tp or 'unknown'}|clarify_prompt" if tp else "clarify_prompt"
    return tp or ""


def emit_inbox_turn_structured_logs(
    result: dict[str, Any],
    *,
    session_id: str | None,
    route_total_latency_ms: float,
) -> None:
    """
    Emit triage_turn_obs always when enabled; pg_truth_turn when DB + comparable identity rows exist.

    latency_ms is end-to-end route wall time (measurable per HTTP turn).
    """
    if not inbox_structured_obs_enabled():
        return

    sid = (session_id or "").strip()
    clarify_triggered = bool(result.get("active_vehicle_clarify_prompt"))
    triage_turn_obs = {
        "event": "triage_turn_obs",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "resolver_action": resolver_action_label(result),
        "active_vehicle_id": "",
        "pg_truth_match": True,
        "clarify_triggered": clarify_triggered,
        "latency_ms": round(float(route_total_latency_ms), 2),
        "session_id": sid[:80] if sid else "",
        "issue_category": str(result.get("issue_category") or "")[:120],
        "triage_path": str(result.get("triage_path") or ""),
    }

    pg_truth_turn: dict[str, Any] | None = None
    has_db = bool(service_record_database_url())
    active_vehicle_id = ""
    if has_db and sid:
        av = get_active_vehicle(sid)
        if isinstance(av, dict):
            active_vehicle_id = str(av.get("entity_id") or "").strip()
        triage_turn_obs["active_vehicle_id"] = active_vehicle_id

        if av and isinstance(av, dict):
            pl = av.get("payload")
            pld = pl if isinstance(pl, dict) else {}
            exp_vk = (_vehicle_key_from_entity_payload(pld) or "").strip()
            exp_sum = (_primary_vehicle_summary_from_entity_payload(pld) or "").strip()
            act_vk = str(result.get("vehicle_key") or "").strip()
            act_sum = str(result.get("primary_vehicle_summary") or "").strip()

            pg_match = True
            if _entity_payload_has_vehicle_identity(pld):
                pg_match = exp_vk == act_vk
                pg_truth_turn = {
                    "event": "pg_truth_turn",
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "resolver_action": resolver_action_label(result),
                    "active_vehicle_id": active_vehicle_id,
                    "pg_truth_match": pg_match,
                    "clarify_triggered": clarify_triggered,
                    "latency_ms": round(float(route_total_latency_ms), 2),
                    "session_id": sid[:80] if sid else "",
                }
                if not pg_match:
                    pg_truth_turn["detail"] = {
                        "exp_vk_preview": exp_vk[:80],
                        "act_vk_preview": act_vk[:80],
                        "summary_case_insensitive_match": exp_sum.lower() == act_sum.lower(),
                    }
                triage_turn_obs["pg_truth_match"] = pg_match

    _emit_line(triage_turn_obs)
    if pg_truth_turn is not None:
        _emit_line(pg_truth_turn)
