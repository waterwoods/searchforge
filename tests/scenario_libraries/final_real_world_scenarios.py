"""
Final lock-in: real-world multi-turn add-car / vehicle confusion scenarios.

Loaded by scripts/llm_chaos_live_triage_check.py (--library).
Each scenario has >=2 user turns for ASGI chaos pack coverage.
"""

from __future__ import annotations

from typing import Any


def _sc(
    sid: str,
    category: str,
    description: str,
    user_turns: list[str],
    risk_tags: list[str],
) -> dict[str, Any]:
    return {
        "id": sid,
        "category": category,
        "description": description,
        "user_turns": user_turns,
        "expected_risk_tags": risk_tags,
    }


# 28 scenarios: multi-vehicle, messy language, long threads, edge cases
ALL_SCENARIOS: list[dict[str, Any]] = [
    # --- A. Multi-vehicle confusion ---
    _sc(
        "frw_mv_first_car",
        "multi_vehicle",
        "Explicit: use the first car",
        [
            "adding two cars — 2019 Honda Civic zip 94122 and 2021 Toyota Camry zip 94122",
            "use the first car for the quote details",
            "garage is still 94122, I'm the main driver on that one",
        ],
        ["multi_vehicle", "anchor"],
    ),
    _sc(
        "frw_mv_not_that_one",
        "multi_vehicle",
        "Correction: not that one",
        [
            "I need add car 2020 Ford F-150 and also a 2022 Nissan Altima, zip 90210",
            "no not that one — I meant the truck for the garaging question",
            "F-150 stays at 90210, spouse primary on the Altima",
        ],
        ["multi_vehicle", "correction"],
    ),
    _sc(
        "frw_mv_switch_back",
        "multi_vehicle",
        "Switch active vehicle then switch back",
        [
            "Adding a 2023 Tesla Model 3 and a 2018 Subaru Outback, ZIP 95123",
            "focus on the Tesla for a second — performance tires question",
            "switch back to the Subaru for garaging — it's at a different address",
        ],
        ["multi_vehicle", "switch"],
    ),
    _sc(
        "frw_mv_just_camry",
        "multi_vehicle",
        "Disambiguation: just the Camry",
        [
            "Hi we have a RAV4 and a Camry to add same policy, 94501",
            "just the Camry please for the ID card name spelling",
            "2022 Camry LE, I'm primary",
        ],
        ["multi_vehicle", "disambiguation"],
    ),
    _sc(
        "frw_mv_which_one_clarify",
        "multi_vehicle",
        "Which SUV vague then resolve",
        [
            "two suvs new one is cx5 other is crv zip 94588",
            "the mazda",
            "pickup this Saturday, I drive the mazda most",
        ],
        ["multi_vehicle", "clarify"],
    ),
    # --- B. Real messy language ---
    _sc(
        "frw_lang_typos",
        "messy_language",
        "Heavy typos",
        [
            "add car pls acoord 2021 gryage 90402",
            "sorry Accord* 2021 honda accrod",
            "tuesday pickup i am primary drievr",
        ],
        ["typo", "add_car"],
    ),
    _sc(
        "frw_lang_broken_en",
        "messy_language",
        "Broken English",
        [
            "I want insurance for new car buying, not sure how say",
            "is 2019 corolla, zip where I live 85001, wife she drive more",
            "ok we put my name policy",
        ],
        ["broken_en", "add_car"],
    ),
    _sc(
        "frw_lang_zh_en_mix",
        "messy_language",
        "Mixed Chinese / English",
        [
            "想加一台车 quote 一下",
            "2020 Toyota Camry 凯美瑞, ZIP 94112, 这周末提车",
            "primary driver 是我 myself",
        ],
        ["zh_en", "add_car"],
    ),
    _sc(
        "frw_lang_vague",
        "messy_language",
        "Vague then narrow",
        [
            "something something new car insurance help",
            "oh it's a compact SUV, Mazda I think",
            "2024 CX-30, 94566, Friday delivery, me primary",
        ],
        ["vague", "add_car"],
    ),
    _sc(
        "frw_lang_sms_style",
        "messy_language",
        "SMS-style fragments",
        [
            "add car",
            "accord 22 / 94107 / fri / me",
            "wait 2023 accord not 22",
        ],
        ["sms", "correction"],
    ),
    _sc(
        "frw_lang_confusing_pronouns",
        "messy_language",
        "Pronoun soup",
        [
            "my brother's car and mine both new but I only need mine on policy",
            "mine is the Prius his is the WRX",
            "Prius zip 94608, I'm primary",
        ],
        ["pronouns", "multi_vehicle"],
    ),
    # --- C. Long threads (10–15 turns): switches, corrections, late VIN ---
    _sc(
        "frw_long_10_switch",
        "long_thread",
        "10 turns: multiple corrections",
        [
            "Need to add a vehicle.",
            "It's a sedan.",
            "Toyota.",
            "Camry.",
            "2020.",
            "Actually 2021 Camry.",
            "Garage ZIP 90301.",
            "No — 90302.",
            "Pickup end of month.",
            "I'm the primary driver.",
        ],
        ["long", "correction"],
    ),
    _sc(
        "frw_long_12_vin_late",
        "long_thread",
        "12 turns: VIN appears late",
        [
            "Adding a used SUV.",
            "Honda.",
            "CR-V.",
            "2019.",
            "ZIP 91355.",
            "Primary me.",
            "Spouse sometimes drives — note that.",
            "Delivery was last week already.",
            "Odometer about 45k.",
            "Color silver.",
            "One more thing — VIN at the end: 5FNRL38478B045121",
            "Please confirm the VIN matches CR-V.",
        ],
        ["long", "vin_late"],
    ),
    _sc(
        "frw_long_11_two_cars",
        "long_thread",
        "11 turns: two cars then late focus",
        [
            "Two cars to add.",
            "First: 2022 Civic.",
            "Second: 2022 Civic also but different VIN later.",
            "Same ZIP 94080 for both.",
            "I drive the first.",
            "Wife drives the second.",
            "Wait both are Civics same year — first is sedan second is hatch",
            "First VIN will send next message",
            "19XFC2F59NE123456",
            "Second VIN 2HGFC2F59PH789012",
            "Confirm both on policy.",
        ],
        ["long", "same_model", "vin"],
    ),
    _sc(
        "frw_long_10_zh_corrections",
        "long_thread",
        "10 turns: Chinese + corrections",
        [
            "要加新车。",
            "丰田。",
            "凯美瑞。",
            "不对是2021年。",
            "邮编94015。",
            "这周五提车。",
            "主要是我开。",
            "其实还有第二台车晚点再说",
            "先搞定这台Camry",
            "谢谢",
        ],
        ["long", "zh"],
    ),
    _sc(
        "frw_long_15_messy",
        "long_thread",
        "15 turns: messy incremental",
        [
            "hi",
            "car",
            "new",
            "ford",
            "escape",
            "2020",
            "zip",
            "98101",
            "seattle",
            "me driver",
            "actually 2021 escape",
            "same zip",
            "pickup tuesday",
            "add comprehensive",
            "thanks",
        ],
        ["long", "incremental"],
    ),
    # --- D. Edge cases ---
    _sc(
        "frw_edge_same_model_twice",
        "edge",
        "Same model twice different trims",
        [
            "Two 2021 Honda Accords to add, 94117",
            "LX and Sport trim — different VINs I'll send",
            "Focus on LX first: I'm primary on LX",
            "Sport is for my partner — primary driver partner",
        ],
        ["same_model", "multi_vehicle"],
    ),
    _sc(
        "frw_edge_vin_conflict",
        "edge",
        "VIN stated then corrected",
        [
            "Add 2018 Jeep Grand Cherokee ZIP 80202 VIN 1C4RJFAG5JC123456",
            "Sorry wrong VIN — use 1C4RJFAG5JC654321 instead",
            "Everything else same, I'm primary",
        ],
        ["vin_conflict", "correction"],
    ),
    _sc(
        "frw_edge_ignore_old",
        "edge",
        "Ignore prior mention + new car",
        [
            "Forget the Camry I mentioned — don't add that",
            "Only add 2024 Hyundai Elantra ZIP 33101",
            "I'm primary, pickup Monday",
        ],
        ["ignore", "scope"],
    ),
    _sc(
        "frw_edge_duplicate_year",
        "edge",
        "Duplicate year confusion",
        [
            "2020 2020 Toyota RAV4 zip 97201",
            "meant one RAV4 — typo double year",
            "2020 RAV4 hybrid, I'm primary",
        ],
        ["duplicate_token", "typo"],
    ),
    _sc(
        "frw_edge_out_of_order",
        "edge",
        "Facts out of order",
        [
            "ZIP 33139",
            "Toyota Corolla",
            "2022",
            "I am primary, add this car please",
        ],
        ["reorder", "add_car"],
    ),
    _sc(
        "frw_edge_policy_renewal_noise",
        "edge",
        "Noise then add-car signal",
        [
            "renewal question unrelated — actually need add vehicle",
            "2023 Nissan Rogue 95814",
            "Friday pickup spouse primary",
        ],
        ["noise", "add_car"],
    ),
    # --- Extra high-value mix ---
    _sc(
        "frw_mix_truck_vs_sedan",
        "multi_vehicle",
        "Truck vs sedan disambiguation",
        [
            "adding F-150 and a Civic same household zip 75001",
            "coverage question is only for the truck",
            "F-150 I'm listed primary",
        ],
        ["multi_vehicle"],
    ),
    _sc(
        "frw_mix_late_garage",
        "long_thread",
        "Garage ZIP late in thread",
        [
            "Add 2021 Subaru Forester",
            "I'm primary",
            "Picking up Sunday",
            "Oh garaging 97005 Oregon",
        ],
        ["late_field"],
    ),
    _sc(
        "frw_mix_lease",
        "edge",
        "Lease language",
        [
            "lease return then new lease 2024 BMW 330i",
            "ZIP 10001 garaging",
            "I'm lessee and primary driver",
        ],
        ["lease", "add_car"],
    ),
    _sc(
        "frw_mv_rank_second",
        "multi_vehicle",
        "Second car explicitly",
        [
            "2017 Lexus RX and 2020 Acura MDX, zip 90808",
            "details for the second car in the list",
            "MDX — I'm primary",
        ],
        ["multi_vehicle", "ordinal"],
    ),
    _sc(
        "frw_lang_fat_finger",
        "messy_language",
        "Keyboard adjacent typos",
        [
            "add 2921 Honda Cvic zip 9q410",  # intentional near-miss keys
            "2021 Civic zip 94104 sorry",
            "I'm primary, pickup weds",
        ],
        ["typo", "add_car"],
    ),
    _sc(
        "frw_long_9_oco",
        "long_thread",
        "9 turns: odometer and color before VIN",
        [
            "Used minivan to add",
            "Chrysler Pacifica 2019",
            "ZIP 44101",
            "50k miles roughly",
            "navy blue",
            "VIN: 2C4RC1BG7KR123456",
            "I'm primary",
            "Also need rental reimbursement",
            "Thanks — that's the full picture.",
        ],
        ["long", "vin_late"],
    ),
]

SCENARIOS = ALL_SCENARIOS
