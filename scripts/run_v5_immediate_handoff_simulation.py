#!/usr/bin/env python3
"""
V5 Immediate Handoff Engine — multi-session simulation, variant comparison, self-evolution loops.

Does not start HTTP; calls triage_conversation directly. Uses INTAKE_EVOLUTION_VARIANT for A/B/C.
"""

from __future__ import annotations

import json
import os
import random
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.fiqa_api.inbox_triage import case_draft_engine as cde
import services.fiqa_api.inbox_triage.triage as triage_mod
from services.fiqa_api.inbox_triage.triage import triage_conversation

# Rule-only triage for fast, deterministic simulation (no OpenAI).
triage_mod._is_llm_enabled = lambda: False  # type: ignore[method-assign]


@dataclass
class SessionResult:
    variant: str
    persona: str
    turns_to_handoff: int | None
    handoff: bool
    user_chars: int
    case_usable_t2: bool
    risk: float
    quote_ready_t2: bool


@dataclass
class BatchMetrics:
    variant: str
    handoff_rate: float = 0.0
    median_turns: float = 0.0
    mean_effort: float = 0.0
    mean_usability: float = 0.0
    mean_risk: float = 0.0
    n: int = 0
    sessions: list[SessionResult] = field(default_factory=list)


# --- Scripted personas (deterministic; avoids LLM) ---------------------------------

PERSONA_MESSAGES: dict[str, tuple[str, str]] = {
    "minimal_en": (
        "add car 2024 Honda Accord zip 92648",
        "ok",
    ),
    "sparse_zh": (
        "加车 2023 凯美瑞 邮编 94102",
        "好",
    ),
    "medium_en": (
        "I need insurance for a new car — 2022 Tesla Model 3, garaging zip 95112, picking up Friday, I am the driver",
        "yes",
    ),
    "rich_zh": (
        "加车 VIN LRWYGCFS5PC123456 邮编 91001 下周三提车 主驾是我本人 2024 Model Y",
        "好的",
    ),
    "noisy_en": (
        "hey can you quote adding a vehicle its a bmw x3 2021 zip is 94501 not sure about vin yet delivery soon",
        "ok thanks",
    ),
}


def _run_session(variant: str, persona: str, rng: random.Random) -> SessionResult:
    m1, m2 = PERSONA_MESSAGES[persona]
    # Light noise so effort score varies
    noise = rng.choice(["", " ", " thanks", " 谢谢"])
    os.environ["INTAKE_EVOLUTION_VARIANT"] = variant
    t1 = triage_conversation(m1 + noise, [], client_id="chen_kui")
    user_chars = len(m1 + noise)
    turns = 1
    handoff = bool(t1.get("handoff_ready"))
    risk = float((t1.get("v5_handoff_risk_score") or t1.get("v4_error_risk_score") or 0.0) or 0.0)
    cu = bool(t1.get("case_usable"))
    qr = str(t1.get("quote_ready_status") or "") == "quote_ready"

    if not handoff:
        user_chars += len(m2)
        turns = 2
        t2 = triage_conversation(
            m2,
            [{"role": "customer", "text": m1 + noise}],
            client_id="chen_kui",
            prior_workflow_state={
                "conversion_stage": t1.get("conversion_stage"),
                "last_conversion_turn_index": t1.get("last_conversion_turn_index"),
            },
        )
        handoff = bool(t2.get("handoff_ready"))
        risk = float((t2.get("v5_handoff_risk_score") or t2.get("v4_error_risk_score") or 0.0) or 0.0)
        cu = bool(t2.get("case_usable"))
        qr = str(t2.get("quote_ready_status") or "") == "quote_ready"

    return SessionResult(
        variant=variant,
        persona=persona,
        turns_to_handoff=turns if handoff else None,
        handoff=handoff,
        user_chars=user_chars,
        case_usable_t2=cu,
        risk=risk,
        quote_ready_t2=qr,
    )


def _aggregate(batch: BatchMetrics) -> None:
    xs = batch.sessions
    batch.n = len(xs)
    if not xs:
        return
    batch.handoff_rate = sum(1 for s in xs if s.handoff) / len(xs)
    done = [s.turns_to_handoff for s in xs if s.turns_to_handoff is not None]
    batch.median_turns = float(statistics.median(done)) if done else 0.0
    batch.mean_effort = statistics.mean(s.user_chars for s in xs) if xs else 0.0
    batch.mean_usability = statistics.mean(1.0 if s.case_usable_t2 else 0.0 for s in xs) if xs else 0.0
    batch.mean_risk = statistics.mean(s.risk for s in xs) if xs else 0.0


def _simulate_variant(
    variant: str,
    n_sessions: int,
    rng: random.Random,
    personas: list[str],
) -> BatchMetrics:
    bm = BatchMetrics(variant=variant)
    for _ in range(n_sessions):
        p = rng.choice(personas)
        bm.sessions.append(_run_session(variant, p, rng))
    _aggregate(bm)
    return bm


def _print_comparison(batches: list[BatchMetrics], label: str) -> None:
    print(f"\n=== {label} ===")
    for b in batches:
        print(
            json.dumps(
                {
                    "variant": b.variant,
                    "n": b.n,
                    "handoff_rate": round(b.handoff_rate, 4),
                    "median_turns": b.median_turns,
                    "mean_user_chars": round(b.mean_effort, 1),
                    "case_usable_proxy": round(b.mean_usability, 4),
                    "mean_error_risk": round(b.mean_risk, 4),
                },
                ensure_ascii=False,
            )
        )


def main() -> None:
    rng = random.Random(42)
    personas = list(PERSONA_MESSAGES.keys())
    n_per = 120
    cycles: list[dict[str, Any]] = []

    # --- Cycle 1: production thresholds ---
    b1 = [
        _simulate_variant("A", n_per, rng, personas),
        _simulate_variant("B", n_per, rng, personas),
        _simulate_variant("C", n_per, rng, personas),
    ]
    _print_comparison(b1, "V5_VARIANT_COMPARISON — cycle 1 (baseline thresholds)")
    cycles.append({"cycle": 1, "batches": b1})

    _orig_thr = cde.v5_completeness_threshold

    # --- Cycle 2: lower B only (aggressive experiment; wraps production thresholds) ---
    def _thr_c2(v: str) -> float:
        b = _orig_thr(v)
        if (v or "").strip().upper() == "B":
            return max(0.4, b - 0.06)
        return b

    with patch.object(cde, "v5_completeness_threshold", side_effect=_thr_c2):
        b2 = [
            _simulate_variant("A", n_per, rng, personas),
            _simulate_variant("B", n_per, rng, personas),
            _simulate_variant("C", n_per, rng, personas),
        ]
    _print_comparison(b2, "V5_VARIANT_COMPARISON — cycle 2 (B threshold −0.06 vs production)")
    cycles.append({"cycle": 2, "batches": b2})

    # --- Cycle 3: nudge A upward (fewer false handoffs if risk too high in pilot) ---
    def _thr_c3(v: str) -> float:
        b = _orig_thr(v)
        if (v or "").strip().upper() == "A":
            return min(0.85, b + 0.04)
        return b

    with patch.object(cde, "v5_completeness_threshold", side_effect=_thr_c3):
        b3 = [
            _simulate_variant("A", n_per, rng, personas),
            _simulate_variant("B", n_per, rng, personas),
            _simulate_variant("C", n_per, rng, personas),
        ]
    _print_comparison(b3, "V5_VARIANT_COMPARISON — cycle 3 (A threshold +0.04 vs production)")

    base_a = b1[0].handoff_rate
    best = min(b1, key=lambda x: x.mean_risk)  # prefer lower risk at saturated handoff
    print(
        "\n=== AUTO_DECISION ===\n",
        f"cycle1 A handoff_rate={base_a:.4f}; lowest risk variant={best.variant} (risk={best.mean_risk:.4f}). "
        "When handoff_rate saturates, prefer lower v5_handoff_risk_score.",
    )


if __name__ == "__main__":
    main()
