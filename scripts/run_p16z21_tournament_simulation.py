#!/usr/bin/env python3
"""
P16-Z21 Customer Builder Evolution Tournament — 10 Add-Car scenarios × 3 paths.

Reuses P16-Z20 triage engine + scoring. Path A/B/C are UI-only; engine scores identical.
Path deltas applied from documented UX/commercial model (no new framework).

Usage:
  PYTHONPATH=. LLM_GENERATION_ENABLED=0 python3 scripts/run_p16z21_tournament_simulation.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.environ.setdefault("LLM_GENERATION_ENABLED", "0")

# Reuse P16-Z20 runner
from scripts.run_p16z20_add_car_simulation import (  # noqa: E402
    SCENARIOS_PATH,
    _run_scenario,
    _score_case_quality,
)

OUT_DIR = REPO / "docs" / "product_constitution" / ".p16z21_results"
OUT_PATH = OUT_DIR / "tournament_results.json"

# First 10 Add-Car scenarios (AC01–AC10)
SCENARIO_IDS = [f"AC{i:02d}" for i in range(1, 11)]

# Path UX deltas (0–100 scale adjustments vs default baseline)
PATH_DELTAS = {
    "minimal": {
        "customer_friction": +12,  # lower friction = higher score
        "adoption_risk": +8,
        "minutes_saved_customer": +0.3,
        "broker_confidence": 0,
        "case_quality": 0,
        "engineering_cost": +15,  # cheaper to ship
        "commercial_readiness": +5,
    },
    "guided": {
        "customer_friction": +5,
        "adoption_risk": +12,
        "minutes_saved_customer": +0.8,
        "broker_confidence": +3,
        "case_quality": +2,
        "engineering_cost": -8,
        "commercial_readiness": +8,
    },
    "timeline": {
        "customer_friction": +3,
        "adoption_risk": +6,
        "minutes_saved_customer": +0.2,
        "broker_confidence": +2,
        "case_quality": 0,
        "engineering_cost": -5,
        "commercial_readiness": +10,  # closes return-later gap visually
    },
}

# Broker simulation penalties (from P16Z20)
WECHAT_REOPEN_IDS = {"AC11", "AC12"}


def _broker_sim(scenario_id: str, quality: int, handoff_ready: bool) -> dict:
    need_wechat = scenario_id in WECHAT_REOPEN_IDS or quality < 50
    quote_now = handoff_ready and quality >= 80
    clarity = min(100, quality + 5)
    completeness = quality
    confidence = 100 if quote_now and not need_wechat else max(50, quality - 10)
    manual_min = 6.8
    builder_min = 1.0 if need_wechat else 0.7
    gross_saved = round(manual_min - builder_min, 1)
    net_saved = round(gross_saved - (1.2 if need_wechat else 0), 1)
    return {
        "need_wechat": need_wechat,
        "quote_immediately": quote_now,
        "clarity": clarity,
        "completeness": completeness,
        "confidence": confidence,
        "minutes_saved_gross": gross_saved,
        "minutes_saved_net": net_saved,
    }


def _founder_gate(scenario_id: str, quality: int, broker: dict) -> bool:
    if quality < 70:
        return False
    if broker["need_wechat"] and quality < 80:
        return False
    if broker["confidence"] < 70:
        return False
    return True


def _path_scores(base: dict, path: str) -> dict:
    d = PATH_DELTAS[path]
    q = base["case_quality"]
    b = base["broker"]
    return {
        "case_quality": min(100, q + d["case_quality"]),
        "need_wechat": b["need_wechat"],
        "broker_confidence": min(100, b["confidence"] + d["broker_confidence"]),
        "minutes_saved": round(b["minutes_saved_net"] + d["minutes_saved_customer"], 1),
        "customer_friction": min(100, 72 + d["customer_friction"]),
        "engineering_cost": min(100, 85 + d["engineering_cost"]),
        "commercial_readiness": min(
            100,
            int(
                (min(100, q + d["case_quality"]) * 0.25)
                + ((0 if b["need_wechat"] else 100) * 0.15)
                + (min(100, b["confidence"] + d["broker_confidence"]) * 0.2)
                + (min(100, 72 + d["customer_friction"]) * 0.15)
                + (min(100, 85 + d["engineering_cost"]) * 0.1)
                + 15
            ),
        ),
    }


def main() -> int:
    payload = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in payload["scenarios"]}
    scenarios = [by_id[sid] for sid in SCENARIO_IDS if sid in by_id]

    engine_rows: list[dict] = []
    for sc in scenarios:
        result = _run_scenario(sc)
        final = result["final"]
        quality, notes = _score_case_quality(sc, final)
        broker = _broker_sim(sc["id"], quality, bool(final.get("handoff_ready")))
        engine_rows.append(
            {
                "id": sc["id"],
                "title": sc.get("title"),
                "case_quality": quality,
                "service_type": final.get("service_type"),
                "handoff_ready": final.get("handoff_ready"),
                "broker": broker,
                "founder_pass": _founder_gate(sc["id"], quality, broker),
                "quality_notes": notes,
            }
        )

    paths = {}
    for path in ("minimal", "guided", "timeline"):
        rows = []
        for er in engine_rows:
            ps = _path_scores(er, path)
            rows.append({"id": er["id"], **ps})
        paths[path] = {
            "scenarios": rows,
            "averages": {
                k: round(sum(r[k] for r in rows) / len(rows), 1)
                for k in (
                    "case_quality",
                    "broker_confidence",
                    "minutes_saved",
                    "customer_friction",
                    "engineering_cost",
                    "commercial_readiness",
                )
            },
            "need_wechat_count": sum(
                1
                for er in engine_rows
                if er["broker"]["need_wechat"]
            ),
            "founder_pass_count": sum(1 for er in engine_rows if er["founder_pass"]),
        }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "scenario_ids": SCENARIO_IDS,
        "engine_results": engine_rows,
        "paths": paths,
        "role_d_reference": {"reread": 82.6, "need_wechat": "0/10", "source": "P16Z10B local battery"},
    }
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("P16-Z21 Tournament Simulation (AC01–AC10)")
    print(f"Engine avg quality: {sum(r['case_quality'] for r in engine_rows) / len(engine_rows):.1f}")
    for path in ("minimal", "guided", "timeline"):
        avg = paths[path]["averages"]
        print(
            f"  Path {path}: commercial={avg['commercial_readiness']:.1f} "
            f"friction={avg['customer_friction']:.1f} eng={avg['engineering_cost']:.1f}"
        )
    print(f"Wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
