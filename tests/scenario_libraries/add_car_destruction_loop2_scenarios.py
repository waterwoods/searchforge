"""
Evolution loop 2: harder add-car destruction (8–15 turns).

New stress themes vs wave 1:
* trim-level whiplash (LE vs XLE named without “sorry”)
* policy number / claim number noise next to VIN
* pronominal “that one / the new one” with late resolution
* multi-ZIP chaos with “USPS said”
* implicit single-truth without “final:”
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
    assert 8 <= len(user_turns) <= 15
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


def _eq(field: str, value: Any) -> dict[str, Any]:
    return {"op": "eq", "field": field, "value": value}


def _contains(field: str, value: str) -> dict[str, Any]:
    return {"op": "contains", "field": field, "value": value}


def _not_contains(field: str, value: str) -> dict[str, Any]:
    return {"op": "not_contains", "field": field, "value": value}


def _not_regex(field: str, pattern: str) -> dict[str, Any]:
    return {"op": "not_regex", "field": field, "pattern": pattern}


def _no_fake_premium() -> dict[str, Any]:
    return _not_regex("client_reply_draft", r"\$\s*[0-9]")


def _build() -> list[dict[str, Any]]:
    s: list[dict[str, Any]] = []
    s.append(
        _sc(
            "dl2_t_01",
            "trim_whiplash",
            "LE then XLE silent — last trim wins",
            [
                "add car: 2020 highlander LE, 90045, I drive, Monday pickup if it matters for trim",
                "dealer upgraded us on the lot to XLE same color",
                "same VIN, same thread — insurance should say XLE not LE",
                "don’t be mad at the dealer, just update trim tier on your side",
                "garaging still 90045, still Monday, still me as primary",
                "the LE line in turn 1 is obsolete",
                "XLE 2020 Highlander, 90045, I drive, Monday, add to policy",
                "no fake premium in chat, thanks",
            ],
            ["trim", "implicit"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2020"),
                _contains("primary_vehicle_summary", "Highlander"),
                _not_regex("client_reply_draft", r"\$\s*[0-9]{2,}"),
            ),
        )
    )
    s.append(
        _sc(
            "dl2_pol_01",
            "id_poisoning",
            "policy # and claim # near VIN — still add-car",
            [
                "add my new car, policy # CA1234567 if your portal needs a reference, not a claim",
                "VIN: 1HGCM82633A009999 (new purchase), ignore claim # CLM-2019-888 from my old case",
                "car: 2019 accord, garaging 94112, tuesday, I drive",
                "if you get confused, bind on VIN+garaging+driver, not the old claim",
                "this is add-vehicle, not re-open a claim on that claim number",
                "thanks",
                "final: 2019 accord 94112 tuesday I drive, add to policy",
                "no dollar amounts in reply please",
            ],
            ["id_noise", "routing"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Accord"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )
    s.append(
        _sc(
            "dl2_pron_01",
            "pronominal_late",
            "that one / the new one then reveal accord",
            [
                "hi, I need to insure that one I bought",
                "the new one, not the old suv",
                "you know, the new one in my driveway, garaging 90033",
                "ok specifics: 2020 honda accord, I drive, wednesday pickup in my head for paperwork",
                "when I said that one, I meant the accord only",
                "old suv stays on the policy for now, different task",
                "accord 2020 90033 wednesday, add",
                "thanks — don’t price the old suv in this thread",
            ],
            ["pronoun", "late_bind"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Accord"),
                _no_fake_premium(),
            ),
        )
    )
    s.append(
        _sc(
            "dl2_zip_01",
            "multi_zip",
            "90210 then 90025 usps then final 90025",
            [
                "2020 civic, garaging 90210, I drive, Friday, add",
                "wait USPS said my ZIP might be 90025 for this house",
                "ignore 90210, it was my work brain",
                "I triple-checked: 90025 is the garage for rating for this civic",
                "same car, same Friday, me as driver, only garaging string changes",
                "if your system can only have one, use 90025",
                "final: 2020 civic 90025 Friday me drive, add to policy",
                "thanks, no $ figures",
            ],
            ["zip", "4_turn"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Civic"),
                _not_contains("primary_vehicle_summary", "2021"),
            ),
        )
    )
    s.append(
        _sc(
            "dl2_zh_01",
            "zh_implicit_truth",
            "no“final”label — last line is truth 2021 rav4",
            [
                "在吗。",
                "要加车。",
                "一开始我说2020 rav4 不对 那是口误。",
                "我其实是2021荣放 你按2021。",
                "邮编90027。",
                "这周六提车 主要我开。",
                "不要给我凑金额数字。",
                "谢谢就按我最后说的那套。",
            ],
            ["zh", "implicit"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "2021"),
                _contains("primary_vehicle_summary", "RAV4"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )
    s.append(
        _sc(
            "dl2_edge_01",
            "sibling_rivalry",
            "brother's pilot vs my civic — VIN for civic only",
            [
                "my brother and I each bought cars; I'm only adding the civic on my policy today.",
                "his pilot is a different VIN, don't mix them — pilot is not in this add.",
                "VIN: 1HGCV1F34MA000555 for the 2020 civic, garaging 90031, thursday, I drive",
                "if a line mentions pilot, treat it as context only, not a second bind",
                "only quote/bind the 2020 civic on this request",
                "zip is home garage 90031 for the civic",
                "ignore pilot trim packages — not today",
                "thanks, add-car only",
            ],
            ["multi", "vin_scope"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Civic"),
                _not_contains("primary_vehicle_summary", "Pilot"),
            ),
        )
    )
    for i in range(30):
        n = 8 + (i % 8)
        lines = [f"loop2 pad seed {i} — add a car today please."]
        y = 2019 + (i % 5)
        models = [
            ("Camry", f"{y} Toyota Camry", "90001"),
            ("Accord", f"{y} Honda Accord", "90002"),
            ("RAV4", f"{y} Toyota RAV4", "90003"),
        ]
        tok, mline, z = models[i % 3]
        for k in range(n - 1):
            if k == 0:
                lines.append(f"Dealer says {mline} for the main purchase.")
            elif k == 1:
                lines.append(f"garaging {z} for rating.")
            elif k == 2:
                lines.append("I drive, pickup next week, ignore my podcast rant below.")
            elif k == 3:
                lines.append("podcast: interest rates are wild — not relevant to the car add.")
            else:
                lines.append(
                    f"restate {k}: {mline} {z} I drive, add to policy, ignore noise in prior bubbles."
                )
        lines = lines[:n]
        s.append(
            _sc(
                f"dl2_p_{i+1:02d}",
                "loop2_pad",
                f"pad {n}-turn {tok}",
                lines,
                ["pad2", "stable"],
                _last(
                    _eq("service_type", "add_car"),
                    _contains("primary_vehicle_summary", str(y)),
                    _contains("primary_vehicle_summary", tok),
                    _no_fake_premium(),
                ),
            )
        )
    return s


SCENARIOS: list[dict[str, Any]] = _build()
