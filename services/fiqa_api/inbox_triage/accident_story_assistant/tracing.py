"""Accident-story LangSmith helpers — redaction + stable metadata (QA/lab).

Never send raw story text, phones, OpenIDs, resume tokens, or photo paths.
Tracing is optional: no API key → local no-op via maybe_traceable.
"""

from __future__ import annotations

import hashlib
import re
import time
from typing import Any

from services.fiqa_api.inbox_triage.accident_story_assistant.contract import SCHEMA_VERSION

ASSISTANT_ID = "accident_story_langgraph_v1"
PROPOSAL_VERSION = "v1"

# Stable metadata keys allowed on root / node traces.
META_ALLOWLIST: frozenset[str] = frozenset(
    {
        "assistant",
        "schema_version",
        "proposal_version",
        "used_fallback",
        "fallback_reason_category",
        "fallback_reason_code",
        "question_count",
        "missing_count",
        "missing_keys",
        "conflict_keys",
        "injury_status",
        "model_provider",
        "model_name",
        "command_id_prefix",
        "scenario",
        "latency_ms",
        "story_char_len",
        "story_lang_hint",
        "node",
        "ok",
        "has_time_text",
        "has_location_text",
        "vehicle_count",
        "warning_count",
        "case_id_hash_prefix",
    }
)

_FALLBACK_CATEGORIES: tuple[tuple[str, str], ...] = (
    ("timeout", "timeout"),
    ("llm_failed", "llm_failed"),
    ("invalid_model", "invalid_model_json"),
    ("invalid_injury", "invalid_injury_status"),
    ("graph_runtime", "graph_runtime"),
    ("hallucinated", "hallucinated"),
)


def command_id_prefix(command_id: str | None) -> str:
    raw = str(command_id or "").strip()
    if not raw:
        return ""
    return raw[:12]


def story_lang_hint(text: str) -> str:
    t = str(text or "")
    has_cjk = bool(re.search(r"[\u4e00-\u9fff]", t))
    has_latin = bool(re.search(r"[A-Za-z]", t))
    if has_cjk and has_latin:
        return "mixed_zh_en"
    if has_cjk:
        return "zh"
    if has_latin:
        return "en"
    return "unknown"


def fallback_reason_category(reason: str | None) -> str:
    raw = str(reason or "").strip().lower()
    if not raw:
        return "none"
    for cat, needle in _FALLBACK_CATEGORIES:
        if needle in raw:
            return cat
    if raw.startswith("llm_failed:"):
        return "llm_failed"
    return "other"


def case_id_hash_prefix(case_id: str | None) -> str:
    raw = str(case_id or "").strip()
    if not raw:
        return ""
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return digest[:12]


def redact_text_blob(text: str | None) -> dict[str, Any]:
    """Replace story content with length + language hint only."""
    raw = str(text or "")
    return {
        "story_char_len": len(raw),
        "story_lang_hint": story_lang_hint(raw),
    }


def redact_state_for_trace(state: dict[str, Any] | None) -> dict[str, Any]:
    """Safe node I/O for LangSmith — no raw story / summary prose."""
    s = state if isinstance(state, dict) else {}
    missing = [str(x) for x in (s.get("missing_required_facts") or []) if str(x).strip()]
    questions = list(s.get("followup_questions") or [])
    conflicts = [str(x) for x in (s.get("conflicts") or []) if str(x).strip()]
    warnings = list(s.get("warnings") or [])
    story = str(s.get("normalized_story") or s.get("raw_story") or "")
    out: dict[str, Any] = {
        "schema_version": int(s.get("schema_version") or SCHEMA_VERSION),
        "injury_status": str(s.get("injury_status") or "unknown"),
        "has_time_text": bool(str(s.get("accident_time_text") or "").strip()),
        "has_location_text": bool(str(s.get("accident_location_text") or "").strip()),
        "vehicle_count": len(list(s.get("involved_vehicles") or [])),
        "missing_count": len(missing),
        "missing_keys": missing[:8],
        "question_count": len(questions),
        "conflict_keys": conflicts[:8],
        "warning_count": len(warnings),
        "used_fallback": bool(s.get("used_fallback")),
        "fallback_reason_category": fallback_reason_category(str(s.get("fallback_reason") or "")),
        "model_provider": str(s.get("model_provider") or ""),
        "model_name": str(s.get("model_name") or ""),
        "command_id_prefix": command_id_prefix(str(s.get("command_id") or "")),
        **redact_text_blob(story),
    }
    if s.get("case_id"):
        out["case_id_hash_prefix"] = case_id_hash_prefix(str(s.get("case_id")))
    return out


def filter_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    """Drop any non-allowlisted metadata keys (defense in depth)."""
    src = meta if isinstance(meta, dict) else {}
    out: dict[str, Any] = {}
    for k, v in src.items():
        key = str(k)
        if key not in META_ALLOWLIST:
            continue
        if key in {"raw_story", "accident_description", "normalized_story", "incident_summary"}:
            continue
        if isinstance(v, str) and len(v) > 200:
            out[key] = v[:200]
        else:
            out[key] = v
    return out


def build_root_trace_metadata(
    *,
    state: dict[str, Any] | None,
    scenario: str = "",
    latency_ms: int | None = None,
) -> dict[str, Any]:
    s = state if isinstance(state, dict) else {}
    missing = [str(x) for x in (s.get("missing_required_facts") or []) if str(x).strip()]
    questions = list(s.get("followup_questions") or [])
    meta = {
        "assistant": ASSISTANT_ID,
        "schema_version": int(s.get("schema_version") or SCHEMA_VERSION),
        "proposal_version": PROPOSAL_VERSION,
        "used_fallback": bool(s.get("used_fallback")),
        "fallback_reason_category": fallback_reason_category(str(s.get("fallback_reason") or "")),
        "question_count": len(questions),
        "missing_count": len(missing),
        "missing_keys": missing[:8],
        "injury_status": str(s.get("injury_status") or "unknown"),
        "model_provider": str(s.get("model_provider") or ""),
        "model_name": str(s.get("model_name") or ""),
        "command_id_prefix": command_id_prefix(str(s.get("command_id") or "")),
        "scenario": str(scenario or "")[:80],
        **redact_text_blob(str(s.get("normalized_story") or s.get("raw_story") or "")),
    }
    if latency_ms is not None:
        meta["latency_ms"] = int(latency_ms)
    if s.get("case_id"):
        meta["case_id_hash_prefix"] = case_id_hash_prefix(str(s.get("case_id")))
    return filter_meta(meta)


_SENSITIVE_STATE_KEYS = frozenset(
    {
        "raw_story",
        "normalized_story",
        "incident_summary",
        "accident_description",
        "accident_time_text",
        "accident_location_text",
        "proposed_facts",
        "followup_questions",
        "involved_vehicles",
        "involved_parties",
    }
)


def process_traced_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    """LangSmith process_inputs hook — redact AccidentStoryState kwargs/args."""
    try:
        if not isinstance(inputs, dict):
            return {"redacted": True}
        out: dict[str, Any] = {"redacted": True}
        if isinstance(inputs.get("state"), dict):
            out["state"] = redact_state_for_trace(inputs["state"])
        elif any(k in inputs for k in _SENSITIVE_STATE_KEYS) or "injury_status" in inputs:
            out["state"] = redact_state_for_trace(inputs)
        else:
            args = inputs.get("args")
            if isinstance(args, (list, tuple)) and args and isinstance(args[0], dict):
                out["state"] = redact_state_for_trace(args[0])
            elif isinstance(inputs.get("kwargs"), dict):
                kw = inputs["kwargs"]
                if isinstance(kw.get("state"), dict):
                    out["state"] = redact_state_for_trace(kw["state"])
                elif isinstance(kw.get("raw_story"), str):
                    # Root run: run_accident_story_graph(raw_story=...)
                    out["state"] = redact_state_for_trace(
                        {
                            "raw_story": kw.get("raw_story"),
                            "command_id": kw.get("command_id"),
                            "idempotency_key": "",
                        }
                    )
                    out["has_command_id"] = bool(str(kw.get("command_id") or "").strip())
                    out["scenario"] = str(kw.get("scenario") or "")[:80]
                else:
                    # Drop unknown kwargs that may contain prose
                    out["kwargs_keys"] = sorted(str(k) for k in kw.keys())[:20]
            if isinstance(inputs.get("raw_story"), str):
                out["state"] = redact_state_for_trace(inputs)
        return out
    except Exception:
        return {"redacted": True, "redaction_error": True}


def process_traced_outputs(outputs: Any) -> dict[str, Any]:
    try:
        if isinstance(outputs, dict):
            return redact_state_for_trace(outputs)
        return {"redacted": True, "type": type(outputs).__name__}
    except Exception:
        return {"redacted": True, "redaction_error": True}


class LatencyTimer:
    def __init__(self) -> None:
        self._t0 = time.perf_counter()

    def ms(self) -> int:
        return int((time.perf_counter() - self._t0) * 1000)


__all__ = [
    "ASSISTANT_ID",
    "META_ALLOWLIST",
    "PROPOSAL_VERSION",
    "LatencyTimer",
    "build_root_trace_metadata",
    "case_id_hash_prefix",
    "command_id_prefix",
    "fallback_reason_category",
    "filter_meta",
    "process_traced_inputs",
    "process_traced_outputs",
    "redact_state_for_trace",
    "redact_text_blob",
    "story_lang_hint",
]
