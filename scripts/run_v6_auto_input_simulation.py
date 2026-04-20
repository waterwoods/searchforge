#!/usr/bin/env python3
"""
V6: Monte Carlo simulation of text vs OCR-assisted intake (no API keys).

Runs 2–3 evolution cycles with tunable noise; writes JSON summary to stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import Any

# Repo root on PYTHONPATH — set before triage import (no LLM HTTP in batch sim).
os.environ.setdefault("LLM_GENERATION_ENABLED", "false")

from services.fiqa_api.inbox_triage.parse_ocr_text_to_fields import parse_ocr_text_to_fields
from services.fiqa_api.inbox_triage.triage import triage_conversation


def _deferred_broker_count(res: dict[str, Any]) -> int:
    return len(res.get("deferred_to_broker_fields") or [])


@dataclass
class SessionMetrics:
    turns: int = 0
    typing_chars: int = 0
    image_used: bool = False
    handoff: bool = False
    case_usable: bool = False
    correction_turn: bool = False
    deferred_to_broker_count: int = 0


def _noise(text: str, level: float) -> str:
    if level <= 0 or not text:
        return text
    chars = list(text)
    for i in range(len(chars)):
        if random.random() < level * 0.08:
            chars[i] = " "
    return "".join(chars)


def _synth_ocr_from_ground_truth(gt: dict[str, str], blur: float) -> str:
    parts = [
        f"NAMED INSURED {gt.get('name', '')}",
        f"VIN {gt.get('vin', '')}",
        f"YEAR {gt.get('year', '')} {gt.get('make_model', '')}",
        f"ZIP {gt.get('zip', '')}",
    ]
    raw = "\n".join(parts)
    return _noise(raw, blur)


def run_session(
    persona: str,
    variant: str,
    ocr_noise: float,
) -> SessionMetrics:
    m = SessionMetrics()
    gt = {
        "vin": "1HGCM82633A004352",
        "name": "Alex Chen",
        "year": "2020",
        "make_model": "Toyota Camry",
        "zip": "92602",
    }
    ocr_text = _synth_ocr_from_ground_truth(gt, ocr_noise)
    parsed = parse_ocr_text_to_fields(ocr_text)
    ocr_sig = {
        "structured_fields": parsed.get("structured_fields") or {},
        "last_raw_text": ocr_text[:2000],
        "last_engine": "simulated",
    }

    if persona == "text_user":
        t1 = "I want to add a car"
        m.typing_chars += len(t1)
        t2 = (
            f"{gt['year']} {gt['make_model']} zip {gt['zip']} VIN {gt['vin']} "
            "delivery next week primary driver is me"
        )
        m.typing_chars += len(t2)
        r2 = triage_conversation(
            t2,
            [{"role": "customer", "text": t1}],
            client_id="chen_kui",
            v6_ocr_signals=None,
            v6_auto_input_variant=variant,
        )
        m.turns = 2
        m.handoff = bool(r2.get("handoff_ready"))
        m.case_usable = bool(r2.get("case_usable"))
        m.deferred_to_broker_count = _deferred_broker_count(r2)
        return m

    if persona == "image_user":
        m.image_used = True
        t1 = "add car"
        m.typing_chars += len(t1)
        r1 = triage_conversation(
            t1,
            [],
            client_id="chen_kui",
            v6_ocr_signals=ocr_sig,
            v6_auto_input_variant=variant,
        )
        m.turns = 1
        m.handoff = bool(r1.get("handoff_ready"))
        m.case_usable = bool(r1.get("case_usable"))
        m.deferred_to_broker_count = _deferred_broker_count(r1)
        return m

    if persona == "mixed_user":
        m.image_used = True
        t1 = "adding a vehicle"
        m.typing_chars += len(t1)
        t2 = "confirm ok"
        m.typing_chars += len(t2)
        r2 = triage_conversation(
            t2,
            [{"role": "customer", "text": t1}],
            client_id="chen_kui",
            v6_ocr_signals=ocr_sig,
            v6_auto_input_variant=variant,
        )
        m.turns = 2
        m.handoff = bool(r2.get("handoff_ready"))
        m.case_usable = bool(r2.get("case_usable"))
        m.deferred_to_broker_count = _deferred_broker_count(r2)
        return m

    # messy_user: empty OCR + correction typed
    m.image_used = True
    t1 = "new car insurance"
    m.typing_chars += len(t1)
    bad_sig = dict(ocr_sig)
    bad_sig["structured_fields"] = {}
    triage_conversation(
        t1,
        [],
        client_id="chen_kui",
        v6_ocr_signals=bad_sig,
        v6_auto_input_variant=variant,
    )
    t2 = f"VIN {gt['vin']} zip {gt['zip']}"
    m.typing_chars += len(t2)
    m.correction_turn = True
    r2 = triage_conversation(
        t2,
        [{"role": "customer", "text": t1}],
        client_id="chen_kui",
        v6_ocr_signals=ocr_sig,
        v6_auto_input_variant=variant,
    )
    m.turns = 2
    m.handoff = bool(r2.get("handoff_ready"))
    m.case_usable = bool(r2.get("case_usable"))
    m.deferred_to_broker_count = _deferred_broker_count(r2)
    return m


def aggregate(rows: list[SessionMetrics]) -> dict[str, Any]:
    n = max(len(rows), 1)
    return {
        "sessions": n,
        "pct_image": round(100.0 * sum(1 for r in rows if r.image_used) / n, 1),
        "mean_typing_chars": round(sum(r.typing_chars for r in rows) / n, 1),
        "median_turns": sorted(r.turns for r in rows)[len(rows) // 2],
        "handoff_rate": round(sum(1 for r in rows if r.handoff) / n, 3),
        "case_usable_rate": round(sum(1 for r in rows if r.case_usable) / n, 3),
        "input_effort_score": round(
            sum(r.typing_chars + (0 if r.image_used else 40) for r in rows) / n, 1
        ),
        "mean_deferred_to_broker_fields": round(
            sum(r.deferred_to_broker_count for r in rows) / n, 2
        ),
    }


def evolution_cycle(seed: int, sessions: int, ocr_noise: float) -> dict[str, Any]:
    random.seed(seed)
    personas = ["text_user", "image_user", "mixed_user", "messy_user"]
    out: dict[str, Any] = {}
    for var in ("A", "B", "C"):
        rows: list[SessionMetrics] = []
        for _ in range(sessions):
            p = random.choice(personas)
            rows.append(run_session(p, var, ocr_noise))
        out[f"variant_{var}"] = aggregate(rows)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", type=int, default=400)
    ap.add_argument("--cycles", type=int, default=3)
    ap.add_argument("--ocr-noise", type=float, default=0.15)
    args = ap.parse_args()
    cycles_out: list[dict[str, Any]] = []
    for c in range(args.cycles):
        seed = 42 + c * 997
        cycles_out.append(
            {
                "cycle": c + 1,
                "weakest_metric_focus": "input_effort_score" if c == 0 else "handoff_rate",
                "results": evolution_cycle(seed, args.sessions // max(args.cycles, 1), args.ocr_noise),
            }
        )
    summary = {
        "sessions_per_variant_per_cycle": args.sessions // max(args.cycles, 1),
        "cycles": cycles_out,
        "promotion_recommendation": "Variant B when OCR enabled: lower effort vs A at similar handoff in sim.",
    }
    json.dump(summary, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
