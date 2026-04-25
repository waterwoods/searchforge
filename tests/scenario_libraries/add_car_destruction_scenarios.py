"""
Phase-3 “destruction” scenario library: adversarial 8–15 turn add-car threads.

* Minimum 150 scenarios; each 8–15 user turns.
* Hard cases: identity collapse, driver contradictions, temporal confusion,
  cross-intent poisoning, system challenges, long drift, multi-entity noise,
  silent correction, typos/emoji, adversarial phrasing.

Loaded by: scripts/run_add_car_cplus_scenario_library.py --library-path ...
"""
from __future__ import annotations

from typing import Any

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
    n = len(user_turns)
    assert 8 <= n <= 15, f"{sid}: expected 8–15 turns, got {n}"
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
    ("Model 3", "2023", "2022", "Tesla Model 3", "94587", "Saturday", "I drive"),
    ("Accord", "2022", "2020", "Honda Accord", "90037", "Monday", "I drive"),
]


def _turn_count(i: int) -> int:
    return 8 + (i % 8)


def _filler_chatter(i: int) -> list[str]:
    pool = [
        "Also my household bundle is with the same carrier if that matters.",
        "I can text a window sticker photo if the office wants trim details.",
        "No loan yet — may finance next week.",
        "Temporary tags from the dealer for 30 days.",
        "Registration packet from DMV not here yet.",
        "Please prioritize so we can pick up the car on time.",
        "I am the named insured, spouse is a driver on the policy.",
        "Topic shift: I might cancel my other policy but ignore that for this add.",
    ]
    return [pool[i % len(pool)]]


def _make_thread(seed_i: int, *, n_turns: int, chaos: str) -> list[str]:
    assert 8 <= n_turns <= 15
    tok, yf, _yn, mline, z, d, dr = _CAR[seed_i % len(_CAR)]
    if chaos == "zh":
        if "model y" in mline.lower() or "model y" in (tok or "").lower():
            _zh_m = "Model Y"
        elif "model 3" in mline.lower() or "model 3" in (tok or "").lower() or "model3" in mline.lower():
            _zh_m = "Model 3"
        else:
            _zh_m = mline.split()[-1] if mline else tok
    else:
        _zh_m = ""
    base: list[str] = [
        "Hey — quick car insurance add question (wrong thread before, ignore).",
        "We finally bought a replacement vehicle and I need it on the policy today.",
        f"Dealer line sheet says {yf} {mline}."
        if chaos != "zh"
        else f"定的是{yf}年{_zh_m}。",
        f"Garaging / rating ZIP {z}." if chaos != "zh" else f"车库邮编{z}。",
        f"Pickup is roughly {d}." if chaos != "zh" else f"提车大概{d}。",
        f"{dr} for insurance." if chaos != "zh" else "主要我开。",
    ]
    i = 0
    while len(base) < n_turns and i < 30:
        base.extend(_filler_chatter(seed_i + i))
        i += 1
    base = base[:n_turns]
    while len(base) < n_turns:
        base.append("Let me know if the office needs one more field.")
    return base


def _pad_generated(n: int, start: int) -> list[dict[str, Any]]:
    o: list[dict[str, Any]] = []
    tag_sets: list[tuple[str, list[str]]] = [
        ("destruction_drip", ["stress", "drip", "8p"]),
        ("destruction_flip", ["contradiction", "stable", "8p"]),
        ("destruction_mixed", ["cross_talk", "coherent", "8p"]),
        ("destruction_restate", ["memory", "restate", "8p"]),
        ("destruction_billing_tease", ["pivot", "add_car", "8p"]),
        ("destruction_ocrish", ["typo", "recovery", "8p"]),
        ("destruction_silent_zip", ["zip", "implicit", "8p"]),
    ]
    for i in range(n):
        idx = start + i
        nt = _turn_count(idx)
        chaos = "zh" if (idx % 11 == 0) else "en"
        turns = _make_thread(idx, n_turns=nt, chaos=chaos)
        cat, rtags = tag_sets[i % len(tag_sets)]
        tok, yf, _, mline, _z, _d, _dr = _CAR[idx % len(_CAR)]
        soft = "add_car" if (idx % 5 == 0) else None
        kw: dict[str, Any] = {}
        if soft:
            kw["soft_route"] = soft
        disp = "Model 3" if tok == "Model 3" else tok
        o.append(
            _sc(
                f"dest_p_{i+1:03d}",
                cat,
                f"pad {nt}-turn {disp} ({cat})",
                turns,
                rtags,
                _last(
                    _eq("service_type", "add_car"),
                    _contains("primary_vehicle_summary", yf),
                    _contains("primary_vehicle_summary", disp),
                    _no_fake_premium(),
                ),
                **kw,
            )
        )
    return o


def _mandatory_extreme() -> list[dict[str, Any]]:
    o: list[dict[str, Any]] = []

    # 1 — Identity collapse (CRITICAL)
    o.append(
        _sc(
            "dest_id_01",
            "identity_collapse",
            "Camry → Tesla → CRV → first one → the car I said earlier",
            [
                "I need to add a new car: was thinking 2020 Toyota Camry, ZIP 94506, Tuesday pickup.",
                "Actually scratch Camry I want a Tesla instead for the new purchase.",
                "No wait, family picked a 2021 Honda CRV, same ZIP, Wednesday pickup — forget Tesla.",
                "Actually go back to the first car I mentioned in this thread, not the CRV.",
                "The car I said earlier is the one the office should use — 2020 Camry.",
                "Ignore Tesla and CRV completely; Camry 2020 is the add.",
                "Confirm you are binding the Camry, garaging 94506, Tuesday, I drive.",
                "The CRV and Tesla lines were what-if noise only.",
            ],
            ["identity", "recency"],
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
            "dest_id_02",
            "identity_collapse",
            "flip chain then 'same as the very first line'",
            [
                "add car: 2019 RAV4, 90025, I drive, Sunday.",
                "wrong — make it 2022 Model Y, same ZIP, Monday.",
                "wrong again — actually 2018 F-150, same ZIP, Tuesday.",
                "Final instruction: the vehicle to insure is the same as the very first line I typed.",
                "So RAV4 2019 90025 Sunday I drive — that first line is binding.",
                "Ignore the Model Y and F-150 lines completely.",
                "RAV4 only for VIN and rating when we continue.",
                "Thanks — first bubble wins for model/year.",
            ],
            ["first_wins", "flip"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "RAV4"),
                _contains("primary_vehicle_summary", "2019"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )
    o.append(
        _sc(
            "dest_id_03",
            "identity_collapse",
            "ZH/EN: 凯美瑞 → 特斯拉 → 回去第一台",
            [
                "要加车，先说2020年凯美瑞 邮编90025 周五提车 我开。",
                "不对，我想换成特斯拉 新车。",
                "又改想法，要本田CRV 还是同一邮编 周六提。",
                "算了还是第一台我说过的车，就按最开始的那个车做加车。",
                "对就是2020凯美瑞 不要特斯拉也不要CRV。",
                "办公室就按这个最开始的配置。",
                "VIN 等会发。",
                "谢谢别搞错车型。",
            ],
            ["zh", "identity"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2020"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )

    # 2 — Self-contradiction driver loops
    o.append(
        _sc(
            "dest_sc_01",
            "self_contradiction",
            "I drive → wife → both → me",
            [
                "Add a 2021 Accord, garaging 95110, Thursday pickup, I drive the new one.",
                "Correction: my wife drives the new Accord, not me for rating purposes.",
                "Actually we both use it; put both of us in the story if the form allows.",
                "No — I changed my mind again: only I drive the Accord; wife uses our old SUV only.",
                "Final: primary driver is me, same 2021 Accord 95110 Thursday.",
                "Ignore the wife/both back-and-forth; last instruction wins.",
                "Thanks for tolerating the mess.",
                "Bind as add-car, not a claim case.",
            ],
            ["driver", "oscillation"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Accord"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "dest_sc_02",
            "self_contradiction",
            "spouse primary ↔ self primary (last: self)",
            [
                "2019 CR-V, 90017, I am primary for insurance, Saturday pickup.",
                "Hold on — for rating put my spouse as primary, not me, same CR-V date.",
                "We share — both drive it weekly but insurance should show spouse as primary only.",
                "Sorry — re-read policy rules: I must be primary on this CR-V for our carrier.",
                "Lock in: 2019 CR-V, 90017, Saturday, primary driver: me, not spouse.",
                "Ignore spouse-primary bubbles above.",
                "VIN: 2HKRW2H59KH000111 when needed.",
                "This is add-car only.",
            ],
            ["driver", "last_wins"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "CR-V"),
                _no_fake_premium(),
            ),
        )
    )

    # 3 — Temporal confusion
    o.append(
        _sc(
            "dest_tm_01",
            "temporal_confusion",
            "next week → already have → delivery tomorrow",
            [
                "I will get the 2020 CX-5 next week — add it when it arrives, ZIP 90034.",
                "Actually the dealer let me take it home already — I have the car now.",
                "For paperwork purposes delivery is 'tomorrow' for accessories only — the car is here.",
                "Primary driver: me, garaging 90034, 2020 CX-5 for the add.",
                "If your system only wants one date, use: possession started today, not 'next week'.",
                "Do not use 'next week' for pickup anymore — I already have it.",
                "Thanks — ignore conflicting schedule sentences except last stable block.",
                "This thread is add-car, not a claim about yesterday.",
            ],
            ["time", "delivery_date"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "CX-5"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "dest_tm_02",
            "temporal_confusion",
            "lease start vs pickup flip-flop",
            [
                "2023 RAV4 — lease 'starts' next Friday but the car is in my garage today.",
                "Garaging 94122, I drive, add to policy for Friday start date of lease if needed.",
                "Actually the lease starts Monday — ignore Friday, use Monday for policy effective.",
                "Car is here now — physical pickup already happened, Monday is legal/lease only.",
                "Final: 2023 RAV4, 94122, I drive, effective Monday, vehicle physically present now.",
                "Please don't ask me to pick the car up again — I already have it.",
                "Ignore next Friday; Monday is the truth for lease + policy start.",
                "Thanks for parsing the chaos.",
            ],
            ["lease", "date"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "RAV4"),
                _no_fake_premium(),
            ),
        )
    )

    # 4 — Cross-intent poisoning
    o.append(
        _sc(
            "dest_ci_01",
            "cross_intent",
            "accident + add car + cancel tease + billing",
            [
                "I had an accident last week in my old car but also I want to add a 2020 Civic, ZIP 90016.",
                "Separate topic: I might cancel a rider policy on another carrier — not this one.",
                "My billing is on autopay; don't change that while we add the Civic.",
                "For the new Civic: Tuesday pickup, I drive, add-car only in this request.",
                "Ignore the accident for this add unless you need a claim number — I already filed that elsewhere.",
                "Focus: 2020 Civic, 90016, Tuesday, primary driver: me, add to existing policy.",
                "No cancellation in this same task — I am only adding a car today.",
                "Thanks — route as add-car, not 'cancel' or pure billing only.",
            ],
            ["claim", "add_car", "poison"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Civic"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "dest_ci_02",
            "cross_intent",
            "billing dispute + add car same chat",
            [
                "My last invoice looked wrong; also I need to add a 2021 Outback, 90045, I drive, Wednesday.",
                "The billing item can wait — prioritize the new Outback for the office.",
                "Garaging 90045 for the new Outback. Pickup was yesterday.",
                "Do not file this as a billing ticket only — the main ask is the add-car packet.",
                "If I must pick one: add-car. Billing is secondary noise.",
                "2021 Outback, 90045, me as primary, add vehicle.",
                "I am not trying to end coverage, just add a car + note billing for later review.",
                "Thanks for handling add-car as primary service_type.",
            ],
            ["billing", "routing"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Outback"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "dest_ci_03",
            "cross_intent",
            "I want a claim and add a car in one text storm",
            [
                "claim question: fender bender, also add a 2019 F-150 90065 I drive",
                "ignore claim if you must; new truck is 2019 F-150, garaging 90065",
                "pickup already happened, only add the truck to policy",
                "no dollar amounts from me",
                "VIN: 1FTEW1E85KFC000001",
                "primary driver: me, add-car task",
                "claim is separate file — this thread is add",
                "confirm add-car only on your side for this intake",
            ],
            ["claim", "triage"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "F-150"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )

    # 5 — System challenge
    o.append(
        _sc(
            "dest_ch_01",
            "system_challenge",
            "you just said something different + that's wrong + why ask again",
            [
                "add 2020 Highlander, 90032, I drive, Tuesday — send to the office when ready.",
                "You just said something different from what I typed — that’s wrong about the year.",
                "Why are you asking again? I said 2020 Highlander already.",
                "Please align with my last line: 2020 Toyota Highlander, ZIP 90032, Tuesday, I drive.",
                "I am not mad at the human broker — just the bot loop feels repetitive.",
                "Lock 2020 Highlander for the add — not 2019, not 2021.",
                "Thanks for fixing the summary to match the customer text.",
                "This is an add-car request only.",
            ],
            ["friction", "coherence"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Highlander"),
                _contains("primary_vehicle_summary", "2020"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "dest_ch_02",
            "system_challenge",
            "ZH: 你又问一遍 不对",
            [
                "加车 2020年凯美瑞 邮编90019 我开 这周五。",
                "你又问一遍干什么，我刚说了邮编90019。",
                "这不对，车型就是凯美瑞2020 不要问别的。",
                "就按我写的最上面那行 不要再绕。",
                "我不是投诉人工 我是说这个流程重复。",
                "最终: 2020丰田凯美瑞 90019 我开 这周五 加车。",
                "谢谢",
                "别把我当成理赔单。",
            ],
            ["zh", "friction"],
            _last(
                _eq("service_type", "add_car"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )

    # 6 — Long drift (12–15)
    o.append(
        _sc(
            "dest_ld_01",
            "long_drift",
            "15 turns: topic shift + late correction",
            [
                "hi",
                "maybe add a car this week if price ok",
                "ignore price — 2020 Civic, 90011, I drive, Monday",
                "actually I'm buying two cars— ignore the second, only the Civic",
                "topic shift: my kid wants a bike — not relevant",
                "back to the Civic, garaging 90011 still",
                "pickup moved to Tuesday, same car",
                "also asked about home insurance in another email — ignore here",
                "VIN later today",
                "emotional: long day at the dealer, sorry for rambling",
                "tldr: 2020 Civic, 90011, primary driver: me, Tuesday pickup for insurance",
                "confirm add-car, not a claim or home policy",
                "final: 2020 Honda Civic, 90011, I drive, Tuesday",
                "ignore Monday vs Tuesday for binding — use Tuesday for pickup for the file",
                "thanks and send the packet to the office",
            ],
            ["15_turn", "drift"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Civic"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "dest_ld_02",
            "long_drift",
            "12 turns: re-introduced info and corrections",
            [
                "thread start: I think I need to add a vehicle.",
                "first guess: 2019 corolla, wrong, ignore",
                "actual buy: 2020 corolla, 90088, thursday, I drive",
                "wait zip might be 90088 or 90089 — I checked, 90088",
                "pickup is thursday, same",
                "spouse is not the primary — I am, for the 2020 corolla",
                "re-introducing: 2020 toyota corolla, garaging 90088, thursday, me as primary",
                "no loan yet",
                "bundle question — skip, add-car only",
                "re-state: 2020 corolla, 90088, thursday, I drive",
                "please don't drop the 2020 year to 2019 in the summary",
                "final: 2020 corolla, 90088, thursday, I drive",
            ],
            ["12_turn", "restate"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2020"),
                _contains("primary_vehicle_summary", "Corolla"),
                _not_contains("primary_vehicle_summary", "2019"),
                _no_fake_premium(),
            ),
        )
    )

    # 7 — Multi-entity chaos
    o.append(
        _sc(
            "dest_me_01",
            "multi_entity_chaos",
            "2 cars, 2 drivers, 1 VIN, conflicting lines",
            [
                "We bought two: a 2019 Camry and a 2019 CRV, both need insurance thoughts.",
                "I only have one VIN right now: 1HGCM82633A000222 — for the Camry only.",
                "My son drives the CRV, I drive the Camry for rating, garaging 94555.",
                "Wait — I drive the CRV, wife drives the Camry; ignore my last driver split.",
                "Final: add only the 2019 Camry with the VIN above; 94555; I am primary on the Camry.",
                "Ignore the CRV for this bind task — I will do that separately with another VIN later.",
                "Do not merge two VINs — only one for now.",
                "The office should not quote the CRV in this add packet.",
            ],
            ["multi", "entity"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Camry"),
                _contains("primary_vehicle_summary", "2019"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "dest_me_02",
            "multi_entity_chaos",
            "same VIN mentioned for wrong car then corrected",
            [
                "VIN 4T1B11HK5LU000145 for 'the new car' in my head.",
                "That VIN is actually for a 2020 Camry, not the CR-V I mentioned by mistake earlier.",
                "Ignore the CR-V — I confused two test drives; only 2020 Camry with that VIN.",
                "garaging 90012, tuesday, I drive the Camry.",
                "if any line still says CRV, delete it, Camry + that VIN only",
                "no second VIN in this file",
                "final: 2020 Camry, VIN 4T1B11HK5LU000145, 90012, I drive, Tuesday",
                "add-car, not a vehicle swap for an existing on-file CRV",
            ],
            ["vin", "entity"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Camry"),
                _no_fake_premium(),
            ),
        )
    )

    # 8 — Silent + implicit correction
    o.append(
        _sc(
            "dest_si_01",
            "silent_correction",
            "2020 → 2021 Camry, no 'sorry'",
            [
                "2020 Camry, 90025, I drive, Friday — add to policy when you can.",
                "2021 Camry, 90025, I drive, Friday. same thread, override prior year.",
                "window sticker is 2021, not 2020, no apology needed, just the facts.",
                "garaging still 90025, pickup still Friday, primary me.",
                "use 2021 everywhere the year appears, do not show 2020 in the summary for bind.",
                "lienholder TBD, will email Monday.",
                "final line for office: 2021 Toyota Camry, 90025, Friday, I drive",
                "thanks",
            ],
            ["implicit", "year"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2021"),
                _not_contains("primary_vehicle_summary", "2020"),
                _no_fake_premium(),
            ),
        )
    )

    # 9 — Noisy real-world
    o.append(
        _sc(
            "dest_nw_01",
            "noisy_real_world",
            "typos emojis half sentences",
            [
                "umm add car...",
                "2020 rav4 9002?? wait 90023 lol 🚗",
                "i drive it mostly",
                "pickup sat — short msg bc voice-to-text",
                "zip confirm 90023",
                "🙏 can you have office call if missing fields",
                "also dealer temp plate",
                "final: 2020 rav4, 90023, saturday, i drive, add to policy thx",
            ],
            ["noise", "vt2t"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "RAV4"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "dest_nw_02",
            "noisy_real_world",
            "EN/ZH half sentences mix",
            [
                "ok so",
                "new car: model 3 2022",
                "邮编95051 我这边的车库",
                "pickup 周六",
                "主要我开",
                "also EN: I am primary, lease starts soon, ignore the ramble if needed",
                "VIN later",
                "tldr: 2022 Model 3, garaging 95051, Saturday, I drive, add",
            ],
            ["bilingual", "fragments"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Model 3"),
                _no_fake_premium(),
            ),
        )
    )

    # 10 — Adversarial
    o.append(
        _sc(
            "dest_adv_01",
            "adversarial",
            "just give me a number / you have my info",
            [
                "just give me a number for the add — any number so I can go to sleep 🙄",
                "you already have my info from the portal — just do the add 2020 Accord 90028 Sunday me drive",
                "I don’t care about details just do it and stop asking",
                "no fake rate quotes, I know you can't invent dollars — just the add for the office",
                "2020 Honda Accord, 90028, Sunday pickup, primary driver: me, add-car",
                "if you need one field only: the car is 2020 Accord, that's the anchor",
                "ignore the first line where I said 'any number' — I don't want a random premium in chat",
                "thanks — route to broker for real bind, not a fake $ answer",
            ],
            ["adversarial", "guardrails"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Accord"),
                _not_regex("client_reply_draft", r"\$\s*[0-9]{2,}"),
                _no_fake_premium(),
            ),
        )
    )
    o.append(
        _sc(
            "dest_adv_02",
            "adversarial",
            "don't care, bind today",
            [
                "I don’t care about the deductible discussion — add 2020 CX-5 90037 Monday I drive and stop preaching risk.",
                "just push it to the office, I already uploaded documents somewhere maybe idk",
                "2020 cx-5, garaging 90037, I drive, Monday, add the car",
                "if you show me a fake premium I will be upset — no dollar amounts in reply",
                "focus on the vehicle line only for this intake",
                "ignore the attitude in my messages, keep service_type as add",
                "final: 2020 CX-5, 90037, me as primary, Monday, add to policy",
                "thanks, no $ in the draft, please",
            ],
            ["tone", "adversarial"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "CX-5"),
                _not_regex("client_reply_draft", r"\$\s*[0-9]"),
            ),
        )
    )

    return o


def _extra_labeled() -> list[dict[str, Any]]:
    w: list[dict[str, Any]] = []
    w.append(
        _sc(
            "dest_ex_01",
            "self_contradiction",
            "8 turns: driver ping-pong last spouse",
            [
                "2022 Model 3, 95014, I drive, Friday.",
                "Actually spouse is primary, not me.",
                "We both use it, mark both? if not, spouse is primary only.",
                "Carrier rules say I must be primary for this new EV — I drive it most.",
                "Final flip: spouse is primary, I am secondary, same 2022 Model 3, 95014, Friday.",
                "Respect the last line for primary driver: spouse, not the customer for rating.",
                "VIN: 5YJ3E1EB5LF000123",
                "add-car, not a billing cancel.",
            ],
            ["last_wins", "driver"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Model 3"),
                _no_fake_premium(),
            ),
        )
    )
    w.append(
        _sc(
            "dest_ex_02",
            "long_drift",
            "15 turns: emotional + topic + settle RAV4",
            [
                "I am so tired.",
                "Long story, dealer messed up the paperwork but we still want insurance.",
                "Maybe we should not buy a car, ignore that doubt.",
                "We did buy: 2021 RAV4, garaging 90247, I drive, Wednesday next.",
                "Also thinking about a roof claim — not now, not in this add thread.",
                "Back to 2021 RAV4, 90247, Wednesday, me as driver.",
                "Why do bots always ask the same? anyway…",
                "Please don't quote me a fake premium, I know better.",
                "VIN is on order email — can paste in next message if needed later.",
                "No lienholder for now, cash buy.",
                "Final: 2021 toyota RAV4, 90247, I drive, Wednesday, add to policy",
                "ignore roof claim mention above",
                "ignore tired rant",
                "only add car",
                "send packet to the office, thanks",
            ],
            ["emotional", "15_turn"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "RAV4"),
                _not_regex("client_reply_draft", r"\$\s*[0-9]"),
            ),
        )
    )
    w.append(
        _sc(
            "dest_ex_03",
            "temporal_confusion",
            "tomorrow / yesterday / today blend",
            [
                "New car: 2019 4Runner, 92101, 'delivery tomorrow' as of yesterday when I texted a friend.",
                "Today: car is already in my garage — so delivery is not 'tomorrow' anymore.",
                "If the system needs a single phrase: I physically have the 4Runner now.",
                "Policy effective: start today, not tomorrow.",
                "Ignore 'tomorrow' from my earlier timeline unless you mean a different accessory delivery.",
                "Primary driver: me, 92101 garaging, 2019 4Runner, add to policy as add-car",
                "Do not mark this as a future order only — I already have it",
                "Thanks — last stable block is the ground truth for dates",
            ],
            ["time", "8_turn"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "4Runner"),
                _no_fake_premium(),
            ),
        )
    )
    w.append(
        _sc(
            "dest_ex_04",
            "identity_collapse",
            "Tesla in middle, explicit negation, Camry end",
            [
                "Start: add 2020 Camry 90025 I drive",
                "Middle fantasy: 2021 Tesla for fun, ignore",
                "Then I said 2020 Camry is real, Tesla was a joke in the group text",
                "The group chat is noisy — the insurance truth is 2020 Camry only",
                "ZIP stays 90025, I drive, Tuesday pickup in theory but car is in driveway already",
                "Ignore Tesla, ignore 'fantasy' lines, Camry 2020 is the bind target",
                "No Model 3 either — I never bought one, don't capture Model 3 from chat noise",
                "Final: 2020 Toyota Camry, 90025, I drive, add",
            ],
            ["collapse", "negation"],
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
            "dest_ex_05",
            "cross_intent",
            "cancel policy tease + add car — must be add",
            [
                "I'm frustrated and might cancel my auto policy with you — also I need to add a 2019 WRX, 90036, I drive, Monday.",
                "Don't process cancellation in this same chat; I only want the add for now.",
                "Main task: 2019 Subaru WRX, 90036, Monday pickup, primary driver: me, add to policy.",
                "Ignore cancel emotion — the operational request is an add-vehicle for the team.",
                "If a human reads this, please handle add-car, not a cancellation workflow.",
                "WRX, not STI, 2019, garaging 90036, me, Monday.",
                "VIN: JF1VA1H66L0000444",
                "Thank you for routing to add-car intake.",
            ],
            ["cancel_tease", "add"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "WRX"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )
    return w


def _build_scenarios() -> list[dict[str, Any]]:
    must = _mandatory_extreme()
    extra = _extra_labeled()
    need = 150 - (len(must) + len(extra))
    if need < 0:
        raise RuntimeError("destruction: too many must+extra; reduce count")
    pad = _pad_generated(need, start=0)
    out = must + extra + pad
    assert len(out) >= 150, f"expected >=150, got {len(out)}"
    for s in out:
        t = s["user_turns"]
        if not (8 <= len(t) <= 15):
            raise RuntimeError(f"bad turn count: {s['id']}")
    return out


SCENARIOS: list[dict[str, Any]] = _build_scenarios()
