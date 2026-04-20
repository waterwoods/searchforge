"""Declarative field strategy for add-car (PTD §9): config-driven tiers, blocking, defaults, deferral, runtime partition."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
_STRATEGY_PATH = _REPO_ROOT / "configs" / "common" / "add_car_field_strategy.json"


@lru_cache(maxsize=1)
def load_add_car_field_strategy() -> dict[str, Any]:
    raw = _STRATEGY_PATH.read_text(encoding="utf-8")
    return json.loads(raw)


def get_field_spec(field_id: str) -> dict[str, Any] | None:
    data = load_add_car_field_strategy()
    fields = data.get("fields")
    if not isinstance(fields, dict):
        return None
    spec = fields.get(str(field_id).strip())
    return dict(spec) if isinstance(spec, dict) else None


def get_default_engine_section() -> dict[str, Any]:
    data = load_add_car_field_strategy()
    de = data.get("default_engine")
    return dict(de) if isinstance(de, dict) else {}


def _session_status(field_id: str, *, collected: set[str], missing: set[str], inferred: set[str]) -> str:
    fl = field_id.lower()
    if fl in collected and fl not in missing:
        return "collected"
    if fl in missing:
        return "missing"
    if fl in inferred:
        return "inferred"
    return "not_seen"


def _norm_field_id(fid: str) -> str:
    return str(fid or "").strip().lower()


def partition_still_needed_by_strategy(still_needed_field_ids: list[str]) -> dict[str, Any]:
    """
    Split operational missing list into user-flow prompts vs broker-deferred (PTD §9–§11).

    Rules:
    - Tier 3 → deferred (never user-blocking).
    - defer_to_broker=true → deferred.
    - blocking=false AND priority_tier >= 2 → deferred (Tier-2 quality fields do not block user flow).
    - Unknown fields → user_flow (conservative).
    """
    user_flow: list[str] = []
    deferred: list[str] = []
    reasons: dict[str, str] = {}

    for raw in still_needed_field_ids or []:
        fid = _norm_field_id(raw)
        if not fid:
            continue
        spec = get_field_spec(fid)
        if spec is None:
            user_flow.append(raw)
            reasons[fid] = "unknown_field_conservative_user_flow"
            continue
        tier = int(spec.get("priority_tier") or 0)
        defer_b = bool(spec.get("defer_to_broker"))
        blocking = bool(spec.get("blocking"))

        if tier >= 3:
            deferred.append(raw)
            reasons[fid] = "tier3_never_user_blocking"
            continue
        if defer_b:
            deferred.append(raw)
            reasons[fid] = "defer_to_broker"
            continue
        if not blocking and tier >= 2:
            deferred.append(raw)
            reasons[fid] = "non_blocking_tier2"
            continue
        user_flow.append(raw)
        reasons[fid] = "user_flow_blocking_or_tier1"

    # Tier order: 1 first, then 2 (stable within tier by field name)
    def _tier_key(fid: str) -> tuple[int, str]:
        sp = get_field_spec(_norm_field_id(fid))
        t = int(sp.get("priority_tier") or 99) if sp else 99
        return (t, fid)

    user_flow.sort(key=_tier_key)
    return {
        "still_needed_user_flow": user_flow,
        "deferred_to_broker_fields": deferred,
        "deferred_reasons": reasons,
    }


def build_field_strategy_view(
    *,
    collected_field_ids: list[str],
    missing_field_ids: list[str],
    inferred_field_keys: set[str],
) -> dict[str, Any]:
    """Attach to case_draft for UI, analytics, and explainability."""
    data = load_add_car_field_strategy()
    fields_cfg = data.get("fields") or {}
    if not isinstance(fields_cfg, dict):
        fields_cfg = {}

    coll = {str(x).lower() for x in collected_field_ids if x}
    miss = {str(x).lower() for x in missing_field_ids if x}
    inf = {str(x).lower() for x in inferred_field_keys if x}

    out_fields: dict[str, Any] = {}
    for fid, spec in fields_cfg.items():
        if not isinstance(spec, dict):
            continue
        st = _session_status(fid, collected=coll, missing=miss, inferred=inf)
        out_fields[fid] = {
            **spec,
            "session_status": st,
        }

    tier1_blocking_missing = [
        fid
        for fid, row in out_fields.items()
        if int(row.get("priority_tier") or 0) == 1
        and bool(row.get("blocking"))
        and row.get("session_status") == "missing"
    ]

    part = partition_still_needed_by_strategy(list(missing_field_ids or []))

    return {
        "version": data.get("version"),
        "lane": data.get("lane"),
        "fields": out_fields,
        "tier1_blocking_missing": tier1_blocking_missing,
        "still_needed_user_flow": part.get("still_needed_user_flow") or [],
        "deferred_to_broker_fields": part.get("deferred_to_broker_fields") or [],
        "deferred_reasons": part.get("deferred_reasons") or {},
    }


def usage_default_from_strategy() -> tuple[str, float, int]:
    """Industry fallback for usage_guess when no keyword match (auto_fill_defaults)."""
    spec = get_field_spec("usage_guess") or {}
    val = spec.get("default_value")
    if val is None or str(val).strip() == "":
        val = "daily_commute"
    conf = float(spec.get("confidence_score") or 0.35)
    tier = int(spec.get("priority_tier") or 2)
    return str(val), conf, tier


def should_skip_user_prompt_for_missing_field(field_id: str) -> bool:
    """True when chat layer should not nag for this missing slot (e.g. VIN deferral)."""
    spec = get_field_spec(field_id)
    if spec is None:
        return False
    if bool(spec.get("defer_to_broker")):
        return True
    if int(spec.get("priority_tier") or 0) >= 3:
        return True
    if not bool(spec.get("blocking")) and int(spec.get("priority_tier") or 0) >= 2:
        return True
    return False


def confirm_priority_tier_for_inferred_key(field_key: str) -> int | None:
    """Map inferred bundle key to strategy tier (None = unknown — keep legacy confirm behavior)."""
    spec = get_field_spec(field_key)
    if spec is None:
        return None
    return int(spec.get("priority_tier") or 2)

