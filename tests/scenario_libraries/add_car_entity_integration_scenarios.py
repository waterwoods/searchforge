"""
Add-car × vehicle entity memory integration scenarios (multi-turn, session-scoped).

Loaded by scripts/run_add_car_cplus_scenario_library.py (--library-path).
Requires SERVICE_RECORD_DATABASE_URL / Stage-1 DB for full entity readback; without DB,
assertions still hold via heuristic fallback where marked.
"""
from __future__ import annotations

from typing import Any


def _sc(
    sid: str,
    category: str,
    description: str,
    user_turns: list[str],
    risk_tags: list[str],
    assertions: list[dict[str, Any]],
    *,
    soft_route: str | None = None,
    reply_truth_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": sid,
        "category": category,
        "description": description,
        "user_turns": user_turns,
        "expected_risk_tags": risk_tags,
        "assertions": assertions,
    }
    if soft_route:
        row["soft_route"] = soft_route
    if reply_truth_context:
        row["reply_truth_context"] = reply_truth_context
    return row


def _last(*checks: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"turn": -1, "checks": list(checks)}]


def _eq(field: str, value: Any) -> dict[str, Any]:
    return {"op": "eq", "field": field, "value": value}


def _contains(field: str, value: str) -> dict[str, Any]:
    return {"op": "contains", "field": field, "value": value}


SCENARIOS: list[dict[str, Any]] = []

# --- A. Correction stability: Camry → 2020 → 2021 → VIN ---
SCENARIOS.append(
    _sc(
        "ent_corr_stability_vin",
        "entity_correction",
        "Year/model corrections then VIN; final summary should reflect latest truth",
        [
            "I want to add a Toyota Camry, garaging ZIP 94103, picking up next Friday, I'm the primary driver.",
            "Actually it's a 2020 Camry.",
            "Sorry — 2021, not 2020.",
            "VIN is 1HGBH41JXMN109186.",
        ],
        ["correction_chain", "vin"],
        _last(
            _eq("service_type", "add_car"),
            _contains("primary_vehicle_summary", "2021"),
            _contains("vehicle_key", "vin:"),
        ),
    )
)

# --- B. Identity switching + re-anchor to first vehicle ---
SCENARIOS.append(
    _sc(
        "ent_identity_switch_first",
        "entity_identity",
        "Switch to Tesla then explicitly re-anchor to first car (Camry)",
        [
            "Adding a 2020 Toyota Camry, ZIP 90210, pickup Friday, I drive.",
            "Wait — change that to a 2022 Tesla Model Y, same ZIP and pickup.",
            "Use the first car I mentioned for the quote please.",
        ],
        ["identity_switch", "first_anchor"],
        _last(
            _eq("service_type", "add_car"),
            _contains("primary_vehicle_summary", "Camry"),
            _contains("primary_vehicle_summary", "2020"),
        ),
    )
)

# --- C. Multi-vehicle noise: Camry + CR-V + ignore CR-V ---
SCENARIOS.append(
    _sc(
        "ent_multi_noise_ignore_crv",
        "entity_multi",
        "Mention CR-V noise then scope to Camry only",
        [
            "I need to add my 2021 Toyota Camry, zip 94608, delivery March 5, I'm the driver.",
            "Also we talked about a Honda CR-V but ignore that — only the Camry for this add.",
        ],
        ["multi_vehicle", "ignore_sibling"],
        _last(
            _eq("service_type", "add_car"),
            _contains("primary_vehicle_summary", "Camry"),
            _contains("primary_vehicle_summary", "2021"),
        ),
    )
)

# --- D. Long drift (10 turns) ---
_drift_turns = [
    "Hey, I want to add a new car.",
    "It's for my household.",
    "California, bay area.",
    "Toyota Camry.",
    "2021 model.",
    "Garaging zip is 95123.",
    "Delivery is April 28.",
    "I'm the main driver.",
    "Let me know what else you need.",
    "That's everything for the Camry add.",
]
SCENARIOS.append(
    _sc(
        "ent_long_drift_10",
        "entity_drift",
        "Ten-turn sparse add-car thread; primary vehicle should remain Camry 2021",
        _drift_turns,
        ["long_thread"],
        _last(
            _eq("service_type", "add_car"),
            _contains("primary_vehicle_summary", "Camry"),
            _contains("primary_vehicle_summary", "2021"),
        ),
    )
)

# --- E. Emotional + correction ---
SCENARIOS.append(
    _sc(
        "ent_emotional_correction",
        "entity_emotion",
        "Frustrated tone with explicit year correction",
        [
            "Ugh I need to add a car this is confusing.",
            "2020 Honda CR-V, zip 92101, I pick up Tuesday, I drive — happy now?",
            "NOT 2020 — it's 2019 CR-V.",
        ],
        ["emotion", "correction"],
        _last(
            _eq("service_type", "add_car"),
            _contains("primary_vehicle_summary", "2019"),
            _contains("primary_vehicle_summary", "CR-V"),
        ),
    )
)

# --- Loop 2: harder chains ---
SCENARIOS.append(
    _sc(
        "ent_flip_flop_year_final",
        "entity_hard",
        "Multiple year edits; final comma-style correction before VIN",
        [
            "Add a Toyota Camry, zip 94102, Friday pickup, I drive.",
            "Year is 2020.",
            "Wait make that 2022.",
            "Actually 2023, not 2022.",
            "VIN 2HGFC2F59KH123456.",
        ],
        ["year_chain"],
        _last(
            _eq("service_type", "add_car"),
            _contains("primary_vehicle_summary", "2023"),
            _contains("vehicle_key", "vin:"),
        ),
    )
)

SCENARIOS.append(
    _sc(
        "ent_zh_year_comma_not",
        "entity_hard",
        "Chinese thread with comma year correction",
        [
            "我要加一台2020丰田凯美瑞，邮编95014，下周五提车，主要我自己开。",
            "年份写错了，是2021，不是2020。",
        ],
        ["zh", "correction"],
        _last(
            _eq("service_type", "add_car"),
            _contains("primary_vehicle_summary", "2021"),
        ),
    )
)
