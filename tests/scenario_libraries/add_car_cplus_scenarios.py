"""
Reusable Add-Car C+ multi-turn scenario library for deterministic triage replay.

Loaded by scripts/run_add_car_cplus_scenario_library.py (importlib).
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
    return row


def _last(*checks: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"turn": -1, "checks": list(checks)}]


def _turn(idx: int, *checks: dict[str, Any]) -> dict[str, Any]:
    return {"turn": idx, "checks": list(checks)}


def _eq(field: str, value: Any) -> dict[str, Any]:
    return {"op": "eq", "field": field, "value": value}


def _contains(field: str, value: str) -> dict[str, Any]:
    return {"op": "contains", "field": field, "value": value}


def _not_contains(field: str, value: str) -> dict[str, Any]:
    return {"op": "not_contains", "field": field, "value": value}


def _not_regex(field: str, pattern: str) -> dict[str, Any]:
    return {"op": "not_regex", "field": field, "pattern": pattern}


def _in_list(field: str, value: str) -> dict[str, Any]:
    return {"op": "in_list", "field": field, "value": value}


def _excludes_still(field: str) -> dict[str, Any]:
    return {"op": "still_needed_excludes", "field": field}


SCENARIOS: list[dict[str, Any]] = []

# --- 1 normal_user ---
SCENARIOS.extend(
    [
        _sc(
            "ac_nu_01",
            "normal_user",
            "Single-turn complete EN add-car",
            [
                "I want to add a 2022 Honda Accord, garaging ZIP 94506, picking up next Tuesday, I am the primary driver."
            ],
            ["tier1", "handoff"],
            _last(
                _eq("service_type", "add_car"),
                _eq("case_usable", True),
                _not_regex("client_reply_draft", r"\$\s*[0-9]"),
            ),
        ),
        _sc(
            "ac_nu_02",
            "normal_user",
            "Single-turn complete ZH Camry",
            [
                "我要加一台2021丰田凯美瑞，邮编95014，这周五提车，主要我自己开。"
            ],
            ["tier1", "zh"],
            _last(
                _eq("service_type", "add_car"),
                _eq("case_usable", True),
                _contains("primary_vehicle_summary", "2021"),
            ),
        ),
        _sc(
            "ac_nu_03",
            "normal_user",
            "Two-turn: opener then details",
            [
                "Hi, I need to add a new car to my policy.",
                "2023 Mazda CX-5, zip 92618, delivery March 20, my spouse is the primary driver.",
            ],
            ["multi_turn"],
            _last(
                _eq("service_type", "add_car"),
                _eq("case_usable", True),
                _contains("primary_vehicle_summary", "CX-5"),
            ),
        ),
        _sc(
            "ac_nu_04",
            "normal_user",
            "Two-turn ZH CR-V",
            [
                "想加新车报价。",
                "2022本田CR-V，邮编90210，下周提车，我本人开。",
            ],
            ["zh", "handoff"],
            _last(
                _eq("service_type", "add_car"),
                _eq("case_usable", True),
                _contains("primary_vehicle_summary", "CR-V"),
            ),
        ),
    ]
)

# --- 2 messy_uncertain ---
SCENARIOS.extend(
    [
        _sc(
            "ac_ms_01",
            "messy_uncertain",
            "Hedging and filler words",
            [
                "umm so like I think we're buying a car?? maybe",
                "ok it's a 2020 Toyota Camry, 94103, picking up end of month, I drive it mostly",
            ],
            ["clarity"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "Camry")),
        ),
        _sc(
            "ac_ms_02",
            "messy_uncertain",
            "Incomplete first turn then salvage",
            [
                "new car insurance thing",
                "2024 Accord, ZIP is 95131, delivery next Friday, primary driver is me",
            ],
            ["recovery"],
            _last(_eq("service_type", "add_car"), _eq("case_usable", True)),
        ),
        _sc(
            "ac_ms_03",
            "messy_uncertain",
            "Thread noise with real signal last",
            [
                "sorry wrong chat",
                "ignore that — add car 2019 Honda Civic 92780 this Saturday wife drives",
            ],
            ["noise"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "Civic")),
        ),
        _sc(
            "ac_ms_04",
            "messy_uncertain",
            "ZH fragmented",
            [
                "那个车险",
                "加车，2023凯美瑞，92620，下周三提车，我开。",
            ],
            ["zh"],
            _last(_eq("service_type", "add_car"), _eq("case_usable", True)),
        ),
    ]
)

# --- 3 correction_heavy ---
SCENARIOS.extend(
    [
        _sc(
            "ac_ch_01",
            "correction_heavy",
            "Multiple inline corrections same turn",
            [
                "Add car: 2020 Camry, zip 90210, delivery April 1, I drive — wait zip is 90211 not 90210, and delivery is April 3.",
            ],
            ["correction", "zip"],
            _last(
                _eq("service_type", "add_car"),
                _in_list("collected_fields", "zip"),
            ),
        ),
        _sc(
            "ac_ch_02",
            "correction_heavy",
            "Turn-level corrections",
            [
                "2021 Accord 95014 pickup Monday I drive",
                "Correction: pickup is Wednesday not Monday.",
                "Also ZIP should be 95015.",
            ],
            ["multi_correction"],
            _last(
                _eq("service_type", "add_car"),
                _in_list("collected_fields", "zip"),
            ),
        ),
        _sc(
            "ac_ch_03",
            "correction_heavy",
            "ZH last correction wins",
            [
                "加车2022思域，邮编94105，周五提车，我开",
                "不对，提车是周六。",
            ],
            ["zh", "correction"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "2022")),
        ),
    ]
)

# --- 4 year_correction ---
SCENARIOS.extend(
    [
        _sc(
            "ac_yr_01",
            "year_correction",
            "Explicit year swap",
            [
                "Add a 2018 Toyota Camry, 92612, next week delivery, I am primary.",
                "Sorry it's a 2020 Camry not 2018.",
            ],
            ["year"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2020"),
                _not_contains("primary_vehicle_summary", "2018"),
            ),
        ),
        _sc(
            "ac_yr_02",
            "year_correction",
            "ZH year fix",
            [
                "加2021雅阁，92801，下月提车，我开",
                "年份说错了，是2023雅阁。",
            ],
            ["zh", "year"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "2023")),
        ),
        _sc(
            "ac_yr_03",
            "year_correction",
            "Model year in second turn only",
            [
                "I bought a Honda Accord, zip 94587, I drive, picking up Sunday.",
                "Year is 2022.",
            ],
            ["partial_then_complete"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "2022")),
        ),
        _sc(
            "ac_yr_04",
            "year_correction",
            "Two year flips",
            [
                "2024 F-150, 95350, Friday, I drive",
                "Actually 2023 F-150.",
                "Wait dealer said 2024 again — keep 2024.",
            ],
            ["flip"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "2024")),
        ),
    ]
)

# --- 5 make_model_correction ---
SCENARIOS.extend(
    [
        _sc(
            "ac_mm_01",
            "make_model_correction",
            "Make/model swap",
            [
                "2022 Toyota Camry LE, 90025, next week, I drive",
                "It's a Camry XSE not LE.",
            ],
            ["trim"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "Camry")),
        ),
        _sc(
            "ac_mm_02",
            "make_model_correction",
            "Wrong model family",
            [
                "Adding 2021 Honda Civic, 95120, Monday, I drive",
                "Sorry Accord not Civic.",
            ],
            ["model"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "Accord")),
        ),
        _sc(
            "ac_mm_03",
            "make_model_correction",
            "ZH model correction",
            [
                "加2020丰田RAV4，邮编94080，周五提车，我开",
                "车型说错，是汉兰达。",
            ],
            ["zh"],
            _last(_eq("service_type", "add_car")),
        ),
        _sc(
            "ac_mm_04",
            "make_model_correction",
            "Mach-E trim clarification",
            [
                "2023 Ford Mustang Mach-E, 94608, March 12 pickup, I drive",
                "Premium trim if it matters.",
            ],
            ["edge_trim"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Mach-E"),
            ),
        ),
    ]
)

# --- 6 vin_correction ---
SCENARIOS.extend(
    [
        _sc(
            "ac_vn_01",
            "vin_correction",
            "VIN replace",
            [
                "Add car 2020 Camry 90210 Friday I drive VIN 1HGCM82633A004352",
                "VIN typo — correct VIN is 1HGCM82633A004353",
            ],
            ["vin"],
            _last(_eq("service_type", "add_car")),
        ),
        _sc(
            "ac_vn_02",
            "vin_correction",
            "VIN later then provided",
            [
                "2022 Accord zip 95131 Tuesday I drive, VIN coming",
                "VIN is 1HGCV1F34LA000001",
            ],
            ["vin_deferred"],
            _last(_eq("service_type", "add_car")),
        ),
        _sc(
            "ac_vn_03",
            "vin_correction",
            "ZH VIN update",
            [
                "加车2021凯美瑞95132周五我开，车架号晚点发",
                "车架号：1HGCV1F34LA000002",
            ],
            ["zh", "vin"],
            _last(_eq("service_type", "add_car")),
        ),
    ]
)

# --- 7 driver_correction ---
SCENARIOS.extend(
    [
        _sc(
            "ac_dr_01",
            "driver_correction",
            "Primary driver swap",
            [
                "2023 CX-5, 92620, March 1, I am primary driver",
                "Primary driver should be my husband, not me.",
            ],
            ["driver"],
            _last(_eq("service_type", "add_car")),
        ),
        _sc(
            "ac_dr_02",
            "driver_correction",
            "ZH driver change",
            [
                "2020雅阁92802周五提车，我开",
                "主驾驶人改成我老婆。",
            ],
            ["zh"],
            _last(_eq("service_type", "add_car")),
        ),
        _sc(
            "ac_dr_03",
            "driver_correction",
            "Joint then single driver",
            [
                "2024 CR-V 94110 Saturday both me and spouse drive",
                "Actually only I drive for insurance purposes.",
            ],
            ["driver"],
            _last(_eq("service_type", "add_car")),
        ),
    ]
)

# --- 8 documents_already_sent ---
SCENARIOS.extend(
    [
        _sc(
            "ac_doc_01",
            "documents_already_sent",
            "Claims docs sent on WeChat",
            [
                "Add 2021 Camry 90210 next week I drive",
                "I already sent the registration photos on WeChat yesterday.",
            ],
            ["already_sent", "materials"],
            _last(
                _eq("service_type", "add_car"),
                _eq("follow_up_type", "already_sent"),
            ),
        ),
        _sc(
            "ac_doc_02",
            "documents_already_sent",
            "ZH materials uploaded",
            [
                "加车2022思域95128周五我开",
                "材料我发你微信了。",
            ],
            ["zh", "already_sent"],
            _last(_eq("service_type", "add_car"), _eq("follow_up_type", "already_sent")),
        ),
        _sc(
            "ac_doc_03",
            "documents_already_sent",
            "Declaration page sent",
            [
                "Add car: 2023 Ford Mustang Mach-E, 94117, March 8, I drive",
                "I emailed you the declaration page already.",
            ],
            ["already_sent"],
            _last(_eq("service_type", "add_car"), _eq("follow_up_type", "already_sent")),
        ),
        _sc(
            "ac_doc_04",
            "documents_already_sent",
            "Does not claim already_sent on first turn",
            [
                "Add car 2020 Accord 92101 Sunday I drive",
            ],
            ["baseline"],
            _last(_eq("service_type", "add_car"), _not_contains("follow_up_type", "already_sent")),
        ),
    ]
)

# --- 9 price_pressure ---
SCENARIOS.extend(
    [
        _sc(
            "ac_pr_01",
            "price_pressure",
            "Asks for premium amount",
            [
                "Add 2019 Camry 95814 Friday I drive — how much will my premium be?",
            ],
            ["price_question", "trust"],
            _last(
                _eq("service_type", "add_car"),
                _not_regex("client_reply_draft", r"\$\s*[0-9]{2,}"),
                _not_contains("client_reply_draft", "/month"),
            ),
        ),
        _sc(
            "ac_pr_02",
            "price_pressure",
            "ZH price push",
            [
                "加车2020雅阁94132下周提车我开，保费大概多少？",
            ],
            ["zh", "price"],
            _last(
                _eq("service_type", "add_car"),
                _not_regex("client_reply_draft", r"[0-9]{3,}\s*刀"),
            ),
        ),
        _sc(
            "ac_pr_03",
            "price_pressure",
            "Negotiation tone",
            [
                "I need the cheapest add for a 2022 Civic 93722 Monday I drive",
                "What's your best rate?",
            ],
            ["price"],
            _last(_eq("service_type", "add_car"), _not_regex("client_reply_draft", r"\$\s*[0-9]")),
        ),
    ]
)

# --- 10 impatient_annoyed ---
SCENARIOS.extend(
    [
        _sc(
            "ac_imp_01",
            "impatient_annoyed",
            "Short annoyed follow-up",
            [
                "add car 2021 accord 95134 friday i drive",
                "hello???",
                "anyone there I need this today",
            ],
            ["impatient"],
            _last(_eq("service_type", "add_car")),
        ),
        _sc(
            "ac_imp_02",
            "impatient_annoyed",
            "ZH impatient",
            [
                "加车2022凯美瑞92806周三我开",
                "快点回复好吗",
            ],
            ["zh"],
            _last(_eq("service_type", "add_car")),
        ),
        _sc(
            "ac_imp_03",
            "impatient_annoyed",
            "Caps frustration",
            [
                "ADD CAR 2020 CR-V 80202 SATURDAY I DRIVE",
                "THIS IS URGENT",
            ],
            ["tone"],
            _last(_eq("service_type", "add_car")),
        ),
    ]
)

# --- 11 mixed_intent_move_add ---
SCENARIOS.extend(
    [
        _sc(
            "ac_mi_01",
            "mixed_intent_move_add",
            "Move mention + add car (soft route)",
            [
                "We are moving to Texas next month and I also need to add a 2023 Accord, zip 75201 for now, pickup April 2, I drive.",
            ],
            ["routing", "mixed"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "Accord")),
            soft_route="add_car",
        ),
        _sc(
            "ac_mi_02",
            "mixed_intent_move_add",
            "Garage change + new car",
            [
                "Changing my garaging address soon.",
                "Also add a 2024 Camry, current zip 91361, Friday, I drive.",
            ],
            ["multi", "soft_route"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "Camry")),
            soft_route="add_car",
        ),
        _sc(
            "ac_mi_03",
            "mixed_intent_move_add",
            "ZH mixed",
            [
                "我要搬家到别的州还要加一台2021凯美瑞，邮编90045，下周提车，我开。",
            ],
            ["zh"],
            _last(_eq("service_type", "add_car")),
            soft_route="add_car",
        ),
    ]
)

# --- 12 typo_partial_recovery ---
SCENARIOS.extend(
    [
        _sc(
            "ac_ty_01",
            "typo_partial_recovery",
            "Fat-finger zip",
            [
                "2020 Camry zip 9021O Friday I drive",
                "zip typo — 90210",
            ],
            ["typo", "zip"],
            _last(_eq("service_type", "add_car"), _in_list("collected_fields", "zip")),
        ),
        _sc(
            "ac_ty_02",
            "typo_partial_recovery",
            "Broken model token",
            [
                "2022 Toytoa Camry 94501 Monday I drive",
            ],
            ["ocr_like"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "Camry")),
        ),
        _sc(
            "ac_ty_03",
            "typo_partial_recovery",
            "ZH typo",
            [
                "加车20203雅阁94102周五我开",
                "年份打错了是2020",
            ],
            ["zh"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "2020")),
        ),
    ]
)

# --- 13 zip_digits_only ---
SCENARIOS.extend(
    [
        _sc(
            "ac_zd_01",
            "zip_digits_only",
            "Digits only no ZIP word EN",
            [
                "Add 2022 Accord, garaging 94115, pickup Tuesday, I drive.",
            ],
            ["zip"],
            _last(_eq("service_type", "add_car"), _eq("case_usable", True)),
        ),
        _sc(
            "ac_zd_02",
            "zip_digits_only",
            "ZH digits",
            [
                "加2021凯美瑞92618周五我开",
            ],
            ["zh", "zip"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Camry"),
            ),
        ),
        _sc(
            "ac_zd_03",
            "zip_digits_only",
            "Split turn zip digits",
            [
                "2020 Civic pickup Sunday I drive",
                "95136",
            ],
            ["zip"],
            _last(_eq("service_type", "add_car"), _eq("case_usable", True)),
        ),
    ]
)

# --- 14 multiple_vehicles ---
SCENARIOS.extend(
    [
        _sc(
            "ac_mv_01",
            "multiple_vehicles",
            "Two cars mentioned — primary clarity",
            [
                "I have a 2018 RAV4 already, and I'm adding a 2024 Camry, zip 94566, Friday, I drive the new one.",
            ],
            ["disambiguation"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2024"),
                _contains("primary_vehicle_summary", "Camry"),
            ),
        ),
        _sc(
            "ac_mv_02",
            "multiple_vehicles",
            "ZH two vehicles",
            [
                "家里已有旧车，现在加一台2023雅阁，邮编94010，下周提车，我开新车。",
            ],
            ["zh"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Accord"),
            ),
        ),
        _sc(
            "ac_mv_03",
            "multiple_vehicles",
            "Clarifying turn",
            [
                "Adding a car — we mentioned a Tesla and a Honda.",
                "The new one is 2023 Model Y, zip 94025, Monday, I drive.",
            ],
            ["clarify"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "Model Y")),
        ),
    ]
)

# --- 15 edge_make_model ---
SCENARIOS.extend(
    [
        _sc(
            "ac_ed_01",
            "edge_make_model",
            "Mustang Mach-E",
            [
                "Add my 2024 Ford Mustang Mach-E Select, 94612, March 18, I am primary driver.",
            ],
            ["edge", "mach-e"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Mach-E"),
            ),
        ),
        _sc(
            "ac_ed_02",
            "edge_make_model",
            "F-150",
            [
                "2023 Ford F-150 Lariat, 95355, Friday pickup, I drive.",
            ],
            ["edge", "f150"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "F-150"),
            ),
        ),
        _sc(
            "ac_ed_03",
            "edge_make_model",
            "Honda CR-V",
            [
                "2022 Honda CR-V EX, 92867, next Wednesday, spouse is primary.",
            ],
            ["edge", "crv"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "CR-V")),
        ),
        _sc(
            "ac_ed_04",
            "edge_make_model",
            "Mazda CX-5",
            [
                "2021 Mazda CX-5, 92101, Saturday, I drive.",
            ],
            ["edge", "cx5"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "CX-5")),
        ),
        _sc(
            "ac_ed_05",
            "edge_make_model",
            "Accord",
            [
                "2019 Honda Accord Sport, 94122, Sunday, I drive.",
            ],
            ["edge", "accord"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "Accord")),
        ),
        _sc(
            "ac_ed_06",
            "edge_make_model",
            "Camry",
            [
                "2020 Toyota Camry SE, 90046, Monday, I drive.",
            ],
            ["edge", "camry"],
            _last(_eq("service_type", "add_car"), _contains("primary_vehicle_summary", "Camry")),
        ),
    ]
)

# --- a few more to reach 52 scenarios ---
SCENARIOS.extend(
    [
        _sc(
            "ac_xtra_01",
            "normal_user",
            "VIN included full handoff",
            [
                "Add 2021 Camry VIN 1HGCM82633A004352 zip 95126 Friday I drive",
            ],
            ["vin", "handoff"],
            _last(_eq("service_type", "add_car"), _eq("case_usable", True)),
        ),
        _sc(
            "ac_xtra_02",
            "messy_uncertain",
            "Late VIN",
            [
                "2022 Accord 94116 Tuesday I drive",
                "VIN 1HGCV1F34LA000003",
            ],
            ["vin"],
            _last(_eq("service_type", "add_car")),
        ),
        _sc(
            "ac_xtra_03",
            "correction_heavy",
            "Driver + date correction",
            [
                "2020 CR-V 95825 Monday my wife drives",
                "Correction: I drive, and pickup is Tuesday.",
            ],
            ["driver", "delivery"],
            _last(_eq("service_type", "add_car")),
        ),
        _sc(
            "ac_xtra_04",
            "documents_already_sent",
            "Second turn only already sent",
            [
                "Add 2023 Model Y 94080 Friday I drive",
                "Photos are in WeChat already.",
            ],
            ["already_sent"],
            _last(_eq("follow_up_type", "already_sent")),
        ),
    ]
)
