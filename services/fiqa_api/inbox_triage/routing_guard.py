"""
Append routing helpers: vehicle scope vs persisted case (CASE_CONTRACT_V1).

Keeps conflict detection pure and testable; triage.py supplies enriched booleans.
"""

from __future__ import annotations


def _norm_vehicle_key(key: str | None) -> str | None:
    s = (key or "").strip()
    return s if s else None


def detect_vehicle_conflict(
    persisted_vehicle_key: str | None,
    new_vehicle_key: str | None,
    additional_vehicle_mentioned: bool,
    *,
    message_suggests_vehicle_scope_ambiguity: bool = False,
) -> str:
    """
    Returns:
        "same_vehicle" — append stays on current vehicle scope
        "new_vehicle" — different vehicle / explicit multi-vehicle intent → new case
        "ambiguous" — conflicting or unclear vehicle scope → office confirmation
    """
    pv = _norm_vehicle_key(persisted_vehicle_key)
    nv = _norm_vehicle_key(new_vehicle_key)
    add = bool(additional_vehicle_mentioned)

    # Extra-vehicle intent wins even when the persisted record has no vehicle_key yet
    # (e.g. early thread: customer asks to add another car before VIN is on file).
    if add:
        return "new_vehicle"

    if message_suggests_vehicle_scope_ambiguity and pv:
        return "ambiguous"

    if not pv:
        return "same_vehicle"
    if nv and nv == pv:
        return "same_vehicle"
    if nv and nv != pv:
        return "new_vehicle"
    # Persisted scope exists but this turn did not surface a distinct key — treat as same
    # vehicle unless the message hints at a different scope (handled above).
    return "same_vehicle"


def text_suggests_vehicle_scope_ambiguity(message: str) -> bool:
    """Comparative / cross-vehicle phrasing without a clear single-vehicle correction."""
    t = (message or "").strip()
    if not t:
        return False
    tl = t.lower()
    if "other car" in tl and ("same" in tl or "like" in tl or "as" in tl):
        return True
    if "另一辆" in t and ("一样" in t or "相同" in t or "同样" in t):
        return True
    if "跟另一" in t or "和另一" in t:
        return True
    return False


def append_turn_signals_extra_vehicle_intent(message: str) -> bool:
    """
    Phrases that imply a second vehicle / add-another scope on this turn.
    Feeds additional_vehicle_mentioned for detect_vehicle_conflict when rule extractors miss it.
    """
    raw = (message or "").strip()
    if not raw:
        return False
    tl = raw.lower()
    en_markers = (
        "another car",
        "a second car",
        "second car",
        "one more car",
        "add another car",
        "add another vehicle",
        "two cars",
        "second vehicle",
        "one more vehicle",
    )
    if any(m in tl for m in en_markers):
        return True
    zh_markers = (
        "另一台",
        "还有一台",
        "第二辆",
        "另一辆",
        "再加",
        "还有一辆",
        "两台车",
        "第二台",
        "再买一辆",
        "再买一台",
    )
    return any(m in raw for m in zh_markers)
