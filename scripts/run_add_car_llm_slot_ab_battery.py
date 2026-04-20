#!/usr/bin/env python3
"""
Bounded Add-Car LLM slot layer A/B battery (backend multi-turn).

Runs selected add_car_quote scenarios from customer_entry_multi_turn_simulations.json
and prints per-turn metrics for comparing ADD_CAR_LLM_SLOT_EXTRACTION=0 vs 1.

Usage:
  LLM_GENERATION_ENABLED=0 ADD_CAR_LLM_SLOT_EXTRACTION=0 PYTHONPATH=. python3 scripts/run_add_car_llm_slot_ab_battery.py
  LLM_GENERATION_ENABLED=0 ADD_CAR_LLM_SLOT_EXTRACTION=1 PYTHONPATH=. python3 scripts/run_add_car_llm_slot_ab_battery.py

Requires OPENAI_API_KEY (or LLM_API_KEY) in env for mode B to invoke the slot model.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_conversation

CONFIG = REPO / "configs" / "customer_entry_multi_turn_simulations.json"

# Bounded messy / multi-turn Add-Car set (see sprint 02_AB_BATTERY_SPEC.md)
DEFAULT_SCENARIO_IDS = (
    "MT1",
    "MT11",
    "MT13",
    "MT43",
    "MT45",
    "MT46",
    "MT44",
    "ACE02",
)


def load_sims(ids: tuple[str, ...]) -> list[dict]:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in data.get("simulations", [])}
    out = []
    for i in ids:
        if i not in by_id:
            print(f"WARN: missing scenario {i}", file=sys.stderr)
            continue
        out.append(by_id[i])
    return out


def run_sim(sim: dict) -> dict:
    sim_id = sim.get("id", "?")
    turns = [t for t in sim.get("turns", []) if (t.get("role") or "").lower() == "customer"]
    conv: list[dict[str, str]] = []
    per_turn: list[dict] = []
    slot_calls = 0
    slot_accepted_any = 0

    for idx, t in enumerate(turns):
        text = (t.get("text") or "").strip()
        if not text:
            continue
        r = triage_conversation(text, conv)
        layer = r.get("add_car_llm_slot_layer") or {}
        if layer.get("called"):
            slot_calls += 1
        acc = layer.get("accepted_slots") or []
        if acc:
            slot_accepted_any += 1
        per_turn.append(
            {
                "turn": idx + 1,
                "customer_len": len(text),
                "handoff_ready": bool(r.get("handoff_ready")),
                "still_needed_n": len(r.get("still_needed_fields") or []),
                "still_needed": list(r.get("still_needed_fields") or []),
                "collected_n": len(r.get("collected_fields") or []),
                "collected": sorted(str(x) for x in (r.get("collected_fields") or [])),
                "quote_ready_status": r.get("quote_ready_status"),
                "slot_called": bool(layer.get("called")),
                "slot_skip": layer.get("skip_reason"),
                "slot_accepted": list(acc),
                "slot_certainty": layer.get("certainty"),
                "slot_error": layer.get("error"),
            }
        )
        sys_reply = r.get("client_reply_draft") or ""
        conv.append({"role": "customer", "text": text})
        conv.append({"role": "system", "text": sys_reply})

    handoff_turn = next((x["turn"] for x in per_turn if x["handoff_ready"]), None)
    return {
        "id": sim_id,
        "name": sim.get("name", ""),
        "expected_handoff_after_turn": sim.get("expected_handoff_after_turn"),
        "handoff_ready_at_turn": handoff_turn,
        "slot_api_calls": slot_calls,
        "turns_with_accepted_slots": slot_accepted_any,
        "per_turn": per_turn,
    }


def main() -> int:
    slot_flag = os.environ.get("ADD_CAR_LLM_SLOT_EXTRACTION", "").strip().lower() in ("1", "true", "yes", "on")
    llm_gen = os.environ.get("LLM_GENERATION_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")
    has_key = bool(
        (os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY") or "").strip()
    )
    sims = load_sims(DEFAULT_SCENARIO_IDS)
    out = {
        "mode": "B_slot_on" if slot_flag else "A_slot_off",
        "llm_generation_enabled": llm_gen,
        "add_car_llm_slot_extraction": slot_flag,
        "api_key_present": has_key,
        "scenarios": [run_sim(s) for s in sims],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
