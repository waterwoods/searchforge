"""Add-Car Stage 1 field contract — canonical ids, labels, and lightweight validation.

Aligned with docs/sprints/ADD_CAR_FIELD_LEVEL_MINIMUM_CONTRACT_SPRINT/02_FIELD_LEVEL_MINIMUM_CONTRACT.md
and configs/common/add_car_stage1_field_contract.json (single source for ids + zh labels).
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONTRACT_PATH = _REPO_ROOT / "configs" / "common" / "add_car_stage1_field_contract.json"


@lru_cache(maxsize=1)
def load_add_car_stage1_contract() -> dict[str, Any]:
    raw = _CONTRACT_PATH.read_text(encoding="utf-8")
    return json.loads(raw)


def canonical_add_car_field_ids() -> frozenset[str]:
    data = load_add_car_stage1_contract()
    return frozenset(data.get("canonical_field_ids") or [])


def structural_still_needed_ids() -> frozenset[str]:
    data = load_add_car_stage1_contract()
    return frozenset(data.get("structural_still_needed_ids") or [])


def contact_still_needed_ids() -> frozenset[str]:
    data = load_add_car_stage1_contract()
    return frozenset(data.get("contact_still_needed_ids") or [])


def label_zh(field_id: str) -> str | None:
    data = load_add_car_stage1_contract()
    labels = data.get("labels_zh") or {}
    return labels.get(field_id)


def validate_add_car_field_lists(
    collected: list[str] | None,
    still_needed: list[str] | None,
    *,
    strict: bool | None = None,
) -> list[str]:
    """Return warnings for unknown field ids. If strict=True, raises ValueError on unknown.

    Unknown keys are the main contract drift vector between backend and UI.
    """
    if strict is None:
        strict = os.environ.get("ADD_CAR_CONTRACT_STRICT", "").strip().lower() in ("1", "true", "yes")
    allowed = canonical_add_car_field_ids()
    # Materials / doc-request keys may be dynamic (requested_*) — allow those patterns without listing all.
    dynamic_ok = ("requested_", "customer_says_sent_")

    def _check(items: list[str] | None, label: str) -> list[str]:
        out: list[str] = []
        for x in items or []:
            if not x:
                continue
            s = str(x).strip()
            if s in allowed:
                continue
            if any(s.startswith(p) for p in dynamic_ok):
                continue
            msg = f"{label}: unknown add-car field id {s!r}"
            out.append(msg)
            if strict:
                raise ValueError(msg)
        return out

    return _check(collected, "collected_fields") + _check(still_needed, "still_needed_fields")


def quote_ready_matches_still_needed(
    quote_ready_status: str,
    still_needed: list[str] | None,
) -> bool:
    """Return False if quote_ready_status contradicts core structural gaps in still_needed.

    Pilot: ``quote_ready`` and ``almost_ready`` both imply VIN is present in truth; neither
    may contradict a missing VIN in still_needed.
    """
    sn = {str(x).lower() for x in (still_needed or []) if x}
    qrs = (quote_ready_status or "").strip()
    # almost_ready / quote_ready: VIN must not be missing. Year/make may remain in still when VIN suffices.
    if qrs in ("quote_ready", "almost_ready"):
        if "vin" in sn:
            return False
    if qrs == "quote_ready":
        if "zip" in sn:
            return False
        if sn & {"primary_driver", "delivery_date"}:
            return False
    return True


def dedupe_preserve_order(items: list[str] | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items or []:
        if not x:
            continue
        k = str(x).strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out
