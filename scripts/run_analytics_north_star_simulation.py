#!/usr/bin/env python3
"""Simulate analytics scenarios; prints ANALYTICS_SIMULATION_RESULTS and CONVERSION_FLOW_V3_RESULTS."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.fiqa_api.analytics.funnel_events import emit_funnel_event, iter_funnel_events, reset_funnel_store
from services.fiqa_api.analytics.funnel_metrics import compute_dropoff_summary, compute_funnel
from services.fiqa_api.analytics.conversion_copy_ab import simulate_conversion_ab_batch
from services.fiqa_api.analytics.north_star_score import compute_north_star_score
from services.fiqa_api.analytics.triage_funnel import is_meaningful_customer_text


def _snap(**kwargs: object) -> dict:
    base = {
        "quote_ready_status": kwargs.get("quote_ready_status", "need_more"),
        "still_needed_fields": kwargs.get("still_needed_fields", ["zip"]),
        "collected_fields": kwargs.get("collected_fields", []),
        "next_best_question": kwargs.get("next_best_question", "请提供邮编。"),
        "client_reply_draft": kwargs.get("client_reply_draft", "还缺邮编。"),
        "handoff_ready": kwargs.get("handoff_ready", False),
        "triage_mode": "greenfield",
        "append_allowed": True,
        "conversion_stage": kwargs.get("conversion_stage", ""),
        "issue_category": "customer_question",
        "reroute_occurred": kwargs.get("reroute_occurred", False),
        "customer_turn_index": kwargs.get("customer_turn_index", 1),
        "customer_text_len": 20,
    }
    return base


def _run_scenario(name: str, build_events: Callable[[], None]) -> dict:
    reset_funnel_store()
    build_events()
    events = iter_funnel_events()
    by_session = {}
    for e in events:
        sid = e.get("session_id") or "anon"
        by_session.setdefault(sid, []).append(e)
    first_key = next(iter(by_session))
    score = compute_north_star_score(by_session[first_key], None)
    funnel = compute_funnel(events)
    return {"scenario": name, "score": score, "funnel_counts": funnel["counts"]}


# --- Conversion Flow V3: persona + probabilistic behavior (Part 6–8) -----------------

# Base categorical draw at quote_ready: hesitate 30%, drop 20%, question 20%, convert 30%
_BASE_OUTCOMES = (
    ("hesitate", 0.30),
    ("drop", 0.20),
    ("question", 0.20),
    ("convert", 0.30),
)

_PERSONA_BIAS: dict[str, dict[str, float]] = {
    "happy_user": {"convert": 0.22, "drop": -0.12, "question": -0.05, "hesitate": -0.05},
    "messy_user": {"question": 0.12, "hesitate": 0.08, "drop": 0.05, "convert": -0.25},
    "hesitant_user": {"hesitate": 0.18, "question": 0.08, "drop": 0.06, "convert": -0.32},
    "silent_user": {"drop": 0.14, "hesitate": 0.06, "convert": -0.12, "question": -0.08},
    "distrust_user": {"question": 0.15, "drop": 0.12, "convert": -0.22, "hesitate": -0.05},
}

# A/B/C: modeled intake evolution — B reaches quote_ready faster + slightly higher post-QR conversion;
# C adds confirmation friction (slightly slower, modest trust lift on convert).
_VARIANT_QR_PEAK_SHIFT: dict[str, float] = {"A": 0.0, "B": -1.25, "C": 0.35}
_VARIANT_POST_QR_CONVERT_BOOST: dict[str, float] = {"A": 0.0, "B": 0.05, "C": 0.025}
_VARIANT_COMPLETENESS_MEAN: dict[str, float] = {"A": 0.78, "B": 0.74, "C": 0.82}


def _draw_outcome(rng: random.Random, persona: str, *, variant: str) -> str:
    bias = dict(_PERSONA_BIAS.get(persona, {}))
    vb = _VARIANT_POST_QR_CONVERT_BOOST.get(variant, 0.0)
    bias["convert"] = bias.get("convert", 0.0) + vb
    weights = []
    names = []
    for name, w in _BASE_OUTCOMES:
        adj = max(0.01, w + bias.get(name, 0.0))
        names.append(name)
        weights.append(adj)
    s = sum(weights)
    weights = [x / s for x in weights]
    return rng.choices(names, weights=weights, k=1)[0]


def _simulate_persona_session(
    sid: str,
    cid: str,
    persona: str,
    rng: random.Random,
    *,
    v3_product: bool,
    variant: str = "A",
) -> dict[str, Any]:
    """Emit funnel events for one session; return timing + outcome metadata."""
    t0 = time.perf_counter()
    emit_funnel_event(
        "session_started",
        session_id=sid,
        metadata={"persona": persona, "v3": v3_product, "intake_variant": variant},
    )

    messy = persona == "messy_user" and rng.random() < 0.45
    if messy:
        from services.fiqa_api.analytics.funnel_events import append_session_analytics_event

        append_session_analytics_event("append_blocked", session_id=sid, metadata={})

    emit_funnel_event(
        "first_meaningful_input",
        session_id=sid,
        metadata={"customer_turn_index": 1, "case_snapshot": _snap(customer_turn_index=1, reroute_occurred=messy)},
    )
    emit_funnel_event(
        "case_created",
        session_id=sid,
        case_id=cid,
        metadata={"customer_turn_index": 2, "case_snapshot": _snap(customer_turn_index=2, reroute_occurred=messy)},
    )

    peak = 7 + _VARIANT_QR_PEAK_SHIFT.get(variant, 0.0)
    qr_turn = int(rng.triangular(3, 14, peak))
    if persona == "silent_user":
        qr_turn += int(rng.triangular(0, 6, 2))
    if persona == "hesitant_user":
        qr_turn += int(rng.triangular(0, 5, 2))

    emit_funnel_event(
        "quote_ready_reached",
        session_id=sid,
        case_id=cid,
        metadata={
            "customer_turn_index": qr_turn,
            "case_snapshot": _snap(
                quote_ready_status="quote_ready",
                still_needed_fields=["phone"] if rng.random() < 0.55 else [],
                collected_fields=["vin", "zip", "driver", "delivery"],
                next_best_question="",
                handoff_ready=True,
                customer_turn_index=qr_turn,
            ),
        },
    )

    outcome = _draw_outcome(rng, persona, variant=variant)
    converted = False
    extra_turns = 0

    if outcome == "drop":
        if persona == "distrust_user" and rng.random() < 0.35:
            emit_funnel_event(
                "first_meaningful_input",
                session_id=sid,
                metadata={
                    "customer_turn_index": qr_turn + 1,
                    "case_snapshot": _snap(
                        quote_ready_status="quote_ready",
                        still_needed_fields=["phone"],
                        handoff_ready=False,
                        customer_turn_index=qr_turn + 1,
                    ),
                },
            )
        converted = False
    elif outcome == "question":
        emit_funnel_event(
            "first_meaningful_input",
            session_id=sid,
            metadata={
                "customer_turn_index": qr_turn + 1,
                "case_snapshot": _snap(
                    quote_ready_status="quote_ready",
                    still_needed_fields=["phone"],
                    handoff_ready=True,
                    customer_turn_index=qr_turn + 1,
                ),
            },
        )
        extra_turns = 1
        # second draw: after question, may still convert or drop
        outcome2 = _draw_outcome(rng, persona, variant=variant)
        if outcome2 == "convert":
            converted = True
        elif outcome2 == "hesitate" and rng.random() < 0.55:
            converted = True
        else:
            converted = False
    elif outcome == "hesitate":
        extra_turns = int(rng.triangular(1, 4, 2))
        if rng.random() < (0.58 if v3_product else 0.40):
            converted = True
        else:
            converted = False
    else:
        converted = True

    if persona == "hesitant_user" and rng.random() < 0.18:
        converted = False
    if persona == "distrust_user" and outcome == "convert" and rng.random() < 0.25:
        converted = False

    if converted:
        emit_funnel_event(
            "handoff_started",
            session_id=sid,
            case_id=cid,
            metadata={
                "customer_turn_index": qr_turn + 1 + extra_turns,
                "case_snapshot": _snap(
                    quote_ready_status="quote_ready",
                    still_needed_fields=[],
                    handoff_ready=True,
                    conversion_stage="contact_received_ack" if v3_product else "user_engaged_after_ready",
                    customer_turn_index=qr_turn + 1 + extra_turns,
                ),
            },
        )
        if rng.random() < 0.72:
            emit_funnel_event(
                "handoff_confirmed",
                session_id=sid,
                case_id=cid,
                metadata={
                    "customer_turn_index": qr_turn + 2 + extra_turns,
                    "case_snapshot": _snap(
                        quote_ready_status="quote_ready",
                        still_needed_fields=[],
                        conversion_stage="handoff_confirmed",
                        handoff_ready=True,
                        customer_turn_index=qr_turn + 2 + extra_turns,
                    ),
                },
            )

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    completeness = max(
        0.55,
        min(
            0.97,
            _VARIANT_COMPLETENESS_MEAN.get(variant, 0.78)
            + rng.uniform(-0.06, 0.06)
            - 0.03 * max(0, qr_turn - 8),
        ),
    )
    effort = max(1, qr_turn + extra_turns + (0 if converted else 2))
    return {
        "persona": persona,
        "outcome": outcome,
        "converted": converted,
        "qr_turn": qr_turn,
        "extra_turns": extra_turns,
        "elapsed_ms": round(elapsed_ms, 3),
        "case_completeness_score": round(completeness, 4),
        "user_effort_score": effort,
        "variant": variant,
    }


def run_conversion_v3_monte_carlo(
    n_sessions: int,
    seed: int,
    *,
    v3_product: bool,
    variant: str = "A",
) -> dict[str, Any]:
    rng = random.Random(seed)
    personas = [
        "happy_user",
        "messy_user",
        "hesitant_user",
        "silent_user",
        "distrust_user",
    ]
    rows = []
    for i in range(n_sessions):
        p = personas[i % len(personas)]
        sid = f"v3-{i}-{p}-{variant}"
        cid = f"c-{i}"
        rows.append(
            _simulate_persona_session(sid, cid, p, rng, v3_product=v3_product, variant=variant)
        )

    events = iter_funnel_events()
    funnel = compute_funnel(events)
    rates = funnel.get("conversion_rates") or {}
    qr_to_ho = float(rates.get("quote_ready_to_handoff") or 0.0)

    sessions_with_qr = {e.get("session_id") for e in events if e.get("event") == "quote_ready_reached"}
    converted_sessions = {e.get("session_id") for e in events if e.get("event") == "handoff_started"}
    drop_rate = 1.0 - (len(converted_sessions & sessions_with_qr) / max(len(sessions_with_qr), 1))

    turn_to_conv = [r["qr_turn"] + r["extra_turns"] for r in rows if r["converted"]]
    median_turns = sorted(turn_to_conv)[len(turn_to_conv) // 2] if turn_to_conv else None

    by_persona: dict[str, dict[str, float]] = {}
    for p in personas:
        sub = [r for r in rows if r["persona"] == p]
        conv = sum(1 for r in sub if r["converted"])
        by_persona[p] = {
            "n": float(len(sub)),
            "handoff_rate": round(conv / max(len(sub), 1), 4),
        }

    scores = []
    by_session: dict[str, list] = {}
    for e in events:
        sid = e.get("session_id") or "anon"
        by_session.setdefault(sid, []).append(e)
    for sid, evs in by_session.items():
        scores.append(compute_north_star_score(evs, None)["total_score"])

    conv_rows = [r for r in rows if r["converted"]]
    median_effort = (
        sorted(r["user_effort_score"] for r in conv_rows)[len(conv_rows) // 2] if conv_rows else None
    )
    mean_complete = round(
        sum(r["case_completeness_score"] for r in rows) / max(len(rows), 1),
        4,
    )
    return {
        "n_sessions": n_sessions,
        "seed": seed,
        "v3_product": v3_product,
        "variant": variant,
        "quote_ready_to_handoff_rate": round(qr_to_ho, 4),
        "approx_dropoff_after_quote_ready": round(drop_rate, 4),
        "median_turns_to_handoff_among_converters": median_turns,
        "median_user_effort_among_converters": median_effort,
        "mean_case_completeness_score": mean_complete,
        "per_persona": by_persona,
        "north_star_score_mean": round(sum(scores) / max(len(scores), 1), 4),
        "funnel_counts": funnel.get("counts"),
    }


def run_variant_comparison_table(
    n_sessions: int,
    seed: int,
    *,
    v3_product: bool,
) -> dict[str, Any]:
    arms = ["A", "B", "C"]
    table = []
    for v in arms:
        reset_funnel_store()
        arm = run_conversion_v3_monte_carlo(n_sessions, seed + ord(v), v3_product=v3_product, variant=v)
        table.append(
            {
                "variant": v,
                "quote_ready_to_handoff_rate": arm["quote_ready_to_handoff_rate"],
                "approx_dropoff_after_quote_ready": arm["approx_dropoff_after_quote_ready"],
                "median_turns_to_handoff_among_converters": arm["median_turns_to_handoff_among_converters"],
                "median_user_effort_among_converters": arm["median_user_effort_among_converters"],
                "mean_case_completeness_score": arm["mean_case_completeness_score"],
                "north_star_score_mean": arm["north_star_score_mean"],
            }
        )
    return {"sessions_per_arm": n_sessions, "v3_product": v3_product, "rows": table}


def run_auto_evolution_loop(
    n_sessions: int,
    seed: int,
    *,
    v3_product: bool,
    max_cycles: int = 2,
) -> dict[str, Any]:
    """Promote challenger vs baseline when quote_ready→handoff improves (modeled)."""
    cycles = []
    current = "A"
    s = seed
    for c in range(max_cycles):
        challenger = "B" if c == 0 else "C"
        reset_funnel_store()
        base_arm = run_conversion_v3_monte_carlo(
            n_sessions, s, v3_product=v3_product, variant=current
        )
        s += 97
        reset_funnel_store()
        ch_arm = run_conversion_v3_monte_carlo(
            n_sessions, s, v3_product=v3_product, variant=challenger
        )
        s += 97
        promoted = ch_arm["quote_ready_to_handoff_rate"] > base_arm["quote_ready_to_handoff_rate"]
        cycles.append(
            {
                "cycle": c + 1,
                "baseline_variant": current,
                "challenger_variant": challenger,
                "baseline_qr_ho": base_arm["quote_ready_to_handoff_rate"],
                "challenger_qr_ho": ch_arm["quote_ready_to_handoff_rate"],
                "promoted_challenger": promoted,
            }
        )
        if promoted:
            current = challenger
    return {"baseline_after_loop": current, "cycles": cycles}


# --- V4 Zero-Question Intake (modeled): confirmation-first + partial completeness ----------

_V4_PERSONAS = ("messy_user", "hesitant_user", "silent_user", "distrust_user")

# Shift in customer turns to reach quote_ready (B infers more aggressively in-product)
_V4_TURNS_SHIFT: dict[str, float] = {"A": 0.0, "B": -2.8, "C": -1.2}

# Modeled: user accepts confirmation block without edits
_V4_CONFIRM_OK_BASE: dict[str, float] = {"A": 0.72, "B": 0.81, "C": 0.86}

# User sends correction after confirmation (edits / clarifications)
_V4_CORRECTION_RATE: dict[str, float] = {"A": 0.24, "B": 0.15, "C": 0.17}

# Heuristic error risk from aggressive inference (0–1)
_V4_ERROR_RISK_BASE: dict[str, float] = {"A": 0.26, "B": 0.37, "C": 0.29}


def _v4_persona_adjust(persona: str) -> dict[str, float]:
    return {
        "messy_user": {"correction": 0.12, "confirm_ok": -0.08, "turns": 1.4, "error_risk": 0.08},
        "hesitant_user": {"correction": 0.06, "confirm_ok": -0.12, "turns": 1.8, "error_risk": 0.02},
        "silent_user": {"correction": -0.06, "confirm_ok": -0.18, "turns": 2.2, "error_risk": -0.04},
        "distrust_user": {"correction": 0.1, "confirm_ok": -0.14, "turns": 0.6, "error_risk": 0.06},
    }.get(persona, {})


def run_v4_intake_monte_carlo(
    n_sessions: int,
    seed: int,
    *,
    variant: str = "B",
) -> dict[str, Any]:
    """
    V4 flow simulation: median turns (target ≤5), confirmation success, correction rate,
    case completeness, error risk — separate from post-quote_ready conversion_v3 model.
    """
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    v = (variant or "A").strip().upper()
    for i in range(n_sessions):
        persona = _V4_PERSONAS[i % len(_V4_PERSONAS)]
        adj = _v4_persona_adjust(persona)
        peak = 7 + _V4_TURNS_SHIFT.get(v, 0.0) + adj.get("turns", 0.0)
        qr_turn = max(2, int(rng.triangular(2, 12, peak)))
        confirm_ok = max(
            0.05,
            min(
                0.97,
                _V4_CONFIRM_OK_BASE.get(v, 0.75)
                + adj.get("confirm_ok", 0.0)
                + rng.uniform(-0.06, 0.06),
            ),
        )
        correction = max(
            0.0,
            min(
                0.95,
                _V4_CORRECTION_RATE.get(v, 0.2) + adj.get("correction", 0.0) + rng.uniform(-0.04, 0.04),
            ),
        )
        err_risk = max(
            0.05,
            min(
                0.95,
                _V4_ERROR_RISK_BASE.get(v, 0.3) + adj.get("error_risk", 0.0) + rng.uniform(-0.05, 0.05),
            ),
        )
        completeness = max(
            0.42,
            min(0.98, 0.55 + 0.04 * qr_turn + rng.uniform(-0.08, 0.08) + (0.06 if v == "C" else 0.03)),
        )
        # Total turns: intake to handoff (confirmation + optional correction + contact)
        extra = 1
        if rng.random() > confirm_ok:
            extra += 1
        if rng.random() < correction:
            extra += 1
        total_turns = qr_turn + extra
        effort = total_turns
        rows.append(
            {
                "persona": persona,
                "variant": v,
                "qr_turn": qr_turn,
                "total_turns_to_handoff": total_turns,
                "confirmation_success_rate_draw": round(confirm_ok, 4),
                "correction_rate_draw": round(correction, 4),
                "case_completeness_score": round(completeness, 4),
                "error_risk_score": round(err_risk, 4),
                "user_effort_score": effort,
            }
        )

    med_turns = sorted(r["total_turns_to_handoff"] for r in rows)[len(rows) // 2]
    med_effort = sorted(r["user_effort_score"] for r in rows)[len(rows) // 2]
    mean_complete = round(sum(r["case_completeness_score"] for r in rows) / max(len(rows), 1), 4)
    mean_err = round(sum(r["error_risk_score"] for r in rows) / max(len(rows), 1), 4)
    mean_confirm = round(sum(r["confirmation_success_rate_draw"] for r in rows) / max(len(rows), 1), 4)
    mean_corr = round(sum(r["correction_rate_draw"] for r in rows) / max(len(rows), 1), 4)
    auto_gen_rate = round(sum(1 for r in rows if r["case_completeness_score"] >= 0.70) / max(len(rows), 1), 4)

    by_p: dict[str, dict[str, float]] = {}
    for p in _V4_PERSONAS:
        sub = [r for r in rows if r["persona"] == p]
        by_p[p] = {
            "n": float(len(sub)),
            "median_turns": float(sorted(s["total_turns_to_handoff"] for s in sub)[len(sub) // 2])
            if sub
            else 0.0,
        }

    return {
        "n_sessions": n_sessions,
        "seed": seed,
        "variant": v,
        "median_turns_total": med_turns,
        "median_user_effort": med_effort,
        "mean_case_completeness_score": mean_complete,
        "mean_error_risk_score": mean_err,
        "mean_confirmation_success_rate": mean_confirm,
        "mean_correction_rate": mean_corr,
        "auto_generated_case_rate_ge_70pct_completeness": auto_gen_rate,
        "per_persona_median_turns": by_p,
        "method_note": "V4 Monte Carlo models confirmation-first + partial completeness; calibrate with production case_draft.v4_completeness_score.",
    }


def run_v4_variant_comparison_table(
    n_sessions: int,
    seed: int,
) -> dict[str, Any]:
    arms = ["A", "B", "C"]
    table = []
    for v in arms:
        arm = run_v4_intake_monte_carlo(n_sessions, seed + ord(v), variant=v)
        table.append(
            {
                "variant": v,
                "median_turns_total": arm["median_turns_total"],
                "mean_confirmation_success_rate": arm["mean_confirmation_success_rate"],
                "mean_correction_rate": arm["mean_correction_rate"],
                "mean_case_completeness_score": arm["mean_case_completeness_score"],
                "mean_error_risk_score": arm["mean_error_risk_score"],
                "auto_generated_case_rate_ge_70pct_completeness": arm["auto_generated_case_rate_ge_70pct_completeness"],
                "quote_ready_to_handoff_rate": run_conversion_v3_monte_carlo(
                    n_sessions, seed + 11 + ord(v), v3_product=True, variant=v
                )["quote_ready_to_handoff_rate"],
            }
        )
    return {"sessions_per_arm": n_sessions, "label": "V4_VARIANT_COMPARISON_TABLE", "rows": table}


def run_auto_evolution_loop_v4(
    n_sessions: int,
    seed: int,
    *,
    v3_product: bool,
    max_cycles: int = 2,
    error_risk_cap: float = 0.42,
) -> dict[str, Any]:
    """
    Promote B only if conversion improves AND modeled error risk stays below cap (V4 policy).
    """
    cycles = []
    current = "A"
    s = seed
    for c in range(max_cycles):
        challenger = "B" if c == 0 else "C"
        reset_funnel_store()
        base_arm = run_conversion_v3_monte_carlo(
            n_sessions, s, v3_product=v3_product, variant=current
        )
        base_v4 = run_v4_intake_monte_carlo(n_sessions, s + 3, variant=current)
        s += 97
        reset_funnel_store()
        ch_arm = run_conversion_v3_monte_carlo(
            n_sessions, s, v3_product=v3_product, variant=challenger
        )
        ch_v4 = run_v4_intake_monte_carlo(n_sessions, s + 3, variant=challenger)
        s += 97
        better_conv = ch_arm["quote_ready_to_handoff_rate"] > base_arm["quote_ready_to_handoff_rate"]
        risk_ok = float(ch_v4.get("mean_error_risk_score") or 0.0) <= error_risk_cap
        promoted = better_conv and risk_ok
        cycles.append(
            {
                "cycle": c + 1,
                "baseline_variant": current,
                "challenger_variant": challenger,
                "baseline_qr_ho": base_arm["quote_ready_to_handoff_rate"],
                "challenger_qr_ho": ch_arm["quote_ready_to_handoff_rate"],
                "baseline_error_risk": base_v4["mean_error_risk_score"],
                "challenger_error_risk": ch_v4["mean_error_risk_score"],
                "promoted_challenger": promoted,
                "error_risk_cap": error_risk_cap,
            }
        )
        if promoted:
            current = challenger
    return {"baseline_after_loop": current, "cycles": cycles, "label": "V4_AUTO_EVOLUTION_LOOP"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mc-sessions", type=int, default=320, help="Monte Carlo sessions (100–500 typical)")
    parser.add_argument("--mc-seed", type=int, default=42)
    args = parser.parse_args()

    results = []

    def happy_path():
        emit_funnel_event("session_started", session_id="sim-h", metadata={"persona": "happy_user"})
        emit_funnel_event(
            "first_meaningful_input",
            session_id="sim-h",
            metadata={"customer_turn_index": 1, "case_snapshot": _snap(customer_turn_index=1)},
        )
        emit_funnel_event(
            "case_created",
            session_id="sim-h",
            case_id="ch",
            metadata={"customer_turn_index": 3, "case_snapshot": _snap(customer_turn_index=3)},
        )
        emit_funnel_event(
            "quote_ready_reached",
            session_id="sim-h",
            case_id="ch",
            metadata={
                "customer_turn_index": 6,
                "case_snapshot": _snap(
                    quote_ready_status="quote_ready",
                    still_needed_fields=[],
                    collected_fields=["vin", "zip", "driver", "delivery"],
                    next_best_question="",
                    client_reply_draft="已齐，转办公室。",
                    handoff_ready=True,
                    customer_turn_index=6,
                ),
            },
        )
        emit_funnel_event(
            "handoff_started",
            session_id="sim-h",
            case_id="ch",
            metadata={
                "customer_turn_index": 6,
                "case_snapshot": _snap(quote_ready_status="quote_ready", still_needed_fields=[], handoff_ready=True, customer_turn_index=6),
            },
        )
        emit_funnel_event(
            "handoff_confirmed",
            session_id="sim-h",
            case_id="ch",
            metadata={
                "customer_turn_index": 7,
                "case_snapshot": _snap(
                    quote_ready_status="quote_ready",
                    still_needed_fields=[],
                    conversion_stage="handoff_confirmed",
                    handoff_ready=True,
                    customer_turn_index=7,
                ),
            },
        )

    def slow_user():
        emit_funnel_event("session_started", session_id="sim-s", metadata={"persona": "silent_user"})
        emit_funnel_event(
            "first_meaningful_input",
            session_id="sim-s",
            metadata={"customer_turn_index": 2, "case_snapshot": _snap(customer_turn_index=2)},
        )
        emit_funnel_event(
            "quote_ready_reached",
            session_id="sim-s",
            case_id="cs",
            metadata={
                "customer_turn_index": 16,
                "case_snapshot": _snap(
                    quote_ready_status="quote_ready",
                    still_needed_fields=[],
                    collected_fields=["vin", "zip", "driver", "delivery"],
                    next_best_question="",
                    handoff_ready=True,
                    customer_turn_index=16,
                ),
            },
        )

    def messy_user():
        from services.fiqa_api.analytics.funnel_events import append_session_analytics_event

        emit_funnel_event("session_started", session_id="sim-m", metadata={"persona": "messy_user"})
        append_session_analytics_event("append_blocked", session_id="sim-m", metadata={})
        append_session_analytics_event("append_blocked", session_id="sim-m", metadata={})
        emit_funnel_event(
            "first_meaningful_input",
            session_id="sim-m",
            metadata={"customer_turn_index": 3, "case_snapshot": _snap(customer_turn_index=3, reroute_occurred=True)},
        )

    def hesitant_user_c_plus():
        emit_funnel_event("session_started", session_id="sim-c", metadata={"persona": "hesitant_user"})
        emit_funnel_event(
            "first_meaningful_input",
            session_id="sim-c",
            metadata={"customer_turn_index": 1, "case_snapshot": _snap(customer_turn_index=1)},
        )
        emit_funnel_event(
            "quote_ready_reached",
            session_id="sim-c",
            case_id="cc",
            metadata={
                "customer_turn_index": 9,
                "case_snapshot": _snap(
                    quote_ready_status="quote_ready",
                    still_needed_fields=["phone", "name"],
                    handoff_ready=True,
                    customer_turn_index=9,
                ),
            },
        )
        emit_funnel_event(
            "first_meaningful_input",
            session_id="sim-c",
            metadata={
                "customer_turn_index": 10,
                "case_snapshot": _snap(
                    quote_ready_status="quote_ready",
                    still_needed_fields=["phone"],
                    handoff_ready=True,
                    customer_turn_index=10,
                ),
            },
        )

    def silent_user():
        emit_funnel_event("session_started", session_id="sim-z", metadata={"persona": "silent_user"})
        emit_funnel_event(
            "first_meaningful_input",
            session_id="sim-z",
            metadata={"customer_turn_index": 1, "case_snapshot": _snap(customer_turn_index=1)},
        )
        emit_funnel_event(
            "quote_ready_reached",
            session_id="sim-z",
            case_id="cz",
            metadata={
                "customer_turn_index": 5,
                "case_snapshot": _snap(
                    quote_ready_status="quote_ready",
                    still_needed_fields=["phone"],
                    handoff_ready=True,
                    customer_turn_index=5,
                ),
            },
        )

    def distrust_user():
        emit_funnel_event("session_started", session_id="sim-d", metadata={"persona": "distrust_user"})
        emit_funnel_event(
            "first_meaningful_input",
            session_id="sim-d",
            metadata={"customer_turn_index": 1, "case_snapshot": _snap(customer_turn_index=1)},
        )
        emit_funnel_event(
            "quote_ready_reached",
            session_id="sim-d",
            case_id="cd",
            metadata={
                "customer_turn_index": 6,
                "case_snapshot": _snap(
                    quote_ready_status="quote_ready",
                    still_needed_fields=["phone"],
                    handoff_ready=True,
                    customer_turn_index=6,
                ),
            },
        )

    def quote_ready_no_response():
        emit_funnel_event("session_started", session_id="sim-q", metadata={})
        emit_funnel_event(
            "first_meaningful_input",
            session_id="sim-q",
            metadata={"customer_turn_index": 1, "case_snapshot": _snap(customer_turn_index=1)},
        )
        emit_funnel_event(
            "quote_ready_reached",
            session_id="sim-q",
            case_id="cq",
            metadata={
                "customer_turn_index": 4,
                "case_snapshot": _snap(
                    quote_ready_status="quote_ready",
                    still_needed_fields=[],
                    handoff_ready=True,
                    customer_turn_index=4,
                ),
            },
        )

    results.append(_run_scenario("happy_user", happy_path))
    results.append(_run_scenario("slow_user", slow_user))
    results.append(_run_scenario("messy_user", messy_user))
    results.append(_run_scenario("hesitant_user_c_plus", hesitant_user_c_plus))
    results.append(_run_scenario("silent_user", silent_user))
    results.append(_run_scenario("distrust_user", distrust_user))
    results.append(_run_scenario("quote_ready_no_response", quote_ready_no_response))

    print("ANALYTICS_SIMULATION_RESULTS")
    print(json.dumps({"scenarios": results, "score_spread": [r["score"]["total_score"] for r in results]}, indent=2))
    print("/ANALYTICS_SIMULATION_RESULTS")

    reset_funnel_store()
    emit_funnel_event("session_started", session_id="opt-a", metadata={})
    emit_funnel_event(
        "first_meaningful_input",
        session_id="opt-a",
        metadata={"customer_turn_index": 1, "case_snapshot": _snap()},
    )
    emit_funnel_event(
        "quote_ready_reached",
        session_id="opt-a",
        case_id="ca",
        metadata={"customer_turn_index": 4, "case_snapshot": _snap(quote_ready_status="quote_ready", handoff_ready=True)},
    )
    emit_funnel_event(
        "handoff_started",
        session_id="opt-a",
        case_id="ca",
        metadata={"customer_turn_index": 4, "case_snapshot": _snap(quote_ready_status="quote_ready", handoff_ready=True)},
    )
    ev_complete = iter_funnel_events()
    funnel_complete = compute_funnel(ev_complete)
    score_complete = compute_north_star_score(
        [e for e in ev_complete if e.get("session_id") == "opt-a"],
        _snap(quote_ready_status="quote_ready", handoff_ready=True),
    )

    reset_funnel_store()
    emit_funnel_event("session_started", session_id="opt-b", metadata={})
    emit_funnel_event(
        "first_meaningful_input",
        session_id="opt-b",
        metadata={"customer_turn_index": 1, "case_snapshot": _snap()},
    )
    emit_funnel_event(
        "quote_ready_reached",
        session_id="opt-b",
        case_id="cb",
        metadata={"customer_turn_index": 4, "case_snapshot": _snap(quote_ready_status="quote_ready", handoff_ready=False)},
    )
    ev_stall = iter_funnel_events()
    funnel_stall = compute_funnel(ev_stall)
    score_stall = compute_north_star_score(
        [e for e in ev_stall if e.get("session_id") == "opt-b"],
        _snap(quote_ready_status="quote_ready", handoff_ready=False),
    )

    opt_payload = {
        "messy_input_signals": {
            "short_ok_meaningful": is_meaningful_customer_text("ok"),
            "short_zh_ok_meaningful": is_meaningful_customer_text("好"),
        },
        "quote_ready_to_handoff_conversion_rate": {
            "with_handoff_session": funnel_complete["conversion_rates"].get("quote_ready_to_handoff"),
            "stall_session_no_handoff_event": funnel_stall["conversion_rates"].get("quote_ready_to_handoff"),
        },
        "north_star_total": {
            "with_handoff": score_complete["total_score"],
            "quote_ready_stall": score_stall["total_score"],
        },
        "weakest_dimension_on_stall": score_stall["dimensions"].get("efficiency"),
        "note": "efficiency caps when quote_ready_reached without handoff_started (conversion stall).",
    }
    print("OPTIMIZATION_SIMULATION_RESULTS")
    print(json.dumps(opt_payload, indent=2, ensure_ascii=False))
    print("/OPTIMIZATION_SIMULATION_RESULTS")

    ab_payload = simulate_conversion_ab_batch()
    conv_delta: dict[str, Any] = {}
    for z, lst in (ab_payload.get("ab_test_results") or {}).get("per_zone_rankings", {}).items():
        if not lst:
            continue
        best = lst[0].get("conversion_rate", 0.0)
        worst = lst[-1].get("conversion_rate", 0.0) if len(lst) > 1 else 0.0
        conv_delta[z] = {
            "best_conversion_rate": best,
            "spread_vs_worst": round(max(0.0, best - worst), 4),
        }
    ab_payload["conversion_improvement_vs_worst_in_sim"] = conv_delta
    print("CONVERSION_AB_TEST_REPORT")
    print(json.dumps(ab_payload, indent=2, ensure_ascii=False))
    print("/CONVERSION_AB_TEST_REPORT")

    # --- Part 6–9: large-sample V3 vs pre-V3 funnel (probabilistic personas)
    n_mc = max(100, min(500, args.mc_sessions))
    reset_funnel_store()
    pre_v3 = run_conversion_v3_monte_carlo(n_mc, args.mc_seed, v3_product=False, variant="A")
    reset_funnel_store()
    post_v3 = run_conversion_v3_monte_carlo(n_mc, args.mc_seed + 7, v3_product=True, variant="A")

    variant_table = run_variant_comparison_table(n_mc, args.mc_seed + 13, v3_product=True)
    print("VARIANT_COMPARISON_TABLE")
    print(json.dumps(variant_table, indent=2, ensure_ascii=False))
    print("/VARIANT_COMPARISON_TABLE")

    evolution = run_auto_evolution_loop(n_mc, args.mc_seed + 19, v3_product=True, max_cycles=2)
    print("AUTO_EVOLUTION_LOOP")
    print(json.dumps(evolution, indent=2, ensure_ascii=False))
    print("/AUTO_EVOLUTION_LOOP")

    v4_table = run_v4_variant_comparison_table(n_mc, args.mc_seed + 31)
    print("V4_VARIANT_COMPARISON_TABLE")
    print(json.dumps(v4_table, indent=2, ensure_ascii=False))
    print("/V4_VARIANT_COMPARISON_TABLE")

    v4_evolution = run_auto_evolution_loop_v4(n_mc, args.mc_seed + 41, v3_product=True, max_cycles=2)
    print("V4_AUTO_EVOLUTION_LOOP")
    print(json.dumps(v4_evolution, indent=2, ensure_ascii=False))
    print("/V4_AUTO_EVOLUTION_LOOP")

    v3_report = {
        "label": "CONVERSION_FLOW_V3_RESULTS",
        "sessions_each_arm": n_mc,
        "conversion_rate_quote_ready_to_handoff": {
            "before_v3_model": pre_v3["quote_ready_to_handoff_rate"],
            "after_v3_model": post_v3["quote_ready_to_handoff_rate"],
            "delta": round(post_v3["quote_ready_to_handoff_rate"] - pre_v3["quote_ready_to_handoff_rate"], 4),
        },
        "north_star_score_mean": {
            "before_v3_model": pre_v3["north_star_score_mean"],
            "after_v3_model": post_v3["north_star_score_mean"],
            "delta": round(post_v3["north_star_score_mean"] - pre_v3["north_star_score_mean"], 4),
        },
        "approx_dropoff_after_quote_ready": {
            "before_v3_model": pre_v3["approx_dropoff_after_quote_ready"],
            "after_v3_model": post_v3["approx_dropoff_after_quote_ready"],
            "improvement": round(
                pre_v3["approx_dropoff_after_quote_ready"] - post_v3["approx_dropoff_after_quote_ready"],
                4,
            ),
        },
        "median_turns_to_handoff_among_converters": {
            "before": pre_v3["median_turns_to_handoff_among_converters"],
            "after": post_v3["median_turns_to_handoff_among_converters"],
        },
        "per_persona_handoff_rate_after_v3": post_v3["per_persona"],
        "method_note": "before/after arms differ only in post-quote_ready continuation probabilities (V3 models clearer copy + higher resume-after-hesitation conversion). Not live traffic.",
    }
    print("CONVERSION_FLOW_V3_RESULTS")
    print(json.dumps(v3_report, indent=2, ensure_ascii=False))
    print("/CONVERSION_FLOW_V3_RESULTS")

    diag = {
        "label": "FINAL_CONVERSION_DIAGNOSIS",
        "what_still_blocks_users": [
            "Residual distrust and phone-number refusal (distrust_user arm).",
            "Messy / rerouted threads that burn turns before quote_ready.",
            "Silent users who never reply after the quote-ready impression.",
        ],
        "where_users_hesitate": [
            "Immediately after quote-ready impression (timing + privacy).",
            "Secondary beats: after a clarification question in distrust/messy personas.",
        ],
        "approx_drop_share_after_quote_ready_post_v3": post_v3["approx_dropoff_after_quote_ready"],
        "trust_sufficient": "Improved for most personas via explicit no-spam and minutes-level timing; not sufficient for highest-skeptic segment without human proof or channel preference.",
    }
    print("FINAL_CONVERSION_DIAGNOSIS")
    print(json.dumps(diag, indent=2, ensure_ascii=False))
    print("/FINAL_CONVERSION_DIAGNOSIS")

    eval_block = {
        "label": "FINAL_CONVERSION_EVALUATION",
        "is_high_conversion_flow": "Stronger than pre-V3 on modeled quote_ready→handoff and north-star means, but still gated by real-world channel trust and operator latency.",
        "still_missing": [
            "Live A/B on production copy; latency SLA surfaced to the user.",
            "UI-level single-button mode when only contact is missing (optional).",
        ],
        "next_biggest_opportunity": "Measure real funnel with handoff_started at quote_ready + contact completion ack; tune distrust path with optional alternate channel (e.g. callback window).",
    }
    print("FINAL_CONVERSION_EVALUATION")
    print(json.dumps(eval_block, indent=2, ensure_ascii=False))
    print("/FINAL_CONVERSION_EVALUATION")

    final_report = {
        "label": "FINAL_SYSTEM_EVOLUTION_REPORT",
        "phase1_reference": "See chat SYSTEM_DIAGNOSIS (inspection of triage, conversion_layer, routes, UI, ui_copy).",
        "code_shipped": [
            "case_draft + intake_evolution_variant on triage result",
            "Add-car minimal questioning from turn 1; variant B shorter asks; variant C confirmation vehicle ask",
            "UI: completion_message alert + contact-only gap single-path CTA",
            "Simulation: VARIANT_COMPARISON_TABLE + AUTO_EVOLUTION_LOOP + extended metrics",
            "V4: build_v4_case_draft_bundle, confirmation-first B/C, partial handoff ≥70% from turn 2, V4 Monte Carlo tables",
        ],
        "modeled_conversion_note": "Monte Carlo arms are illustrative; calibrate against production funnel events.",
        "variant_table_summary": variant_table.get("rows"),
        "v4_variant_comparison_table": v4_table.get("rows"),
        "v4_auto_evolution_winner": v4_evolution.get("baseline_after_loop"),
        "evolution_winner": evolution.get("baseline_after_loop"),
        "next_roi": [
            "Wire production A/B on intake_evolution_variant with real quote_ready→handoff",
            "Teach case_draft inferred_fields from LLM slot layer with explicit confidence",
        ],
    }
    print("FINAL_SYSTEM_EVOLUTION_REPORT")
    print(json.dumps(final_report, indent=2, ensure_ascii=False))
    print("/FINAL_SYSTEM_EVOLUTION_REPORT")


if __name__ == "__main__":
    main()
