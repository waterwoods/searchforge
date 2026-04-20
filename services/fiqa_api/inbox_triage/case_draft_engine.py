"""
Auto Case Draft — structured snapshot for every add-car (and generic) turn.

Additive: triage remains authoritative; this packages known / inferred / missing / confidence
for UI, analytics, and minimal-question routing.

V4 Zero-Question Intake: infer → draft → confirm → submit (variants B/C).
V5 Immediate Handoff Engine: case_usable (structural completeness + tier-1 vehicle) replaces quote_ready for broker handoff gating; VIN/name/phone do not block case_usable.
"""

from __future__ import annotations

import re
from typing import Any

from services.fiqa_api.inbox_triage.add_car_vehicle_signals import utterance_has_explicit_vehicle_identity
from services.fiqa_api.inbox_triage.error_tolerance_layer import apply_error_tolerance
from services.fiqa_api.inbox_triage.field_strategy import (
    build_field_strategy_view,
    confirm_priority_tier_for_inferred_key,
    get_default_engine_section,
    get_field_spec,
    usage_default_from_strategy,
)
from services.fiqa_api.inbox_triage.ocr_case_fusion import fuse_ocr_into_inferred

# Fields we never mark as high-confidence without extraction/guardrail truth
_HIGH_RISK_SLOT_IDS = frozenset({"vin", "primary_driver", "delivery_date", "zip", "name", "phone"})

# --- V4: confidence tiers (product policy) ---------------------------------
CONF_HIGH = "high"  # auto-accept in draft packaging (still truth-gated upstream)
CONF_MEDIUM = "medium"  # show in confirmation block
CONF_LOW = "low"  # defer to broker or ignore in UX

# Core slots for completeness (0–1 scale for partial-handoff policy)
_V4_CORE_SLOT_WEIGHTS: dict[str, float] = {
    "year": 0.10,
    "make_model": 0.12,
    "vin": 0.22,
    "zip": 0.12,
    "delivery_date": 0.12,
    "primary_driver": 0.10,
    "name": 0.08,
    "phone": 0.14,
}

# V5 handoff: VIN never blocks; name/phone are conversion/contact — not part of case_usable gate
_V5_HANDOFF_SLOT_WEIGHTS: dict[str, float] = {
    "year": 0.20,
    "make_model": 0.24,
    "zip": 0.22,
    "delivery_date": 0.17,
    "primary_driver": 0.17,
}

# Heuristic CA ZIP3 → rough area label (safe display only; broker verifies).
# Superseded by default_engine.garaging_area_hint.zip3_prefix_hints when present (PTD §10).
_CA_ZIP3_AREA_HINT: dict[str, str] = {
    "926": "Orange County, CA",
    "927": "Orange County, CA",
    "928": "Orange County, CA",
    "900": "Los Angeles, CA",
    "902": "Los Angeles, CA",
    "941": "San Francisco Bay Area, CA",
    "951": "Inland Empire, CA",
    "945": "East Bay, CA",
    "950": "South Bay / Peninsula, CA",
}


def _resolved_zip3_area_hints() -> dict[str, str]:
    _de = get_default_engine_section()
    _gh = dict(_de.get("garaging_area_hint") or {}) if isinstance(_de, dict) else {}
    raw = _gh.get("zip3_prefix_hints")
    if isinstance(raw, dict) and raw:
        out: dict[str, str] = {}
        for k, v in raw.items():
            ks = str(k).strip()
            vs = str(v).strip()
            if ks and vs:
                out[ks] = vs
        return out if out else _CA_ZIP3_AREA_HINT
    return _CA_ZIP3_AREA_HINT


def _norm_list(xs: list[str] | None) -> list[str]:
    out: list[str] = []
    for x in xs or []:
        s = str(x).strip()
        if s:
            out.append(s)
    return out


def _zip5_from_text(text: str) -> str | None:
    m = re.search(r"\b(9[0-9]{4})\b", text or "")
    return m.group(1) if m else None


def auto_fill_defaults(
    merged_text: str,
    *,
    collected_field_ids: list[str],
    missing_field_ids: list[str],
    primary_vehicle_summary: str | None,
) -> dict[str, Any]:
    """
    Safe industry/heuristic defaults only — never fabricates VIN, phone, or legal name.
    All auto-filled keys are LOW–MEDIUM confidence and must be labeled inferred.
    """
    inferred: dict[str, Any] = {}
    mt = merged_text or ""
    coll = {str(x).lower() for x in collected_field_ids}
    miss = {str(x).lower() for x in missing_field_ids}
    _de_cfg = get_default_engine_section()
    _de_gh = dict(_de_cfg.get("garaging_area_hint") or {}) if isinstance(_de_cfg, dict) else {}
    z = _zip5_from_text(mt) if "zip" in miss or "zip" in coll else None
    if z and len(z) == 5:
        pre3 = z[:3]
        area = _resolved_zip3_area_hints().get(pre3)
        if area and "garaging_area_hint" not in coll:
            _gfs = get_field_spec("garaging_area_hint") or {}
            inferred["garaging_area_hint"] = {
                "value": area,
                "from_zip_prefix": pre3,
                "confidence": float(_gfs.get("confidence_score") or 0.48),
                "tier": CONF_LOW,
                "source": "zip_prefix_heuristic",
                "field_strategy_id": "garaging_area_hint",
                "confidence_policy": str(_gfs.get("confidence_policy") or "weak_hint"),
                "default_engine": {
                    "fallback_order": list(_de_gh.get("fallback_order") or ["zip_prefix_map", "phone_area_code_map"]),
                    "rule_id": "ca_zip3_area_hint",
                },
            }

    tl = mt.lower()
    usage_val = None
    usage_conf = 0.38
    _de_u = dict(_de_cfg.get("usage_guess") or {}) if isinstance(_de_cfg, dict) else {}
    _kw_rules = _de_u.get("keyword_rules")
    if isinstance(_kw_rules, list) and _kw_rules:
        for rule in _kw_rules:
            if not isinstance(rule, dict):
                continue
            val = rule.get("value")
            kws = rule.get("keywords") or []
            conf = rule.get("confidence")
            if not val or not isinstance(kws, list):
                continue
            try:
                uc = float(conf) if conf is not None else 0.38
            except (TypeError, ValueError):
                uc = 0.38
            if any(str(k).lower() in tl for k in kws if k):
                usage_val = str(val)
                usage_conf = uc
                break
    else:
        if any(x in tl for x in ("commute", "上下班", "通勤", "daily driver", "daily drive")):
            usage_val = "daily_commute"
            usage_conf = 0.52
        elif any(x in tl for x in ("uber", "lyft", "rideshare", "网约车")):
            usage_val = "rideshare"
            usage_conf = 0.48
        elif any(x in tl for x in ("pleasure", "weekend", "偶尔", "休闲")):
            usage_val = "pleasure"
            usage_conf = 0.42
    if usage_val:
        _ugs_kw = get_field_spec("usage_guess") or {}
        _ug_kw_de = {
            "fallback_order": list(_de_u.get("fallback_order") or ["keyword_heuristic", "industry_default"]),
            "rule_id": "usage_keyword_rules" if isinstance(_kw_rules, list) and _kw_rules else "usage_keyword_heuristic",
        }
        inferred["usage_guess"] = {
            "value": usage_val,
            "confidence": usage_conf,
            "tier": CONF_MEDIUM if usage_conf >= 0.5 else CONF_LOW,
            "source": "keyword_heuristic",
            "field_strategy_id": "usage_guess",
            "confidence_policy": str(_ugs_kw.get("confidence_policy") or "default_low"),
            "default_engine": _ug_kw_de,
        }
    elif "usage" in miss or "primary_use" in miss:
        dv, dc, pt = usage_default_from_strategy()
        _ugs = get_field_spec("usage_guess") or {}
        inferred["usage_guess"] = {
            "value": dv,
            "confidence": dc,
            "tier": CONF_MEDIUM if dc >= 0.5 else CONF_LOW,
            "source": "industry_default",
            "priority_tier": pt,
            "field_strategy_id": "usage_guess",
            "confidence_policy": str(_ugs.get("confidence_policy") or "default_low"),
            "default_engine": {
                "fallback_order": list(_de_u.get("fallback_order") or ["keyword_heuristic", "industry_default"]),
                "rule_id": "usage_industry_default",
            },
        }

    pvc = (primary_vehicle_summary or "").strip()
    if pvc and ("year" in miss or "make_model" in miss):
        _vfs = get_field_spec("vehicle_from_summary") or {}
        _de_v = dict(_de_cfg.get("vehicle_from_summary") or {}) if isinstance(_de_cfg, dict) else {}
        inferred["vehicle_from_summary"] = {
            "hint": pvc,
            "confidence": float(_vfs.get("confidence_score") or 0.55),
            "tier": CONF_MEDIUM,
            "needs_confirmation": True,
            "source": "primary_vehicle_summary",
            "field_strategy_id": "vehicle_from_summary",
            "confidence_policy": str(_vfs.get("confidence_policy") or "prefer_inference"),
            "default_engine": {
                "fallback_order": list(_de_v.get("fallback_order") or ["primary_vehicle_summary"]),
                "rule_id": "vehicle_from_summary_hint",
            },
        }

    # V6: light location inference from common CA area codes in thread (display hint only)
    if "zip" in miss or "garaging_area_hint" not in coll:
        digits_only = re.sub(r"[^\d]", "", mt)
        phone_ac: str | None = None
        if len(digits_only) >= 10:
            m10 = re.search(r"(\d{3})(\d{3})(\d{4})$", digits_only)
            if m10:
                ac = m10.group(1)
                if ac in (
                    "415",
                    "650",
                    "408",
                    "925",
                    "949",
                    "510",
                    "213",
                    "310",
                    "323",
                    "626",
                    "714",
                    "657",
                    "562",
                ):
                    phone_ac = ac
        if not phone_ac:
            par = re.search(r"\((\d{3})\)\s*\d{3}[-.\s]?\d{4}", mt)
            if par:
                phone_ac = par.group(1)
        if phone_ac:
            ac = phone_ac
            area_hint = {
                "415": "San Francisco Bay Area, CA",
                "650": "Peninsula / South Bay, CA",
                "408": "South Bay, CA",
                "925": "East Bay, CA",
                "949": "Orange County / Coastal OC, CA",
                "510": "East Bay, CA",
                "213": "Los Angeles, CA",
                "310": "West LA / LA, CA",
                "323": "Los Angeles, CA",
                "626": "San Gabriel Valley, CA",
                "714": "Orange County, CA",
                "657": "Orange County, CA",
                "562": "Long Beach / LA, CA",
            }.get(ac)
            if area_hint and "garaging_area_hint" not in inferred:
                _gfs2 = get_field_spec("garaging_area_hint") or {}
                inferred["garaging_area_hint"] = {
                    "value": area_hint,
                    "from_area_code": ac,
                    "confidence": 0.36,
                    "tier": CONF_LOW,
                    "source": "phone_area_hint",
                    "field_strategy_id": "garaging_area_hint",
                    "confidence_policy": str(_gfs2.get("confidence_policy") or "weak_hint"),
                    "default_engine": {"fallback_order": ["phone_area_code_map"], "rule_id": "ca_phone_area_hint"},
                }

    # V6: common make token in thread → weak model hint (never replaces explicit extraction)
    if "make_model" in miss:
        tl2 = mt.lower()
        for make in (
            "toyota",
            "honda",
            "tesla",
            "bmw",
            "mercedes",
            "ford",
            "chevrolet",
            "nissan",
            "mazda",
            "subaru",
            "hyundai",
            "kia",
            "lexus",
            "audi",
        ):
            if re.search(rf"\b{re.escape(make)}\b", tl2):
                _mk = get_field_spec("make_keyword_hint") or {}
                inferred["make_keyword_hint"] = {
                    "value": make.title(),
                    "confidence": float(_mk.get("confidence_score") or 0.33),
                    "tier": CONF_LOW,
                    "source": "make_token_heuristic",
                    "field_strategy_id": "make_keyword_hint",
                    "confidence_policy": str(_mk.get("confidence_policy") or "weak_hint"),
                }
                break

    return {"inferred_fields": inferred}


def compute_v4_completeness(
    collected_field_ids: list[str],
    missing_field_ids: list[str],
    inferred_pack: dict[str, Any],
) -> float:
    """Weighted completeness in [0,1] for partial-handoff policy (≥0.70 usable)."""
    coll = {str(x).lower() for x in collected_field_ids}
    miss = {str(x).lower() for x in missing_field_ids}
    inferred = inferred_pack.get("inferred_fields") if isinstance(inferred_pack, dict) else {}
    inf_keys = set(inferred.keys()) if isinstance(inferred, dict) else set()

    slot_ok: dict[str, bool] = {}
    for slot in _V4_CORE_SLOT_WEIGHTS:
        if slot in coll and slot not in miss:
            slot_ok[slot] = True
        elif slot == "make_model" and ("make_model" in coll or "model" in coll):
            slot_ok[slot] = True
        else:
            slot_ok[slot] = False

    # Inferior substitutes (do not count as truth; partial credit only)
    if not slot_ok.get("zip") and "garaging_area_hint" in inf_keys:
        slot_ok["zip"] = True  # partial credit below via weight discount
    if not slot_ok.get("make_model") and "vehicle_from_summary" in inf_keys:
        slot_ok["make_model"] = True

    total_w = sum(_V4_CORE_SLOT_WEIGHTS.values())
    earned = 0.0
    for slot, w in _V4_CORE_SLOT_WEIGHTS.items():
        if slot_ok.get(slot):
            if slot == "zip" and "zip" not in coll and "garaging_area_hint" in inf_keys:
                earned += w * 0.55
            elif slot == "make_model" and "make_model" not in coll and "vehicle_from_summary" in inf_keys:
                earned += w * 0.65
            else:
                earned += w
    return round(min(1.0, earned / total_w), 3)


def v5_completeness_threshold(variant: str) -> float:
    """Aligned with structural completeness (year/make/zip alone ≈0.66). A = conservative, C = minimal."""
    v = (variant or "A").strip().upper()
    if v == "B":
        return 0.58
    if v == "C":
        return 0.50
    return 0.62


def compute_v5_handoff_completeness(
    collected_field_ids: list[str],
    missing_field_ids: list[str],
    inferred_pack: dict[str, Any],
) -> float:
    """Weighted completeness for broker-usable case handoff — no VIN requirement."""
    coll = {str(x).lower() for x in collected_field_ids}
    miss = {str(x).lower() for x in missing_field_ids}
    inferred = inferred_pack.get("inferred_fields") if isinstance(inferred_pack, dict) else {}
    inf_keys = set(inferred.keys()) if isinstance(inferred, dict) else set()

    slot_ok: dict[str, bool] = {}
    for slot in _V5_HANDOFF_SLOT_WEIGHTS:
        if slot in coll and slot not in miss:
            slot_ok[slot] = True
        elif slot == "make_model" and ("make_model" in coll or "model" in coll):
            slot_ok[slot] = True
        else:
            slot_ok[slot] = False

    if not slot_ok.get("zip") and "garaging_area_hint" in inf_keys:
        slot_ok["zip"] = True
    if not slot_ok.get("make_model") and "vehicle_from_summary" in inf_keys:
        slot_ok["make_model"] = True

    total_w = sum(_V5_HANDOFF_SLOT_WEIGHTS.values())
    earned = 0.0
    for slot, w in _V5_HANDOFF_SLOT_WEIGHTS.items():
        if slot_ok.get(slot):
            if slot == "zip" and "zip" not in coll and "garaging_area_hint" in inf_keys:
                earned += w * 0.55
            elif slot == "make_model" and "make_model" not in coll and "vehicle_from_summary" in inf_keys:
                earned += w * 0.65
            else:
                earned += w
    return round(min(1.0, earned / total_w), 3)


def add_car_tier1_vehicle_ok(
    merged_text: str,
    primary_vehicle_summary: str | None,
    collected_field_ids: list[str],
    missing_field_ids: list[str],
) -> bool:
    """Tier 1: basic vehicle existence (intent is add_car lane — caller enforces)."""
    coll = {str(x).lower() for x in collected_field_ids}
    miss = {str(x).lower() for x in missing_field_ids}
    if "vin" in coll and "vin" not in miss:
        return True
    cust_blob = " ".join(re.findall(r"\[客户\]\s*([^[]+)", merged_text or ""))
    scan = (cust_blob.strip() or merged_text or "").strip()
    if utterance_has_explicit_vehicle_identity(scan):
        return True
    pvc = (primary_vehicle_summary or "").strip()
    if len(pvc) >= 6:
        return True
    if ("year" in coll and "year" not in miss) and (
        ("make_model" in coll or "model" in coll)
        and "make_model" not in miss
        and "model" not in miss
    ):
        return True
    return False


def evaluate_v5_case_usable(
    bundle: dict[str, Any],
    *,
    merged_text: str,
    primary_vehicle_summary: str | None,
    variant: str,
) -> tuple[bool, float, str]:
    """True when Tier1 satisfied and V5 completeness meets variant threshold (not quote_ready)."""
    collected = list(bundle.get("collected_fields") or [])
    missing = list(bundle.get("missing_fields") or [])
    inferred = bundle.get("inferred_fields") if isinstance(bundle.get("inferred_fields"), dict) else {}
    tier1 = add_car_tier1_vehicle_ok(merged_text, primary_vehicle_summary, collected, missing)
    if not tier1:
        return False, 0.0, "tier1_vehicle_missing"
    v5c = compute_v5_handoff_completeness(
        collected,
        missing,
        {"inferred_fields": inferred},
    )
    thresh = v5_completeness_threshold(variant)
    if v5c + 1e-9 >= thresh:
        return True, v5c, "usable"
    return False, v5c, "below_completeness_threshold"


def estimate_v5_handoff_risk_score(
    bundle: dict[str, Any],
    *,
    quote_ready_status: str,
    case_usable: bool,
) -> float:
    """0–1: higher = broker must backfill / higher mis-quote risk."""
    base = estimate_v4_error_risk_score(bundle, quote_ready_status=quote_ready_status)
    if case_usable and quote_ready_status != "quote_ready":
        base = min(1.0, base + 0.12)
    return round(min(1.0, base), 3)


def _tier_from_conf(c: float) -> str:
    if c >= 0.82:
        return CONF_HIGH
    if c >= 0.52:
        return CONF_MEDIUM
    return CONF_LOW


def build_confirm_priority_fields(
    confidence_map: dict[str, float],
    inferred_fields: dict[str, Any],
    *,
    variant: str,
) -> list[str]:
    """Field-strategy tier first (Tier 1 > 2; Tier 3 excluded), then MEDIUM-confidence; variant C surfaces more keys."""
    v = (variant or "A").strip().upper()
    candidates: list[tuple[int, float, str]] = []
    for k, v_inf in inferred_fields.items():
        if not isinstance(v_inf, dict):
            continue
        fk = str(k)
        pt = confirm_priority_tier_for_inferred_key(fk)
        if pt is not None and pt >= 3:
            continue
        conf = float(v_inf.get("confidence") or 0.0)
        tier = str(v_inf.get("tier") or _tier_from_conf(conf))
        eligible = tier == CONF_MEDIUM or (v == "C" and tier == CONF_LOW and v_inf.get("needs_confirmation"))
        if not eligible:
            continue
        sort_tier = pt if pt is not None else 2
        candidates.append((sort_tier, -conf, fk))
    candidates.sort(key=lambda x: (x[0], x[1]))
    out = [c[2] for c in candidates]
    seen: set[str] = set()
    deduped: list[str] = []
    for x in out:
        if x not in seen:
            deduped.append(x)
            seen.add(x)
    return deduped


def format_v4_confirmation_block(
    *,
    language: str,
    lines: list[tuple[str, str]],
    variant: str,
) -> str:
    """Single confirmation step — no multi-question ladder in this string."""
    is_zh = (language or "").strip().lower() == "zh"
    v = (variant or "B").strip().upper()
    head = (
        "我先根据你的留言整理了一版，请你看一下对不对："
        if is_zh
        else "Here's what I have from your message—does this look right?"
    )
    bullets = "\n".join(f"• {label}: {value}" for label, value in lines if value)
    tail = (
        "如果都对，回复「好」或 OK；不对请直接改在一条消息里。"
        if is_zh
        else 'If it looks right, reply "OK" or "yes". If anything is wrong, send corrections in one message.'
    )
    if v == "C":
        extra = (
            "\n（办公室仍会核对细节。）"
            if is_zh
            else "\n(The office will still verify details.)"
        )
        tail = tail + extra
    return "\n".join([head, bullets, tail]).strip()


def build_v6_unified_confirmation_preview(
    bundle: dict[str, Any],
    *,
    language: str,
    primary_vehicle_summary: str | None,
) -> dict[str, Any]:
    """Single-block confirmation metadata for UI (OCR highlights + edit affordances)."""
    is_zh = (language or "").strip().lower() == "zh"
    inferred = bundle.get("inferred_fields") or {}
    ocr_keys = [k for k, v in inferred.items() if isinstance(v, dict) and v.get("v6_highlight")]
    pvc = (primary_vehicle_summary or "").strip() or "(…)"
    lines: list[str] = []
    head = "我已为你整理好关键项，请确认或一条消息内修改：" if is_zh else "I've prepared everything for you—confirm or edit in one message:"
    lines.append(head)
    v_label = "车辆" if is_zh else "Vehicle"
    lines.append(f"🚗 {v_label}: {pvc}")
    z = _zip5_from_text(str(bundle.get("merged_text_for_v6") or ""))
    if not z:
        z_ocr = inferred.get("zip_from_ocr")
        if isinstance(z_ocr, dict) and z_ocr.get("value"):
            z = str(z_ocr.get("value"))
    z_label = "邮编" if is_zh else "ZIP"
    lines.append(f"📍 {z_label}: {z or ('(待补充)' if is_zh else '(add ZIP)')}")
    drv = "1 位驾驶人" if is_zh else "1 driver"
    lines.append(f"👤 {drv}")
    tail = "回复「好」或 OK 确认。" if is_zh else 'Reply "OK" to proceed.'
    lines.append(tail)
    return {
        "headline": head,
        "lines": lines,
        "ocr_highlight_field_keys": ocr_keys[:24],
        "single_confirmation_step": True,
    }


def build_v4_case_draft_bundle(
    *,
    merged_text: str,
    collected_fields: list[str],
    missing_fields: list[str],
    primary_vehicle_summary: str | None,
    quote_ready_status: str,
    human_confirmation_fields: list[str],
    issue_category: str,
    language: str,
    variant: str,
    ocr_context: dict[str, Any] | None = None,
    v6_auto_input_variant: str = "A",
) -> dict[str, Any]:
    """
    Full V4 snapshot layered on top of legacy case_draft fields.
    """
    collected = _norm_list(list(collected_fields or []))
    missing = _norm_list(list(missing_fields or []))
    af = auto_fill_defaults(
        merged_text,
        collected_field_ids=collected,
        missing_field_ids=missing,
        primary_vehicle_summary=primary_vehicle_summary,
    )
    inferred_extra = dict(af.get("inferred_fields") or {})

    base = build_add_car_case_draft(
        merged_text=merged_text,
        collected_fields=collected,
        still_needed_fields=missing,
        primary_vehicle_summary=primary_vehicle_summary,
        quote_ready_status=quote_ready_status,
        human_confirmation_fields=human_confirmation_fields,
        issue_category=issue_category,
        language=language,
    )
    known = dict(base.get("known_fields") or {})
    inferred = dict(base.get("inferred_fields") or {})
    inferred.update(inferred_extra)
    inferred = fuse_ocr_into_inferred(
        merged_text,
        inferred_fields=inferred,
        ocr_structured=ocr_context,
        v6_variant=v6_auto_input_variant,
    )

    confidence_map: dict[str, float] = dict(base.get("confidence_map") or {})
    for k, v in inferred.items():
        if isinstance(v, dict):
            confidence_map[f"inferred:{k}"] = float(v.get("confidence") or 0.0)

    completeness = compute_v4_completeness(collected, missing, {"inferred_fields": inferred})
    v5_hc = compute_v5_handoff_completeness(collected, missing, {"inferred_fields": inferred})
    tier1_ok = add_car_tier1_vehicle_ok(
        merged_text,
        primary_vehicle_summary,
        collected,
        missing,
    )
    v5_thresh = v5_completeness_threshold(variant)
    case_usable = bool(tier1_ok and v5_hc + 1e-9 >= v5_thresh)
    confirm_priority = build_confirm_priority_fields(confidence_map, inferred, variant=variant)

    partial_eligible = completeness >= 0.70

    out_bundle = {
        **base,
        "collected_fields": collected,
        "still_needed_fields": missing,
        "inferred_fields": inferred,
        "confidence_map": confidence_map,
        "confirm_priority_fields": confirm_priority,
        "v4_completeness_score": completeness,
        "v5_handoff_completeness_score": v5_hc,
        "v5_completeness_threshold": v5_thresh,
        "v5_tier1_vehicle_ok": tier1_ok,
        "case_usable": case_usable,
        "v4_partial_handoff_eligible": partial_eligible,
        "v4_flow": True,
        "merged_text_for_v6": merged_text,
        "v6_auto_input_variant": (v6_auto_input_variant or "A").strip().upper(),
        "confidence_tier_policy": {
            "high_auto": CONF_HIGH,
            "medium_confirm": CONF_MEDIUM,
            "low_defer": CONF_LOW,
        },
    }
    out_bundle["v6_confirmation"] = build_v6_unified_confirmation_preview(
        out_bundle,
        language=language,
        primary_vehicle_summary=primary_vehicle_summary,
    )
    inf_keys = {str(k) for k in (out_bundle.get("inferred_fields") or {}).keys() if k}
    out_bundle["field_strategy"] = build_field_strategy_view(
        collected_field_ids=collected,
        missing_field_ids=missing,
        inferred_field_keys=inf_keys,
    )
    fs = out_bundle.get("field_strategy") or {}
    out_bundle["still_needed_user_flow"] = list(fs.get("still_needed_user_flow") or [])
    out_bundle["deferred_to_broker_fields"] = list(fs.get("deferred_to_broker_fields") or [])
    _def_fields = out_bundle["deferred_to_broker_fields"]
    _def_lab = ", ".join(str(x).replace("_", " ") for x in _def_fields[:16])
    out_bundle["broker_completion"] = {
        "broker_usable_case": bool(out_bundle.get("case_usable")),
        "deferred_fields": list(_def_fields),
        "full_missing_fields": list(missing),
        "office_completes_summary": (
            f"Office completes later: {_def_lab}." if _def_lab else "No broker-deferred gaps flagged by strategy."
        ),
    }
    out_bundle = apply_error_tolerance(out_bundle, quote_ready_status=quote_ready_status)
    return out_bundle


def build_v4_confirmation_client_reply_from_bundle(
    bundle: dict[str, Any],
    *,
    merged_text: str,
    primary_vehicle_summary: str | None,
    language: str,
    variant: str,
) -> str:
    """Single confirmation block for B/C — replaces multi-step question ladder."""
    is_zh = (language or "").strip().lower() == "zh"
    inferred = bundle.get("inferred_fields") or {}
    lines: list[tuple[str, str]] = []

    pvc = (primary_vehicle_summary or "").strip()
    if not pvc:
        pvc = (merged_text or "").strip()[:120]
    lab_v = "车辆" if is_zh else "Vehicle"
    lines.append((lab_v, pvc or ("(待确认)" if is_zh else "(to confirm)")))

    z = _zip5_from_text(merged_text or "")
    lab_z = "邮编" if is_zh else "ZIP"
    lines.append((lab_z, z or ("(待补充)" if is_zh else "(add ZIP)")))

    gh = inferred.get("garaging_area_hint")
    if isinstance(gh, dict) and (gh.get("value") or "").strip():
        lines.append(("地区" if is_zh else "Area hint", str(gh.get("value"))))

    ug = inferred.get("usage_guess")
    if isinstance(ug, dict) and (ug.get("value") or "").strip():
        lines.append(("用途估计" if is_zh else "Usage (estimate)", str(ug.get("value"))))

    miss = bundle.get("missing_fields") or []
    miss_l = [str(x) for x in miss if str(x).strip()]
    if miss_l:
        pending = ", ".join(miss_l[:6])
        lines.append(
            ("待办公室补齐" if is_zh else "Office may still need", pending)
        )

    return format_v4_confirmation_block(
        language=language,
        lines=lines,
        variant=variant,
    )


def estimate_v4_error_risk_score(
    bundle: dict[str, Any],
    *,
    quote_ready_status: str,
) -> float:
    """
    Heuristic 0–1: higher = riskier inference (wrong default hurts quote/binding).
    """
    base = 0.12
    if quote_ready_status == "quote_ready":
        return round(min(1.0, base + 0.05), 3)
    inf = bundle.get("inferred_fields") or {}
    risk = base
    if isinstance(inf.get("usage_guess"), dict) and inf["usage_guess"].get("source") == "industry_default":
        risk += 0.18
    if "garaging_area_hint" in inf:
        risk += 0.12
    if float(bundle.get("v4_completeness_score") or 0) < 0.85:
        risk += 0.15
    return round(min(1.0, risk), 3)


def _intent_key(lowered: str, issue_category: str) -> str:
    if any(m in lowered for m in ("加车", "add car", "add vehicle", "new car", "提车", "quote")):
        return "add_car_quote"
    if any(m in lowered for m in ("换保", "switch", "转保")):
        return "switch_carrier"
    if issue_category in ("cancellation_warning", "payment_lapse_expiration"):
        return "payment_risk"
    if issue_category == "missing_document":
        return "document_followup"
    return "general"


def build_add_car_case_draft(
    *,
    merged_text: str,
    collected_fields: list[str] | None,
    still_needed_fields: list[str] | None,
    primary_vehicle_summary: str | None,
    quote_ready_status: str,
    human_confirmation_fields: list[str] | None,
    issue_category: str,
    language: str,
) -> dict[str, Any]:
    """Structured draft for add-car service_type paths."""
    collected = _norm_list(list(collected_fields or []))
    missing = _norm_list(list(still_needed_fields or []))
    known: dict[str, Any] = {}
    for fid in collected:
        fl = fid.lower()
        conf = 0.92 if fl not in _HIGH_RISK_SLOT_IDS else 0.78
        known[fid] = {"confidence": conf, "source": "session_extract_or_persisted"}
    inferred: dict[str, Any] = {}
    pvc = (primary_vehicle_summary or "").strip()
    if pvc and any(
        m in missing
        for m in ("year", "make_model", "model", "vin")
    ):
        inferred["vehicle_guess"] = {
            "hint": pvc,
            "confidence": 0.55,
            "needs_confirmation": True,
        }

    confidence_map: dict[str, float] = {k: float(v["confidence"]) for k, v in known.items()}
    for k, v in inferred.items():
        confidence_map[f"inferred:{k}"] = float(v.get("confidence") or 0.0)

    needs_confirmation: list[str] = []
    for k, v in inferred.items():
        if v.get("needs_confirmation"):
            needs_confirmation.append(k)
    for h in human_confirmation_fields or []:
        hs = str(h).strip()
        if hs and hs not in needs_confirmation:
            needs_confirmation.append(hs)

    # Completion messaging (1–2 short lines; UI may show near progress)
    n_miss = len(missing)
    is_zh = (language or "").strip().lower() == "zh"
    if n_miss == 0:
        completion_zh = "关键项已齐：可按系统提示完成最后一步。"
        completion_en = "Core fields look complete—finish the last step shown above."
    elif n_miss == 1:
        lab = missing[0].replace("_", " ")
        completion_zh = f"还差 1 项（{lab}），补完即可进入下一步。"
        completion_en = f"One item left ({lab}); add it to move forward."
    else:
        completion_zh = f"还差 {n_miss} 项要点；按上方提示一次补一项即可。"
        completion_en = f"{n_miss} items still needed—follow the prompt above one step at a time."

    return {
        "lane": "add_car",
        "intent": _intent_key((merged_text or "").lower(), issue_category or ""),
        "known_fields": known,
        "inferred_fields": inferred,
        "missing_fields": missing,
        "confidence_map": confidence_map,
        "needs_confirmation": needs_confirmation,
        "quote_ready_status": quote_ready_status,
        "completion_message": completion_zh if is_zh else completion_en,
        "completion_fraction": _completion_fraction(collected, missing),
    }


def build_generic_case_draft(
    *,
    merged_text: str,
    issue_category: str,
    language: str,
) -> dict[str, Any]:
    """Lightweight draft for non–add-car turns (intent + thread signal only)."""
    lowered = (merged_text or "").lower()
    is_zh = (language or "").strip().lower() == "zh"
    return {
        "lane": "generic",
        "intent": _intent_key(lowered, issue_category or ""),
        "known_fields": {},
        "inferred_fields": {},
        "missing_fields": [],
        "confidence_map": {},
        "needs_confirmation": [],
        "quote_ready_status": "",
        "completion_message": (
            "已收到您的说明，办公室会按类别整理并跟进。"
            if is_zh
            else "Got it—our office will triage and follow up."
        ),
        "completion_fraction": None,
    }


def _completion_fraction(collected: list[str], missing: list[str]) -> float | None:
    keys = {
        "year",
        "make_model",
        "vin",
        "zip",
        "delivery_date",
        "primary_driver",
        "name",
        "phone",
    }
    coll = {str(x).lower() for x in collected}
    miss = {str(x).lower() for x in missing}
    # map aliases
    if "make_model" in coll or "model" in coll:
        coll.add("make_model")
    relevant = keys & (coll | miss)
    if not relevant:
        return None
    done = len([k for k in relevant if k in coll and k not in miss])
    return round(done / max(len(relevant), 1), 3)


def augment_next_ask_with_variant(
    ask: str | None,
    *,
    variant: str,
    language: str,
    primary_vehicle_summary: str | None,
    fields: dict[str, bool],
) -> str | None:
    """
    Adjust add-car next ask for variant B (shorter). C is handled in triage vehicle branch.
    """
    if not (ask or "").strip():
        return ask
    v = (variant or "A").strip().upper()
    _ = primary_vehicle_summary, fields  # reserved for future merged asks
    is_zh = (language or "").strip().lower() == "zh"

    if v == "B":
        # Tighter single-line nudge (aggressive brevity)
        one_line = ask.replace("\n", " ").strip()
        one_line = re.sub(r"\s+", " ", one_line)
        if len(one_line) > 120:
            cut = one_line[:117].rsplit(" ", 1)[0] if not is_zh else one_line[:117]
            one_line = cut + ("…" if is_zh else "…")
        return one_line

    return ask
