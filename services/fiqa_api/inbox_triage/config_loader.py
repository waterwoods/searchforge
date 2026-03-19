"""
Unified Intake config loader — loads industry and client config from configs/.

Load order: common (future) → industry → client.
- Industry: markers, reply_templates.
- Client: handoff_phrases, reply_overrides (merged into industry templates).
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


def get_reply_templates() -> dict[str, Any]:
    """
    Load reply templates: industry base + client overrides.

    Load order:
    1. Industry: configs/industries/insurance/reply_templates.json (base)
    2. Client: configs/clients/chen_kui/reply_overrides.json (shallow merge per key)

    Returns {"add_car": {"zh": "...", "en": "..."}, "missing_document": {...}, ...}.
    Falls back to empty dict if industry missing.
    """
    industry = _load_json("configs/industries/insurance/reply_templates.json")
    if not industry or "templates" not in industry:
        return {}
    templates = dict(industry.get("templates", {}))
    client = _load_json("configs/clients/chen_kui/reply_overrides.json")
    if client and isinstance(client.get("overrides"), dict):
        for key, override in client["overrides"].items():
            if isinstance(override, dict) and override:
                templates[key] = {**templates.get(key, {}), **override}
    return templates


# Defaults for add_car next-step prompts (used when config missing)
_ADD_CAR_RULES_DEFAULTS: dict[str, dict[str, str]] = {
    "ask_vehicle": {
        "zh": "先把年份和车型发我，我就能帮你算。",
        "en": "Send me the year and make/model first so I can run the quote.",
    },
    "ask_zip": {
        "zh": "先把地址邮编发我，我就能帮你算。",
        "en": "Send me the zip or address first and I will run the quote.",
    },
    "ask_delivery_driver": {
        "zh": "提车日期和主要驾驶人发我一下，我好安排报价。",
        "en": "Send me the delivery date and main driver so I can prepare the quote.",
    },
}


def get_add_car_rules() -> dict[str, dict[str, str]]:
    """
    Load Add-Car Quote next-step prompts from configs/industries/insurance/add_car_rules.json.
    Returns {"ask_vehicle": {"zh": "...", "en": "..."}, "ask_zip": {...}, "ask_delivery_driver": {...}}.
    Falls back to hardcoded defaults when config missing.
    """
    data = _load_json("configs/industries/insurance/add_car_rules.json")
    if not data:
        return dict(_ADD_CAR_RULES_DEFAULTS)
    out: dict[str, dict[str, str]] = {}
    for key in ("ask_vehicle", "ask_zip", "ask_delivery_driver"):
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
    Only persists when running locally with writable config dir.
    """
    path = _REPO_ROOT / "configs/industries/insurance/add_car_rules.json"
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
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        logger.warning("Could not save add_car_rules.json (may be read-only): %s", e)
        raise


def get_active_client_id() -> str:
    """
    Return active client ID from CLIENT_ID env or default.
    Used by API to select which client config to serve.
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
    for key in ("app_title", "office_label", "office_workbench", "talk_to_agent_label",
                "talk_to_agent_starter", "handoff_default", "welcome_highlight", "welcome_hint"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            out[key] = val.strip()
    qsb = data.get("quick_start_buttons")
    if isinstance(qsb, dict) and qsb:
        out["quick_start_buttons"] = qsb
    return out
