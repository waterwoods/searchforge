"""Evolution loop 3: adversarial follow-up + edge routing (8–12 turns). Themes: receipt ask, office hours, duplicate case tease."""
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


def _not_regex(field: str, pattern: str) -> dict[str, Any]:
    return {"op": "not_regex", "field": field, "pattern": pattern}


def _no_fake_premium() -> dict[str, Any]:
    return _not_regex("client_reply_draft", r"\$\s*[0-9]")


def _build() -> list[dict[str, Any]]:
    w: list[dict[str, Any]] = []
    w.append(
        _sc(
            "dl3_rc_01",
            "receipt_compete",
            "asks for office receipt style but must stay add_car",
            [
                "I need a receipt for the binder fee at the dealer — also add a 2021 CX-5, 90041, I drive, Sunday.",
                "Separate the receipt question from the add if you must, but my main task is the CX-5 add to policy.",
                "garaging 90041, 2021 Mazda CX-5, Sunday, me as primary driver.",
                "no premium numbers in chat",
                "if you can only do one workflow, do add-car first for the office queue",
                "VIN later from the dealer email",
                "thanks",
                "final: 2021 CX-5 90041 Sunday I drive",
            ],
            ["receipt", "add_car"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "CX-5"),
                _no_fake_premium(),
            ),
            soft_route="add_car",
        )
    )
    w.append(
        _sc(
            "dl3_dup_01",
            "duplicate_case_tease",
            "says I already opened a case but this is the real add line",
            [
                "I think I accidentally opened a duplicate case id in the portal — ignore that one.",
                "This chat is the real add: 2018 Corolla, 90019, Friday, I drive.",
                "Case number ABC-999 is garbage, don’t route on that.",
                "only 2018 corolla 90019 for the bind packet",
                "if your system merges threads, keep the corolla facts from this thread",
                "thanks",
                "no cancellation of my whole policy — just add a car",
                "appreciate it",
            ],
            ["dup", "routing"],
            _last(
                _eq("service_type", "add_car"),
                _contains("primary_vehicle_summary", "Corolla"),
                _no_fake_premium(),
            ),
        )
    )
    for i in range(18):
        n = 8 + (i % 5)
        y = 2020 + (i % 4)
        lines = [
            "Loop3 stress add-car thread start.",
            f"Vehicle: {y} Toyota Camry for the purchase story.",
            "Garaging 90210, I drive, pickup already happened in real life, ignore the drama below.",
        ]
        for j in range(3, n):
            lines.append(
                f"Reconfirm turn {j}: {y} Camry 90210 me as driver, add to policy, skip unrelated noise."
            )
        lines = lines[:n]
        w.append(
            _sc(
                f"dl3_p_{i+1:02d}",
                "loop3_pad",
                f"pad {n}-turn",
                lines,
                ["l3", "stable"],
                _last(
                    _eq("service_type", "add_car"),
                    _contains("primary_vehicle_summary", str(y)),
                    _contains("primary_vehicle_summary", "Camry"),
                    _no_fake_premium(),
                ),
            )
        )
    return w


SCENARIOS: list[dict[str, Any]] = _build()
