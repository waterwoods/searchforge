"""
Unified Intake config loader — loads industry and client config from configs/.

Load order: common (future) → industry → client.
- Industry: markers, reply_templates.
- Client: handoff_phrases; reply_overrides merged into industry templates per client_id (no cross-client fallback).
Falls back to hardcoded defaults when config files are missing.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]

# Default client when CLIENT_ID env not set
_DEFAULT_CLIENT_ID = "chen_kui"


def _load_json(rel_path: str) -> dict[str, Any] | None:
    """Load JSON from configs/ relative to repo root. Returns None if missing or invalid."""
    path = _REPO_ROOT / rel_path
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Failed to load config {rel_path}: {e}")
        return None


def get_insurance_markers() -> dict[str, tuple[str, ...]]:
    """
    Load intent markers from configs/industries/insurance/markers.json.
    Returns dict mapping marker set name -> tuple of strings.
    Falls back to empty dict if file missing (caller must handle).
    """
    data = _load_json("configs/industries/insurance/markers.json")
    if not data:
        return {}
    out: dict[str, tuple[str, ...]] = {}
    for key, value in data.items():
        if key in ("version", "description"):
            continue
        if key == "document_items":
            continue  # Handled separately
        if isinstance(value, list) and all(isinstance(x, str) for x in value):
            out[key] = tuple(value)
    return out


def get_document_item_markers() -> tuple[tuple[tuple[str, ...], str, str], ...]:
    """
    Load document item markers from configs/industries/insurance/markers.json.
    Returns tuple of (markers_tuple, english_label, chinese_label).
    Falls back to empty tuple if missing.
    """
    data = _load_json("configs/industries/insurance/markers.json")
    if not data or "document_items" not in data:
        return ()
    items = data["document_items"]
    if not isinstance(items, list):
        return ()
    result: list[tuple[tuple[str, ...], str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        markers = item.get("markers")
        en_label = item.get("english_label", "")
        zh_label = item.get("chinese_label", "")
        if isinstance(markers, list) and all(isinstance(m, str) for m in markers):
            result.append((tuple(markers), en_label, zh_label))
    return tuple(result)


def get_handoff_phrases(client_id: str | None = None) -> dict[str, dict[str, str]]:
    """
    Load handoff phrases from configs/clients/<client_id>/handoff_phrases.json.
    Returns {"add_car": {"zh": "...", "en": "..."}, "other": {"zh": "...", "en": "..."}}.
    Falls back to chen_kui if client config missing; empty dict if both missing.
    """
    cid = (client_id or "").strip() or get_active_client_id()
    data = _load_json(f"configs/clients/{cid}/handoff_phrases.json")
    if not data or "handoff" not in data:
        if cid != _DEFAULT_CLIENT_ID:
            data = _load_json(f"configs/clients/{_DEFAULT_CLIENT_ID}/handoff_phrases.json")
        if not data or "handoff" not in data:
            return {}
    handoff = data.get("handoff", {})
    if not isinstance(handoff, dict):
        return {}
    return {k: v for k, v in handoff.items() if isinstance(v, dict)}


def get_stitched_handoff_phrases(client_id: str | None = None) -> dict[str, Any]:
    """
    Load optional stitched customer-visible phrases from the same file as handoff_phrases.

    Expected top-level key "stitched" on configs/clients/<client_id>/handoff_phrases.json.
    Shapes (all optional):
      - add_car_materials_sent: {\"zh\": \"...\", \"en\": \"...\"}
      - why_still_chasing_reassurance: {\"zh\": \"...\", \"en\": \"...\"}
      - prospective_send: {\"zh_wechat\", \"zh_screenshot\", \"zh_bundle\", \"en_wechat\", ...}
      - append_boundary: customer-visible append / new-issue / borderline wording (merged over
        engine defaults in triage._apply_append_case_boundary). Subkeys (all optional):
        continuity_zh: {add_car, claim, remove_car, payment, missing_doc, premium, generic}
        new_issue_tail_zh: {claim, billing, remove_car, premium, add_car, default}
        continuity_en_add_car, continuity_en_other (strings)
        new_issue_tail_en: {claim, billing, remove_car, premium, add_car, default}
        add_car_split_hint_zh, add_car_split_hint_en, borderline_zh, borderline_en
      - add_car_price_caveat: {\"zh\", \"en\"} — appended when add-car flow mentions ballpark/cheaper premium
      - document_already_sent_tail: {\"zh\", \"en\"} — appended for payment/premium mixed-intent when the
        customer says materials were already sent
      - handoff_doc_clarification_suffix_add_car: {\"zh\", \"en\"} — suffix after add-car
        doc clarification when the case is handoff-ready
      - handoff_doc_clarification_suffix_other: {\"zh\", \"en\"} — suffix after non-add-car
        doc clarification when the case is handoff-ready
      - handoff_add_car_coverage_answer: {\"zh\", \"en\"} — short response to add-car
        coverage-adjust side question
      - handoff_add_car_coverage_suffix: {\"zh\", \"en\"} — handoff suffix after
        add-car coverage side question
      - handoff_payment_correction_urgency: {\"zh\", \"en\"} — correction+urgency answer
        when payment/cancellation is handoff-ready
      - handoff_add_car_contact_gap_tail: {\"zh\", \"en\"} — appended when add-car is quote-ready
        but name/phone are still missing on the record (truthful completeness). Engine may shorten
        or skip repeating this tail by intent and prior-thread count (see master outline §4.10).

    Client `handoff` entries may also include per-family add-car keys: `add_car_supplement`,
    `add_car_timeline`, `add_car_quote_detail`, `add_car_correction`, plus optional `zh_alt` /
    `en_alt` on `add_car` for bounded turn-based variety.

    Post–formal-submit Add-Car routing: optional parallel keys `add_car_submitted`,
    `add_car_supplement_submitted`, `add_car_timeline_submitted`, `add_car_quote_detail_submitted`,
    `add_car_correction_submitted` (same zh/en shape). Stitched optional: `add_car_clarification_followup_submitted`,
    `handoff_doc_clarification_suffix_add_car_submitted`, `handoff_add_car_coverage_suffix_submitted`,
    `add_car_materials_sent_submitted`.

    No cross-client fallback — missing keys use engine defaults in triage.py (avoids Chen Kui bleed).
    """
    cid = (client_id or "").strip() or get_active_client_id()
    data = _load_json(f"configs/clients/{cid}/handoff_phrases.json")
    if not data or not isinstance(data, dict):
        return {}
    stitched = data.get("stitched")
    return stitched if isinstance(stitched, dict) else {}


def get_workflow_fallbacks() -> dict[str, str]:
    """
    Load common workflow fallbacks from configs/common/workflow_defaults.json.
    Returns {"broker_next_step": "...", "client_prep": "...", "client_reply_draft": "..."}.
    Falls back to empty dict if missing.
    """
    data = _load_json("configs/common/workflow_defaults.json")
    if not data or "fallbacks" not in data:
        return {}
    fallbacks = data.get("fallbacks", {})
    if not isinstance(fallbacks, dict):
        return {}
    return {k: (v or "").strip() for k, v in fallbacks.items() if isinstance(v, str)}


_WORKBENCH_ACTIVITY_DEFAULTS: dict[str, str] = {
    "prefix": "工作台：",
    "mark_test_on": "标记为测试",
    "mark_test_off": "取消测试标记",
    "archive_on": "已归档隐藏",
    "archive_off": "取消归档",
    "generic_update": "更新",
}


def get_workbench_activity_copy() -> dict[str, str]:
    """
    Broker-visible workbench activity lines (case_activity) — keep wording in config, not code.

    Load: configs/common/workbench_activity_copy.json (optional). Unknown keys fall back to
    _WORKBENCH_ACTIVITY_DEFAULTS. Per-client overrides belong in future client packs if needed.
    """
    data = _load_json("configs/common/workbench_activity_copy.json")
    out = dict(_WORKBENCH_ACTIVITY_DEFAULTS)
    if not data or not isinstance(data, dict):
        return out
    for key in _WORKBENCH_ACTIVITY_DEFAULTS:
        raw = data.get(key)
        if isinstance(raw, str) and raw.strip():
            out[key] = raw.strip()
    return out


def get_category_templates() -> dict[str, dict[str, str]]:
    """
    Load per-category broker_next_step and client_prep from configs/industries/insurance/category_templates.json.
    Returns {"cancellation_warning": {"broker_next_step": "...", "client_prep": "..."}, ...}.
    Categories with client_prep="dynamic" (e.g. missing_document) keep dynamic logic in triage.
    Falls back to empty dict if missing.
    """
    data = _load_json("configs/industries/insurance/category_templates.json")
    if not data or "categories" not in data:
        return {}
    categories = data.get("categories", {})
    if not isinstance(categories, dict):
        return {}
    out: dict[str, dict[str, str]] = {}
    for key, val in categories.items():
        if isinstance(val, dict) and val:
            bns = (val.get("broker_next_step") or "").strip()
            cp = (val.get("client_prep") or "").strip()
            out[key] = {"broker_next_step": bns, "client_prep": cp}
    return out


def get_reply_templates(client_id: str | None = None) -> dict[str, Any]:
    """
    Load reply templates: industry base + optional client overrides.

    Load order:
    1. Industry: configs/industries/insurance/reply_templates.json (base)
    2. Client: configs/clients/<client_id>/reply_overrides.json (shallow merge per key)

    Overrides are merged only when that client's file exists and contains an "overrides"
    object (no cross-client fallback — avoids applying one broker's wording to another).

    Returns {"add_car": {"zh": "...", "en": "..."}, "missing_document": {...}, ...}.
    Falls back to empty dict if industry missing.
    """
    industry = _load_json("configs/industries/insurance/reply_templates.json")
    if not industry or "templates" not in industry:
        return {}
    templates = dict(industry.get("templates", {}))
    cid = (client_id or "").strip() or get_active_client_id()
    client = _load_json(f"configs/clients/{cid}/reply_overrides.json")
    if client and isinstance(client.get("overrides"), dict):
        for key, override in client["overrides"].items():
            if isinstance(override, dict) and override:
                templates[key] = {**templates.get(key, {}), **override}
    return templates


# Defaults for add_car next-step prompts (used when config missing)
_ADD_CAR_RULES_DEFAULTS: dict[str, dict[str, str]] = {
    "ask_vehicle": {
        "zh": "年份和车型发我，我好继续报价。",
        "en": "Send year and make/model so I can run the quote.",
    },
    "ask_zip": {
        "zh": "邮编发我一下，我好往下报价。",
        "en": "Send the zip so I can run the quote.",
    },
    "ask_delivery_driver": {
        "zh": "提车日和主要驾驶人发我一下，我好安排报价。",
        "en": "Send me the delivery date and main driver so I can prepare the quote.",
    },
    "ask_driver_only": {
        "zh": "主要驾驶人发我一下，我好安排报价。",
        "en": "Send me the main driver so I can prepare the quote.",
    },
}


_ADD_CAR_RULE_KEYS = ("ask_vehicle", "ask_zip", "ask_delivery_driver", "ask_driver_only")


def get_add_car_rules() -> dict[str, dict[str, str]]:
    """
    Load Add-Car Quote next-step prompts from configs/industries/insurance/add_car_rules.json.
    Returns ask_vehicle, ask_zip, ask_delivery_driver, ask_driver_only (zh/en each).
    Falls back to hardcoded defaults when config missing or key absent.
    """
    data = _load_json("configs/industries/insurance/add_car_rules.json")
    if not data:
        return dict(_ADD_CAR_RULES_DEFAULTS)
    out: dict[str, dict[str, str]] = {}
    for key in _ADD_CAR_RULE_KEYS:
        val = data.get(key)
        if isinstance(val, dict) and val:
            zh = (val.get("zh") or "").strip()
            en = (val.get("en") or "").strip()
            out[key] = {
                "zh": zh or _ADD_CAR_RULES_DEFAULTS[key]["zh"],
                "en": en or _ADD_CAR_RULES_DEFAULTS[key]["en"],
            }
        else:
            out[key] = dict(_ADD_CAR_RULES_DEFAULTS[key])
    return out


def can_publish_add_car_rules() -> bool:
    """
    Check if config directory is writable (e.g. local dev vs Cloud Run read-only).
    Used by Rules Center to show/hide publish button honestly.
    """
    path = _REPO_ROOT / "configs/industries/insurance/add_car_rules.json"
    test_file = path.parent / ".write_test_tmp"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test")
        test_file.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def save_add_car_rules(rules: dict[str, dict[str, str]]) -> None:
    """
    Save Add-Car Quote next-step prompts to configs/industries/insurance/add_car_rules.json.
    Preserves ask_driver_only from disk when the publish payload omits it (Rules Center edits three keys).
    Only persists when running locally with writable config dir.
    """
    path = _REPO_ROOT / "configs/industries/insurance/add_car_rules.json"
    existing = _load_json("configs/industries/insurance/add_car_rules.json") or {}
    data: dict[str, Any] = {
        "version": "1",
        "description": "Add-Car Quote next-step prompts. Editable by business users via Rules Center.",
    }
    for key in ("ask_vehicle", "ask_zip", "ask_delivery_driver"):
        val = rules.get(key)
        if isinstance(val, dict):
            data[key] = {"zh": (val.get("zh") or "").strip(), "en": (val.get("en") or "").strip()}
        else:
            data[key] = dict(_ADD_CAR_RULES_DEFAULTS.get(key, {"zh": "", "en": ""}))
    # Keep driver-only prompt unless explicitly included in rules (future API can pass it)
    if isinstance(rules.get("ask_driver_only"), dict):
        d = rules["ask_driver_only"]
        data["ask_driver_only"] = {"zh": (d.get("zh") or "").strip(), "en": (d.get("en") or "").strip()}
    elif isinstance(existing.get("ask_driver_only"), dict):
        ed = existing["ask_driver_only"]
        data["ask_driver_only"] = {
            "zh": (ed.get("zh") or "").strip(),
            "en": (ed.get("en") or "").strip(),
        }
    else:
        data["ask_driver_only"] = dict(_ADD_CAR_RULES_DEFAULTS["ask_driver_only"])
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        logger.warning("Could not save add_car_rules.json (may be read-only): %s", e)
        raise


# Defaults for soft-route reroute + starter replies (POST /api/inbox/triage).
# Overridden by configs/common/soft_route_inbox.json when present.
_SOFT_ROUTE_REROUTE_DEFAULTS: dict[str, str] = {
    "add_car": "看起来这是加车报价相关的问题，我先帮您处理这个。",
    "remove_car": "看起来这是保单变更相关的问题，我先帮您处理这个。",
    "claim_intake": "看起来这是事故理赔相关的问题，我先帮您处理这个。",
    "cancellation_warning": "看起来这是付款/取消相关的问题，我先帮您处理这个。",
    "missing_document": "看起来这是上传材料相关的问题，我先帮您处理这个。",
}
_SOFT_ROUTE_STARTER_DEFAULTS: dict[str, str] = {
    "add_car": "好的，我来帮您看新车报价。先把年份和车型发我，我就能帮你算。",
    "remove_car": "好的，可以处理。把卖车日期、车辆信息和是否已经过户发我，我先帮你确认。",
    "claim_intake": "先别慌，我先按事故来帮您处理。先把事故经过、现场照片和对方车牌发我，我帮你确认下一步怎么报案。",
    "cancellation_warning": "这像是付款问题。先把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。",
    "missing_document": "好的，材料补交我来帮您处理。把完整通知和要补的材料发我，我整理后尽快帮你回复。",
}


def get_soft_route_inbox_copy() -> tuple[dict[str, str], dict[str, str]]:
    """
    Load reroute_messages and soft_route_starter_replies for inbox triage soft_route handling.
    Merges configs/common/soft_route_inbox.json over code defaults (same strings by default).
    """
    reroute = dict(_SOFT_ROUTE_REROUTE_DEFAULTS)
    starters = dict(_SOFT_ROUTE_STARTER_DEFAULTS)
    data = _load_json("configs/common/soft_route_inbox.json")
    if not data or not isinstance(data, dict):
        return reroute, starters
    rm = data.get("reroute_messages")
    if isinstance(rm, dict):
        for k, v in rm.items():
            if isinstance(k, str) and isinstance(v, str) and v.strip():
                reroute[k] = v.strip()
    sr = data.get("soft_route_starter_replies")
    if isinstance(sr, dict):
        for k, v in sr.items():
            if isinstance(k, str) and isinstance(v, str) and v.strip():
                starters[k] = v.strip()
    return reroute, starters


def get_active_client_id() -> str:
    """
    Return active client ID from CLIENT_ID env or default.
    Used by API to select which client config to serve.

    Hot-plug boundary (add a client pack under configs/clients/<id>/):
    handoff_phrases.json, reply_overrides.json, ui_copy.json — selected by CLIENT_ID.
    Industry-wide behavior stays under configs/industries/; avoid per-client branches in core triage.
    """
    raw = os.environ.get("CLIENT_ID", "").strip()
    return raw if raw else _DEFAULT_CLIENT_ID


def get_ui_copy(client_id: str | None = None) -> dict[str, Any]:
    """
    Load client UI copy from configs/clients/<client_id>/ui_copy.json.
    Returns dict with app_title, office_label, office_workbench, handoff_default,
    welcome_highlight, welcome_hint, quick_start_buttons.
    Falls back to empty dict if missing (caller should use hardcoded fallbacks).
    """
    cid = (client_id or "").strip() or get_active_client_id()
    path = f"configs/clients/{cid}/ui_copy.json"
    data = _load_json(path)
    if not data or not isinstance(data, dict):
        return {}
    # Sanitize: only allow known keys, strip strings
    out: dict[str, Any] = {}
    for key in (
        "app_title",
        "office_label",
        "office_workbench",
        "talk_to_agent_label",
        "talk_to_agent_starter",
        "handoff_default",
        "welcome_highlight",
        "welcome_hint",
        # ADD_CAR_TRANSACTION_CLARITY_SPRINT — customer transaction identity + closure copy
        "add_car_transaction_title",
        "add_car_transaction_subtitle",
        "add_car_progress_card_title",
        "handoff_closure_headline_add_car",
        "handoff_closure_headline_generic",
        "handoff_closure_processing_add_car",
        "handoff_case_created_line",
        "handoff_case_pending_line",
        "handoff_new_issue_hint",
        "add_car_handoff_toast",
        "handoff_status_badge_add_car",
        "handoff_same_request_panel_title",
        "handoff_same_request_panel_intro",
        "handoff_same_request_placeholder",
        "handoff_same_request_submit",
        # ADD_CAR_CLEAR_SUBMISSION_CONFIRMATION_HANDOFF — closure snapshot + timing + first-turn CTA
        "handoff_received_summary_title_add_car",
        "handoff_received_summary_intro_add_car",
        "handoff_verify_with_office_note_add_car",
        "handoff_office_followup_timing_add_car",
        "customer_entry_submit_add_car",
        # SERVICE_ENTRY_PORTAL_CLARITY_SPRINT — portal hierarchy + labels
        "portal_brand_tagline",
        "portal_hero_title",
        "portal_service_tagline",
        "portal_empty_headline",
        "portal_empty_secondary",
        "portal_choose_path_label",
        "portal_thread_heading",
        "portal_customer_bubble_label",
        "portal_office_bubble_label",
        "portal_loading_status",
        "portal_progress_annotation",
        "portal_generic_progress_title",
        "portal_submit_followup",
        "portal_add_car_quick_title",
        "portal_add_car_quick_hint",
        "portal_add_car_quick_cta",
        "portal_session_restored_toast",
        "portal_closure_reply_summary_label",
        # ADD_CAR_TASK_FIRST_LESS_CHAT_FINAL_POLISH_SPRINT — post-handoff task-first chrome
        "portal_post_handoff_thread_heading",
        "portal_post_handoff_thread_hint",
        "portal_post_handoff_thread_collapse_label",
        "portal_post_handoff_next_section_label",
        "portal_post_handoff_closure_section_label",
        "portal_tab_customer_label",
        "portal_tab_customer_suffix",
        "portal_tab_office_suffix",
        "office_workbench_subtitle",
        "office_workbench_document_title",
        "office_workbench_recent_card_title",
        "office_workbench_recent_card_extra",
        "office_workbench_paste_card_title",
        "office_workbench_empty_queue_hint",
        "portal_input_placeholder_empty",
        "portal_input_placeholder_continue",
        # Quote-ready conversion layer (customer reply + portal chrome)
        "conversion_quote_ready_reply_zh",
        "conversion_quote_ready_reply_en",
        "conversion_ui_ready_title",
        "conversion_ui_next_line",
        "conversion_still_needed_collapse_label",
        # Intake evolution: A | B | C (questioning + confirmation style); overridable via INTAKE_EVOLUTION_VARIANT
        "intake_evolution_variant",
        # V6 auto-input: A=text-first, B=OCR+aggressive auto-fill, C=OCR+conservative confirmation
        "v6_auto_input_variant",
    ):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            out[key] = val.strip()
    qsb = data.get("quick_start_buttons")
    if isinstance(qsb, dict) and qsb:
        out["quick_start_buttons"] = qsb
    li = data.get("light_identity")
    if isinstance(li, dict):
        profile = str(li.get("binding_copy_profile") or "neutral").strip().lower() or "neutral"
        if profile not in ("wechat_preferred", "neutral"):
            profile = "neutral"
        mode = str(li.get("wechat_binding_mode") or "stub").strip().lower() or "stub"
        if mode not in ("stub", "live"):
            mode = "stub"
        li_out: dict[str, Any] = {
            "show_optional_binding": bool(li.get("show_optional_binding")),
            "binding_copy_profile": profile,
            "wechat_binding_mode": mode,
        }
        for optional_key in (
            "strip_primary_line",
            "wechat_cta_label",
            "defer_cta_label",
            "dismiss_cta_label",
            "modal_title",
            "modal_body",
            "phone_email_fallback_hint",
        ):
            v = li.get(optional_key)
            if isinstance(v, str) and v.strip():
                li_out[optional_key] = v.strip()
        out["light_identity"] = li_out
    return out


def get_intake_evolution_variant(client_id: str | None = None) -> str:
    """A = balanced (default), B = shorter / fewer clauses, C = confirmation-first vehicle check."""
    import os

    env = (os.environ.get("INTAKE_EVOLUTION_VARIANT") or "").strip().upper()
    if env in ("A", "B", "C"):
        return env
    ui = get_ui_copy(client_id)
    v = str(ui.get("intake_evolution_variant") or "A").strip().upper()
    if v in ("A", "B", "C"):
        return v
    return "A"


def get_v6_auto_input_variant(client_id: str | None = None) -> str:
    """V6 automatic input: A text-first, B OCR+aggressive fill, C OCR+conservative confirm."""
    import os

    env = (os.environ.get("V6_AUTO_INPUT_VARIANT") or "").strip().upper()
    if env in ("A", "B", "C"):
        return env
    ui = get_ui_copy(client_id)
    v = str(ui.get("v6_auto_input_variant") or "A").strip().upper()
    if v in ("A", "B", "C"):
        return v
    return "A"


def get_wechat_binding_mode_for_client(client_id: str | None) -> str:
    """Return stub | live from client-pack ui_copy.light_identity (default stub)."""
    ui = get_ui_copy(client_id)
    li = ui.get("light_identity") or {}
    if isinstance(li, dict):
        m = str(li.get("wechat_binding_mode") or "stub").strip().lower()
        if m == "live":
            return "live"
    return "stub"
