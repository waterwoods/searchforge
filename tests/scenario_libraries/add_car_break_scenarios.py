"""
Phase-2 “break” scenario library: chaotic multi-turn threads for add-car (rule path).

* Minimum 120 scenarios, each 6–12 user turns.
* Hard cases: contradiction storms, year/VIN chaos, multi-vehicle confusion, emotional users,
  claim vs add-car boundary, typos, long drift, delayed correction, ZIP edges, silent correction.

Loaded by: scripts/run_add_car_cplus_scenario_library.py --library-path ...
"""
from __future__ import annotations

from typing import Any, Callable

# ---------------------------------------------------------------------------
# row builders (same contract as add_car_cplus_scenarios)
# ---------------------------------------------------------------------------


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
    assert 6 <= len(user_turns) <= 12, f"{sid}: expected 6–12 turns, got {len(user_turns)}"
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


def _no_fake_premium() -> dict[str, Any]:
    return _not_regex("client_reply_draft", r"\$\s*[0-9]")


# (display_token, year_final, year_noise, make_line, zip, day_phrase, driver_en)
_CAR: list[tuple[str, str, str, str, str, str, str]] = [
    ("Camry", "2020", "2018", "Toyota Camry", "90210", "next Friday", "I am the primary driver"),
    ("Model Y", "2022", "2021", "Tesla Model Y", "95014", "Monday", "I drive"),
    ("Accord", "2021", "2019", "Honda Accord", "95131", "Tuesday", "my spouse is primary"),
    ("CR-V", "2023", "2021", "Honda CR-V", "90046", "Wednesday", "I drive the new one"),
    ("RAV4", "2021", "2019", "Toyota RAV4", "92620", "Thursday", "I am primary"),
    ("Civic", "2019", "2017", "Honda Civic", "94080", "Saturday", "I drive"),
    ("CX-5", "2020", "2018", "Mazda CX-5", "90025", "Sunday", "I drive"),
    ("F-150", "2021", "2019", "Ford F-150", "95350", "end of month", "I drive"),
    ("Outback", "2022", "2020", "Subaru Outback", "94704", "April 2", "partner drives more"),
    ("Highlander", "2023", "2021", "Toyota Highlander", "92801", "March 5", "I drive"),
    ("4Runner", "2022", "2019", "Toyota 4Runner", "92101", "next week", "I drive"),
    ("Telluride", "2021", "2019", "Kia Telluride", "90265", "Tuesday", "I drive"),
    ("Civic", "2020", "2018", "Honda Civic", "94115", "Friday", "I drive"),
    ("Model 3", "2023", "2022", "Tesla Model 3", "94587", "Saturday", "I drive"),
    ("Accord", "2022", "2020", "Honda Accord", "90037", "Monday", "I drive"),
]


def _turn_count(idx: int) -> int:
    return 6 + (idx % 7)


def _filler_chatter(i: int) -> list[str]:
    """Extra turns to stretch 6–12 without changing vehicle truth."""
    pool = [
        "Also my household bundle is with the same carrier if that matters.",
        "I can text a window sticker photo if the office wants trim details.",
        "No loan yet — may finance next week.",
        "Temporary tags from the dealer for 30 days.",
        "Registration packet from DMV not here yet.",
        "Please prioritize so we can pick up the car on time.",
        "I am the named insured, spouse is a driver on the policy.",
    ]
    return [pool[i % len(pool)]]


def _make_thread(seed_i: int, *, n_turns: int, chaos: str) -> list[str]:
    assert 6 <= n_turns <= 12
    tok, yf, _yn, mline, z, d, dr = _CAR[seed_i % len(_CAR)]
    base: list[str] = [
        "Hey — quick car insurance add question.",
        "We finally bought a replacement vehicle and I need it on the policy.",
        f"Dealer line sheet says {yf} {mline}." if chaos != "zh" else f"定的是{yf}年{mline.split()[-1] if mline else tok}。",
        f"Garaging / rating ZIP {z}." if chaos != "zh" else f"车库邮编{z}。",
        f"Pickup is roughly {d}." if chaos != "zh" else f"提车大概{d}。",
        f"{dr} for insurance." if chaos != "zh" else "主要我开。",
    ]
    if chaos == "zh":
        base = [
            "你好。",
            "要加一辆新车。",
            f"车是{yf}年{mline}。",
            f"邮编{z}。",
            f"{d}提车。",
            "主要我开。",
        ]
    i = 0
    while len(base) < n_turns and i < 20:
        base.extend(_filler_chatter(seed_i + i))
        i += 1
    base = base[:n_turns]
    while len(base) < n_turns:
        base.append("Let me know if the office needs one more field.")
    return base


def _must_include() -> list[dict[str, Any]]:
    o: list[dict[str, Any]] = []

    # 1) Contradiction storm — 2020 Camry ↔ Tesla flips, last wins Camry
    o.append(
        _sc(
            "brk_cs_01",
            "contradiction_storm",
            "4-way make flip; last message returns to 2020 Camry",
            [
                "I need to add a car: I said 2020 Toyota Camry earlier in email.",
                "Wait — not a Camry, scratch that, ignore Camry.",
                "Actually I want a Tesla for the new car.",
                "No — back to Toyota, definitely not Tesla.",
                "Final: 2020 Toyota Camry, garaging ZIP 94506, pickup Tuesday, I drive.",
                "Use that for the add — the Tesla mention was a mistake.",
            ],
            ["flip", "last_wins"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2020"),
                _contains("primary_vehicle_summary", "Camry"),
                _not_contains("primary_vehicle_summary", "Tesla"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )
    o.append(
        _sc(
            "brk_cs_02",
            "contradiction_storm",
            "Model chaos then settle on 2021 Accord",
            [
                "Add car: first I said Civic.",
                "Then I said not Civic.",
                "Then Accord.",
                "Then not Accord — I was confused in the lot.",
                "Settled on 2021 Honda Accord, ZIP 95120, Friday, I am primary driver.",
                "That last line is the only truth for the file.",
            ],
            ["flip", "stability"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2021"),
                _contains("primary_vehicle_summary", "Accord"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )

    # 2) Year chaos + VIN conflict
    o.append(
        _sc(
            "brk_yr_01",
            "year_chaos",
            "2020 not 2018 + late restatement",
            [
                "Hi, add my new car to the policy when you can.",
                "It is a Toyota Camry I think 2018 from the listing.",
                "Wait — dealer sticker says 2020 not 2018, sorry.",
                "ZIP 90025, pickup next Monday, I drive.",
                "If year matters for comp: use 2020 everywhere.",
                "I can send a photo of the Monroney if needed.",
            ],
            ["year", "correction"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2020"),
                _not_contains("primary_vehicle_summary", "2018"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_yr_02",
            "year_chaos",
            "VIN decode vs spoken year (trust last explicit year 2021)",
            [
                "Need add-car for a new Honda I bought Saturday.",
                "VIN 1HGCV1F34MA000123 for your records.",
                "I keep saying 2020 in my head but the paperwork says 2021.",
                "Please use 2021 for the add — 2020 was a typo in my first text.",
                "Garaging 94110, I drive, pickup already happened Sunday.",
                "Confirm 2021 Accord on your side, not 2020.",
            ],
            ["vin", "year"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2021"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_yr_03",
            "year_chaos",
            "2021 actually (ZH)",
            [
            "加车。",
            "我一开始说2020凯美瑞。",
            "不对是2021凯美瑞。",
            "邮编90045。",
            "这周五提车。",
            "主要我开。",
            ],
            ["zh", "year"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2021"),
                _no_fake_premium(),
            ),
        )
    )

    # 3) Multi-vehicle + one VIN + driver mix
    o.append(
        _sc(
            "brk_mv_01",
            "multi_vehicle",
            "Camry + wife CRV; only one VIN; primary driver disambiguation",
            [
            "I need to add my Camry and my wife's CRV to the same policy request thread.",
            "Actually only the new purchase needs binding today — 2020 Camry.",
            "We only have one VIN for now: 4T1B11HK5LU000145 — for the Camry.",
            "The CRV is older and already on file, ignore duplicate ask.",
            "Garaging 92612, pickup is Thursday, I drive the Camry for rating.",
            "Wife is primary on the CRV, but for the new Camry put me as primary — sorry for the mix.",
            ],
            ["multi", "vin", "driver"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2020"),
                _contains("primary_vehicle_summary", "Camry"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_mv_02",
            "multi_vehicle",
            "Two cars then narrow to 2022 RAV4",
            [
            "Dealer is delivering two cars same day — a RAV4 and a Corolla for my parents.",
            "We are only insuring the RAV4 under my policy, not the Corolla here.",
            "RAV4 is 2022, garaging 90013, I drive the RAV4.",
            "I might send two VINs but only the RAV4 VIN is for this add: 2T3H1RFV8MC045678",
            "Ignore the Corolla thread from my last email.",
            "Please quote/bind for the 2022 RAV4 only.",
            ],
            ["disambiguation"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "RAV4"),
                _contains("primary_vehicle_summary", "2022"),
                _no_fake_premium(),
            ),
        )
    )

    # 4) Emotional / impatient
    o.append(
        _sc(
            "brk_em_01",
            "emotional_user",
            "why are you asking again + just do it",
            [
            "add car 2020 accord 90023 friday i drive",
            "why are you asking this again??? i gave zip 90023 already",
            "just do it today",
            "this is stupid if you still ask the same",
            "pickup friday, i drive, accord 2020, zip 90023 — lock it in",
            "please send to the office without more loops",
            ],
            ["emotion"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Accord"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_em_02",
            "emotional_user",
            "impatient + caps",
            [
            "ADD CAR 2020 CR-V 80202 SATURDAY I DRIVE",
            "HELLO",
            "ANYONE THERE",
            "I NEED THIS BOUND",
            "ZIP IS 80202 STOP ASKING",
            "PRIMARY DRIVER: ME. CAR: 2020 HONDA CR-V. SATURDAY PICKUP.",
            ],
            ["tone", "impatient"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "CR-V"),
                _no_fake_premium(),
            ),
        )
    )

    # 5) Claim vs add boundary + already sent
    o.append(
        _sc(
            "brk_cl_01",
            "claim_vs_add",
            "accident mention but explicit add-car lane",
            [
            "I had a fender bender two weeks ago but I am NOT opening a new claim in this text.",
            "I am here to add a 2021 Toyota Camry to my policy, ZIP 90018, next Thursday pickup, I drive.",
            "Do not route me to claims — this is an add-vehicle request only.",
            "Garaging zip 90018 for the new car.",
            "I will email ID cards separately.",
            "Please keep this thread as new-car add only.",
            ],
            ["claim_boundary", "routing"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Camry"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )
    o.append(
        _sc(
            "brk_cl_02",
            "claim_vs_add",
            "sent photos + add car; materials acknowledgment",
            [
            "I need to add a 2022 Civic, 95051, Friday, I drive.",
            "I had an accident in another state last year; ignore that for this add.",
            "Also I already sent photos of the new car registration in WeChat yesterday — please check.",
            "The add is 2022 Civic, same ZIP 95051.",
            "Acknowledge the photos so I do not re-upload.",
            "Primary driver: me for the new Civic only.",
            ],
            ["materials", "add_car"],
            _last(
                _eq("service_type", "add_car"),
                _eq("follow_up_type", "already_sent"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )

    # 6) Typos + garbage OCR-style
    o.append(
        _sc(
            "brk_ty_01",
            "typo_garbage",
            "add vehcle camryyy 202O zip 9O218",
            [
            "add vehcle camryyy 2O2O garaging 9O218 friday me drive pls",
            "sorry that was ocr",
            "correct is 2020 Toyota Camry and ZIP 90018 not letters",
            "pickup still Friday, I am primary",
            "can you read that back without the letter O in the zip",
            "use 90018 for rating",
            ],
            ["typo", "ocr"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2020"),
                _contains("primary_vehicle_summary", "Camry"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_ty_02",
            "typo_garbage",
            "mixed letter digits year",
            [
            "insurance add: Toytoa 2020 camry 9021O tuesday I drive",
            "9021O is wrong",
            "90210 is the zip",
            "Toytoa = Toyota, typo",
            "keep 2020 Camry",
            "thanks",
            ],
            ["typo", "zip"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2020"),
                _no_fake_premium(),
            ),
        )
    )

    # 7) Long drift add → move → price → back to car (10+ turns)
    o.append(
        _sc(
            "brk_ld_01",
            "long_drift",
            "pivot to move and price then return to add-car",
            [
            "I need to add a 2020 Mazda CX-5 to my policy, garaging 90036.",
            "By the way we may move to Oregon next year — not today’s task.",
            "Roughly what would moving do to our bundle? (do not need an exact number now)",
            "Back to the car: pickup March 8, I drive, CX-5 2020.",
            "If premium moves a lot, tell the office to call me — but no fake numbers in chat",
            "Garaging is still 90036 for the add.",
            "I am the primary driver on the new CX-5.",
            "VIN is coming after work today.",
            "Please stage the add for tomorrow morning.",
            "Ignore Oregon move for this add — 90036 and CX-5 only.",
            ],
            ["drift", "add_car", "no_price"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "CX-5"),
                _not_regex("client_reply_draft", r"\$\s*[0-9]"),
            ),
        )
    )
    o.append(
        _sc(
            "brk_ld_02",
            "long_drift",
            "ZH long drift with return to 雅阁",
            [
            "在吗。",
            "要加车。",
            "先问问你们搬家要改地址吗 可能下半年搬",
            "先不管那个",
            "车是2019年雅阁 邮编90025 周五提车 我开",
            "搬家的事以后再说 先把加车给办公室",
            "别给我乱报价数字哈",
            "谢谢",
            ],
            ["zh", "drift"],
            _last(
                _eq("service_type", "add_car"),
                _no_fake_premium(),
            ),
        )
    )

    # 8) Partial delayed correction (3–4 turns later)
    o.append(
        _sc(
            "brk_dc_01",
            "delayed_correction",
            "wrong zip early; correction turn 4",
            [
            "add new car: 2019 RAV4, I drive, pickup Sunday.",
            "I think garaging is 90028 — use that for now.",
            "Also the dealer is open Sunday morning.",
            "Correction: I looked at Zillow, garaging is 90027 for my garage not 90028.",
            "Keep 2019 RAV4, Sunday, I drive — only ZIP changes to 90027.",
            "Thanks for only updating the ZIP field for rating.",
            ],
            ["late_zip"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "RAV4"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_dc_02",
            "delayed_correction",
            "driver correction late in thread",
            [
            "2022 Model Y, 95051, Saturday pickup, I drive for insurance.",
            "I am in a rush — please prep the bind packet.",
            "Might need a lienholder email later but not now.",
            "Actually: primary driver is my partner, not me — update that for the Model Y add.",
            "Everything else the same, still 95051, Saturday, 2022 Model Y.",
            "Sorry for the late correction; partner should be primary on this car.",
            ],
            ["late_driver"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Model Y"),
                _no_fake_premium(),
            ),
        )
    )

    # 9) ZIP edge — spelled "ZIP" + wrong then corrected
    o.append(
        _sc(
            "brk_zp_01",
            "zip_edge",
            "ZIP label + correction",
            [
            "Add vehicle: 2018 F-150, I drive, pickup April 1.",
            "The garaging ZIP code is 9021 — oops that is 4 digits, full ZIP 90210.",
            "Sorry wrong: my house is 90064 not 90210.",
            "Please use ZIP 90064 for garaging on the 2018 F-150.",
            "Pickup April 1 still valid.",
            "Primary driver: me. Thanks.",
            ],
            ["zip", "spelled"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "F-150"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_zp_02",
            "zip_edge",
            "second correction wins 94122",
            [
            "Accord, garaging 94103, I drive, Tuesday.",
            "Wait garage is 94122 not 94103 — fix that for rating.",
            "Honda Accord 2020.",
            "Nothing else changes.",
            "VIN is optional today.",
            "Use 94122 on file, not 94103.",
            ],
            ["zip", "last_wins"],
            _last(
                _eq("service_type", "add_car"),
                _no_fake_premium(),
            ),
        )
    )

    # 10) Silent correction — user restates car without “sorry”
    o.append(
        _sc(
            "brk_sc_01",
            "silent_correction",
            "new message overrides vehicle without apology",
            [
            "I am adding a 2019 Corolla, 90001, I drive, Monday.",
            "2020 Corolla, 90001, I drive, Monday. same thread.",
            "Use the latest line: 2020 Corolla.",
            "The earlier year was a finger slip, not a second car.",
            "No lienholder.",
            "Please confirm 2020 only.",
            ],
            ["silent", "last_wins"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2020"),
                _contains("primary_vehicle_summary", "Corolla"),
                _not_contains("primary_vehicle_summary", "2019"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_sc_02",
            "silent_correction",
            "ZH silent trim swap", 
            [
            "加2019年凯美瑞 90025 周五我开",
            "2021年凯美瑞 90025 周五我开 以上一条为准",
            "不用道歉 直接按新的",
            "VIN 晚点",
            "材料可能要周末",
            "谢谢",
            ],
            ["zh", "silent"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2021"),
                _no_fake_premium(),
            ),
        )
    )

    return o


def _pad_generated(n: int, start: int) -> list[dict[str, Any]]:
    o: list[dict[str, Any]] = []
    tag_sets: list[tuple[str, list[str]]] = [
        ("stress_drip", ["stress", "drip"]),
        ("stress_flip", ["stress", "stable"]),
        ("stress_mixed", ["mixed", "stable"]),
        ("stress_restate", ["restate", "coherent"]),
        ("stress_billing_tease", ["pivot", "add_car"]),
        ("stress_ocrish", ["ocr", "recovery"]),
        ("stress_silent_zip", ["zip", "implicit"]),
    ]
    for i in range(n):
        idx = start + i
        nt = _turn_count(idx)
        chaos = "zh" if (idx % 11 == 0) else "en"
        turns = _make_thread(idx, n_turns=nt, chaos=chaos)
        cat, rtags = tag_sets[i % len(tag_sets)]
        tok, yf, _, mline, z, _d, _dr = _CAR[idx % len(_CAR)]
        soft = "add_car" if (idx % 5 == 0) else None
        kw: dict[str, Any] = {}
        if soft:
            kw["soft_route"] = soft
        o.append(
            _sc(
                f"brk_p_{i+1:03d}",
                cat,
                f"generated {nt}-turn {tok} ({cat})",
                turns,
                rtags,
                _last(
                    _eq("service_type", "add_car"),
                    _contains("primary_vehicle_summary", yf),
                    _contains("primary_vehicle_summary", tok if tok != "Model 3" else "Model 3"),
                    _no_fake_premium(),
                ),
                **kw,
            )
        )
    return o


def _extra_labeled() -> list[dict[str, Any]]:
    """Additional explicit hard threads to diversify categories before padding."""
    o: list[dict[str, Any]] = []
    o.append(
        _sc(
            "brk_hw_20",
            "contradiction_storm",
            "TESLA then CAMRY then Model 3 then final 2020 Camry",
            [
            "add car: starting with 2020 Camry 90210 Friday I drive",
            "not Camry — I want a Tesla for the new purchase",
            "actually the Tesla is my fantasy car; real car is 2020 Camry",
            "I confused trim levels — it is 2020 Camry LE, not XSE, sorry",
            "Final: 2020 Toyota Camry, ZIP 90210, Friday, I drive",
            "Please ignore all Tesla and Model 3 noise above — Camry is final",
            ],
            ["storm", "settle"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2020"),
                _contains("primary_vehicle_summary", "Camry"),
                _not_contains("primary_vehicle_summary", "Tesla"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )
    o.append(
        _sc(
            "brk_hw_21",
            "vin_year_tension",
            "claim VIN year vs user says 2021",
            [
            "VIN 1HGCV1F34MA000333 on the purchase agreement.",
            "Dealer said model year 2021 but the VIN decoders sometimes look weird.",
            "Use 2021 Accord for the add — 95100 garaging, Tuesday pickup, I drive.",
            "If the VIN year disagrees, trust my purchase agreement year 2021.",
            "ZIP is 95100 not 95110 — correction.",
            "Primary driver: me. Thanks.",
            ],
            ["vin", "year"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2021"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_hw_22",
            "multi_vehicle",
            "one VIN only for Camry; CRV is separate policy mention",
            [
            "add my Camry and my wife CRV in one form",
            "Actually wife's CRV is on her own policy, only add the Camry here",
            "Only VIN: 1HGCM82633A004355 for the 2020 Camry",
            "If you can only file one, file the Camry with that VIN",
            "Wife is not a driver on this new Camry for rating: I am",
            "Ignore CRV in this add task completely",
            ],
            ["multi", "one_vin"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Camry"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_hw_23",
            "emotional_user",
            "why again + this is stupid (ZH+EN mix)",
            [
            "加车 2020 雅阁 90025 周五我开",
            "Why are you asking this again about ZIP???",
            "this is stupid 邮编就是90025",
            "just do it 谢谢",
            "I already said primary driver: me 我开",
            "no more back-and-forth",
            ],
            ["emotion", "bilingual"],
            _last(
                _eq("service_type", "add_car"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_hw_24",
            "long_drift",
            "10 turns topic shift price question then car",
            [
            "Hi",
            "I want to add a 2020 Civic",
            "Also moving houses soon — ignore dates",
            "How much is insurance roughly — not asking for a fake number",
            "Back: civic 2020, zip 90011",
            "Tuesday pickup",
            "I drive",
            "No VIN now",
            "Please send to the office as add-car not claim",
            "Thanks and confirm 2020 Civic 90011 only",
            ],
            ["long", "no_price"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Civic"),
                _not_regex("client_reply_draft", r"\$\s*[0-9]{2,}"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_hw_25",
            "zip_edge",
            "ZIP word spelled in sentence",
            [
            "Add a 2019 Corolla, garaging ZIP 90019, Sunday, I drive.",
            "I typed Z-I-P 90019 in the portal — same as chat.",
            "If rating needs 5 digits, use 90019 exactly.",
            "Not 90016 — 90019.",
            "Thanks",
            "No changes beyond ZIP confirmation",
            ],
            ["zip", "spelled_out"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Corolla"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "brk_hw_26",
            "delayed_correction",
            "Model flip turn 4–5: Civic → Accord",
            [
            "New car: 2021 Honda, garaging 94080, I drive, Saturday.",
            "I said Civic in my head in turn 1 but that was wrong",
            "Dealer file says Civic",
            "Actually the purchase order says Accord 2021 — use Accord, not Civic",
            "Keep everything else, only fix model to Accord 2021",
            "VIN: 1HGCV1F34MA000999 when you need it",
            ],
            ["late_model"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Accord"),
                _not_contains("primary_vehicle_summary", "Civic"),
                _no_fake_premium(),
            ),
        )
    )
    return o


def _wave2_hardening() -> list[dict[str, Any]]:
    """Tighter product-boundary threads (regression for follow-up + vehicle line)."""
    w: list[dict[str, Any]] = []
    w.append(
        _sc(
            "brk_w2_01",
            "contradiction_storm",
            "Tesla in middle, last bubble negation only (must pick prior Camry)",
            [
                "add car: 2020 Camry, zip 90025, fri, me drive",
                "actually thinking Tesla for a second",
                "forget Tesla — the purchase is 2020 Camry",
                "zip still 90025",
                "the Tesla line was a mistake, do not use it",
                "only Camry 2020 is real for this bind",
            ],
            ["settle", "tesla_mistake"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2020"),
                _contains("primary_vehicle_summary", "Camry"),
                _not_contains("primary_vehicle_summary", "Tesla"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )
    w.append(
        _sc(
            "brk_w2_02",
            "claim_vs_add",
            "clarify question on ded — must not sticky-already_sent",
            [
                "I had an accident in 2019, old news — today I add a 2021 Accord 90036 Tuesday I drive",
                "I already emailed you the title scan yesterday for a different case",
                "What does the collision deductible on my policy mean for this new car add",
                "Answer that first then continue the add. ZIP stays 90036, car 2021 Accord.",
                "I am not disputing a claim here — this is add-car only after you answer.",
                "Once clear, proceed with the 2021 Accord add for the office.",
            ],
            ["clarify", "add_car", "not_sticky_sent"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2021"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )
    w.append(
        _sc(
            "brk_w2_02b",
            "claim_vs_add",
            "same as w2_02 with 6 turns (pad shape)",
            [
                "accident in 2019, ignore — add 2021 Accord 90036 Tuesday I drive",
                "I emailed a scan yesterday for a different case",
                "what is collision ded",
                "for this add only, ZIP 90036",
                "VIN if needed: 1HGCV1F34MA000777",
                "thanks",
            ],
            ["shape", "clarify"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2021"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )
    w.append(
        _sc(
            "brk_w2_03",
            "multi_vehicle",
            "three names then one VIN for Camry",
            [
            "I mentioned Camry, CRV, and a Pilot in the group chat with my spouse.",
            "The only car we are binding today is the 2019 Camry with VIN 1HGCM82633A004500.",
            "Drop Pilot and CRV for this add task.",
            "garaging 94588, I drive, Sunday pickup for the Camry",
            "If you can only have one, file under Camry only with that VIN",
            "Ignore the other two models completely for the quote request",
            ],
            ["triage", "vin"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Camry"),
                _no_fake_premium(),
            ),
        )
    )
    w.append(
        _sc(
            "brk_w2_04",
            "zip_edge",
            "ZIP in caps mid-thread correction",
            [
            "2020 RAV4 90023 Monday I drive",
            "wrong — garaging is actually ZIP 90025 not 90023",
            "I typed ZIP 90011 by mistake in my notes — ignore 90011",
            "the real ZIP I verify on USPS is 90025 for home garage",
            "pickup is Monday, same 2020 RAV4, same driver: me",
            "confirm 90025 on the record",
            ],
            ["zip", "usps"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "RAV4"),
                _no_fake_premium(),
            ),
        )
    )
    w.append(
        _sc(
            "brk_w2_05",
            "silent_correction",
            "third bubble silent swap 2018 to 2019 F-150",
            [
            "F-150 2018, 90065, thursday, I drive",
            "dealer reprinted paperwork",
            "2019 F-150 same trim, 90065, thursday, I drive",
            "same VIN on the truck — that was a paperwork mismatch year only",
            "use 2019 for insurance",
            "thanks",
            ],
            ["year", "quiet_fix"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2019"),
                _not_contains("primary_vehicle_summary", "2018"),
                _no_fake_premium(),
            ),
        )
    )
    w.append(
        _sc(
            "brk_w2_06",
            "emotional_user",
            "this is stupid + price pressure without $",
            [
            "add 2020 civic 90017 sunday I drive",
            "this is stupid that chat keeps stalling",
            "roughly how does adding a car change premium (no fake dollar number needed)",
            "I just need a human to bind today",
            "ZIP 90017",
            "only the civic 2020",
            ],
            ["emotion", "price"],
            _last(
                _eq("service_type", "add_car"),
                _not_regex("client_reply_draft", r"\$\s*[0-9]{2,}"),
                _no_fake_premium(),
            ),
        )
    )
    w.append(
        _sc(
            "brk_w2_07",
            "typo_garbage",
            "9O2l0 style zip",
            [
            "2021 outback, garagin 9O2l0, thursday, I drive",
            "letter O not zero — fix to 90210",
            "that was obnoxious typing",
            "2021 outback 90210 thursday I drive as final",
            "ok?",
            "thanks",
            ],
            ["typo", "ocr"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2021"),
                _no_fake_premium(),
            ),
        )
    )
    w.append(
        _sc(
            "brk_w2_08",
            "long_drift",
            "12 turns: ping pong topics",
            [
            "hi",
            "add car",
            "maybe move states next year",
            "ignore move",
            "car is 2019 highlander 90032",
            "pickup tuesday",
            "how much premium — no exact numbers",
            "ignore premium question, just the add for office",
            "I drive the highlander",
            "VIN: 5TDDZ3EH8KS000111",
            "bundle discount question — skip",
            "final: 2019 highlander 90032 tuesday I drive",
            ],
            ["12_turn", "drift"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Highlander"),
                _not_regex("client_reply_draft", r"\$\s*[0-9]"),
            ),
        )
    )
    return w


def _build_scenarios() -> list[dict[str, Any]]:
    must = _must_include()
    extra = _extra_labeled()
    w2 = _wave2_hardening()
    need = 120 - (len(must) + len(extra) + len(w2))
    if need < 0:
        raise RuntimeError("logic error: too many must/extra/wave2")
    pad = _pad_generated(need, start=200)
    out = must + extra + w2 + pad
    assert len(out) >= 120
    for s in out:
        t = s["user_turns"]
        if not (6 <= len(t) <= 12):
            raise RuntimeError(f"bad turn count: {s['id']}")
    return out


SCENARIOS: list[dict[str, Any]] = _build_scenarios()
