"""
Conversion copy A/B test zones, variants, assignment, and lightweight simulation metrics.

Production wiring: attach impression / outcome events at quote_ready, defer_ack, and silence paths
(see inbox_triage/conversion_layer.py). This module centralizes definitions and offline simulation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from services.fiqa_api.analytics.funnel_events import (
    append_session_analytics_event,
    emit_funnel_event,
    iter_funnel_events,
    reset_funnel_store,
)
from services.fiqa_api.analytics.funnel_metrics import compute_funnel
from services.fiqa_api.analytics.north_star_score import compute_north_star_score

# --- PART 1: TEST ZONES -------------------------------------------------------

TEST_ZONES: tuple[dict[str, str], ...] = (
    {
        "zone_id": "quote_ready",
        "name": "Quote ready (primary conversion moment)",
        "intent": "First full block after quote_ready: drive name/phone + office follow-up.",
    },
    {
        "zone_id": "hesitation_defer_ack",
        "name": "Hesitation / defer_ack",
        "intent": "User defers (等一下 / later)—keep trust, restate timeline, soft contact nudge.",
    },
    {
        "zone_id": "silence_after_quote_ready",
        "name": "Silence after quote_ready",
        "intent": "No customer reply after quote_ready—passive nudge toward contact completion.",
    },
)


# --- PART 2: COPY VARIANTS (3–5 per zone, distinct strategies) ---------------

COPY_VARIANTS: dict[str, tuple[dict[str, str], ...]] = {
    "quote_ready": (
        {
            "variant_id": "qr_urgency",
            "strategy": "urgency",
            "zh": "只剩一步：在本对话留下称呼+电话，办公室同事即可开始处理并回电确认。",
            "en": "Only one step left: drop your name and phone here so our office can start and call you back.",
        },
        {
            "variant_id": "qr_speed",
            "strategy": "speed",
            "zh": "补上电话大约30秒；同事会按1–2个工作日节奏把报价推进并联系你核对。",
            "en": "Adding your phone takes ~30 seconds—we usually move the quote in 1–2 business days and will reach out to confirm.",
        },
        {
            "variant_id": "qr_safety",
            "strategy": "safety",
            "zh": "信息只用于本次报价与必要联系，不会群发营销；留个电话方便报价送到你手上。",
            "en": "We only use what you share for this quote and follow-up—no promo spam. A phone number is enough for us to deliver the quote.",
        },
        {
            "variant_id": "qr_authority",
            "strategy": "authority",
            "zh": "由持牌顾问同事跟进，先核对细节再出正式报价；请留称呼与联系电话。",
            "en": "A licensed advisor will review details before the formal quote—please share your name and phone.",
        },
        {
            "variant_id": "qr_convenience",
            "strategy": "convenience",
            "zh": "直接把手机号发在本对话里即可，办公室同事会单向联系你，省来回找。",
            "en": "Just send your mobile in this thread—the office can reach you directly without the back-and-forth.",
        },
    ),
    "hesitation_defer_ack": (
        {
            "variant_id": "def_urgency",
            "strategy": "urgency",
            "zh": "好的—报价在推进。你方便时回一句电话即可，同事好把进度接上。",
            "en": "No problem—the quote is moving. When you can, drop your number here so we can connect the next step.",
        },
        {
            "variant_id": "def_speed",
            "strategy": "speed",
            "zh": "回复一句电话大概30秒；我们不催你，但有了号码推进会更快。",
            "en": "A one-line phone reply takes ~30 seconds—we won't rush you, but it speeds the next update.",
        },
        {
            "variant_id": "def_safety",
            "strategy": "safety",
            "zh": "我们不骚扰推销；你忙完后留电话，只为把报价结果送到你。",
            "en": "We won't pressure you—when you're free, leave a phone so we can deliver the quote result.",
        },
        {
            "variant_id": "def_authority",
            "strategy": "authority",
            "zh": "办公室按标准流程联系你，核对清楚再继续；留个联系方式即可。",
            "en": "Our office follows the standard verification flow—leave contact info and we'll align before the next step.",
        },
        {
            "variant_id": "def_convenience",
            "strategy": "convenience",
            "zh": "忙完把手机号发在本对话就行，我们按你的节奏来电。",
            "en": "When you're ready, send your mobile here—we'll call on your timeline.",
        },
    ),
    "silence_after_quote_ready": (
        {
            "variant_id": "sil_urgency",
            "strategy": "urgency",
            "zh": "还在吗？只差一个联系电话，同事才能把报价继续推进。",
            "en": "Still there? We only need a phone number to keep your quote moving.",
        },
        {
            "variant_id": "sil_speed",
            "strategy": "speed",
            "zh": "补上电话约30秒，报价流程不会卡在这里。",
            "en": "Takes ~30 seconds to add a phone so the quote doesn't stall.",
        },
        {
            "variant_id": "sil_safety",
            "strategy": "safety",
            "zh": "不会频繁打扰；只为把报价交付，留个电话即可。",
            "en": "We won't spam you—just need a number to deliver the quote.",
        },
        {
            "variant_id": "sil_authority",
            "strategy": "authority",
            "zh": "持牌团队来电只为核对报价信息，请先留联系电话。",
            "en": "Licensed staff may call only to verify quote details—please share a phone.",
        },
        {
            "variant_id": "sil_convenience",
            "strategy": "convenience",
            "zh": "直接回一条手机号，我们单向联系，你不用再找入口。",
            "en": "Reply with your mobile—we'll reach you so you don't have to hunt for us.",
        },
    ),
}


# --- PART 3: VARIANT ASSIGNMENT -----------------------------------------------

def assign_variant(session_id: str, zone_id: str, *, variants: tuple[dict[str, str], ...] | None = None) -> dict[str, str]:
    """Stable per-session assignment using session_hash (same client always sees same variant in a zone)."""
    rows = variants or COPY_VARIANTS.get(zone_id) or COPY_VARIANTS["quote_ready"]
    if not rows:
        raise ValueError(f"no variants for zone {zone_id}")
    raw = f"{session_id}|{zone_id}|conversion_copy_ab:v1".encode()
    h = int(hashlib.sha256(raw).hexdigest(), 16)
    return dict(rows[h % len(rows)])


def assignment_logic_description() -> dict[str, Any]:
    return {
        "mode": "session_hash_stable",
        "hash": "sha256(session_id + '|' + zone_id + '|conversion_copy_ab:v1') % len(variants)",
        "alternative": "random_uniform (not implemented here—use for quick lab tests only)",
        "properties": ["stable across turns", "uniform across variants", "no external state"],
    }


# --- PART 4: METRIC SCHEMA -----------------------------------------------------

METRIC_SCHEMA: dict[str, Any] = {
    "entities": {
        "session": {"session_id": "string"},
        "variant": {"zone_id": "string", "variant_id": "string", "strategy": "string"},
    },
    "events": {
        "conversion_ab_impression": {
            "when": "Assistant displays copy for a test zone",
            "fields": ["session_id", "case_id?", "zone_id", "variant_id", "strategy", "language"],
            "dedupe": "once per (session_id, zone_id, variant_id) per assistant turn (client should de-dupe)",
        },
        "conversion_ab_handoff_attributed": {
            "when": "handoff_started within attribution window after quote_ready impression",
            "fields": ["session_id", "case_id", "zone_id", "variant_id", "seconds_since_quote_ready"],
        },
        "conversion_ab_drop_after_message": {
            "when": "Session had quote_ready impression but no handoff within window",
            "fields": ["session_id", "case_id", "last_zone_nudged", "seconds_since_last_bot_message"],
        },
    },
    "aggregates_per_variant": {
        "impressions": "count(impression events)",
        "handoff_started": "count(attributed handoff)",
        "conversion_rate": "handoff_started / max(impressions, 1)",
        "median_time_to_conversion_sec": "median(seconds_since_quote_ready for conversions)",
        "drop_off_after_message_rate": "drops / impressions at silence zone",
    },
}


def _snap(**kwargs: object) -> dict[str, Any]:
    base: dict[str, Any] = {
        "quote_ready_status": kwargs.get("quote_ready_status", "need_more"),
        "still_needed_fields": kwargs.get("still_needed_fields", ["phone", "name"]),
        "collected_fields": kwargs.get("collected_fields", ["vin", "zip", "driver", "delivery"]),
        "next_best_question": kwargs.get("next_best_question", ""),
        "client_reply_draft": kwargs.get("client_reply_draft", ""),
        "handoff_ready": kwargs.get("handoff_ready", True),
        "triage_mode": "greenfield",
        "append_allowed": True,
        "conversion_stage": kwargs.get("conversion_stage", ""),
        "issue_category": "customer_question",
        "reroute_occurred": kwargs.get("reroute_occurred", False),
        "customer_turn_index": kwargs.get("customer_turn_index", 1),
        "customer_text_len": 20,
    }
    return base


# --- Simulation: persona -> events + outcomes (deterministic, messy reality) ---

def _strategy_weight(strategy: str, persona: str) -> float:
    """Tiny heuristic boosts/penalties; keeps simulation non-creative and reproducible."""
    base = {
        "happy_user": 1.0,
        "messy_user": 0.55,
        "hesitant_user": 0.58,
        "silent_user": 0.20,
    }.get(persona, 0.5)
    adj = {
        "urgency": -0.04 if persona in ("hesitant_user", "silent_user") else 0.06,
        "speed": 0.05 if persona == "silent_user" else 0.03,
        "safety": 0.08 if persona in ("hesitant_user", "messy_user") else 0.02,
        "authority": 0.07 if persona == "messy_user" else 0.04,
        "convenience": 0.10 if persona in ("silent_user", "hesitant_user") else 0.03,
    }.get(strategy, 0.0)
    p = min(0.99, max(0.02, base + adj))
    # deterministic "dice" from persona + strategy
    h = int(hashlib.sha256(f"{persona}|{strategy}|ab-sim".encode()).hexdigest(), 16)
    dice = (h % 10_000) / 10_000.0
    converts = dice < p
    return 1.0 if converts else 0.0


def simulate_conversion_ab_batch() -> dict[str, Any]:
    """
    Emit funnel + AB analytics rows for four personas; compute per-variant stats and winners.
    """
    reset_funnel_store()
    personas: dict[str, dict[str, Any]] = {
        "happy_user": {"turn_qr": 5, "messy": False, "reply": "好，电话是4155550100", "seconds_to_handoff": 42},
        "messy_user": {"turn_qr": 14, "messy": True, "reply": "等等我发…算了先给你 zip", "seconds_to_handoff": 520},
        "hesitant_user": {"turn_qr": 8, "messy": False, "reply": "晚点再说…哦对了电话给你", "seconds_to_handoff": 380},
        "silent_user": {"turn_qr": 6, "messy": False, "reply": "", "seconds_to_handoff": 0},
    }

    zone_ids = ("quote_ready", "hesitation_defer_ack", "silence_after_quote_ready")
    rows: list[dict[str, Any]] = []
    per_variant: dict[str, dict[str, Any]] = {}

    def bump_v(vid: str, zone: str, field: str, inc: float = 1.0) -> None:
        per_variant.setdefault(vid, {"zone_id": zone, "impressions": 0, "handoff_started": 0.0, "drops": 0.0})
        per_variant[vid][field] = per_variant[vid].get(field, 0) + inc

    for persona_name, cfg in personas.items():
        sid = f"sim-ab-{persona_name}"
        cid = f"c-{persona_name}"
        v_map: dict[str, str] = {}
        for z in zone_ids:
            v = assign_variant(sid, z)
            v_map[z] = v["variant_id"]
            bump_v(v["variant_id"], z, "impressions")
            append_session_analytics_event(
                "conversion_ab_impression",
                session_id=sid,
                case_id=cid,
                metadata={
                    "zone_id": z,
                    "variant_id": v["variant_id"],
                    "strategy": v["strategy"],
                    "language": "zh",
                    "persona": persona_name,
                },
            )
            rows.append({"session_id": sid, "zone_id": z, "variant": v["variant_id"], "event": "impression"})

        # Build funnel
        emit_funnel_event("session_started", session_id=sid, metadata={"persona": persona_name})
        emit_funnel_event(
            "first_meaningful_input",
            session_id=sid,
            metadata={"customer_turn_index": 1, "case_snapshot": _snap(customer_turn_index=1)},
        )
        if cfg["messy"]:
            append_session_analytics_event("append_blocked", session_id=sid, metadata={"persona": persona_name})
            append_session_analytics_event("append_blocked", session_id=sid, metadata={"persona": persona_name})
        emit_funnel_event(
            "case_created",
            session_id=sid,
            case_id=cid,
            metadata={"customer_turn_index": 3, "case_snapshot": _snap(customer_turn_index=3, reroute_occurred=cfg["messy"])},
        )
        qr_meta = {
            "customer_turn_index": cfg["turn_qr"],
            "case_snapshot": _snap(
                quote_ready_status="quote_ready",
                still_needed_fields=[],
                handoff_ready=True,
                customer_turn_index=cfg["turn_qr"],
            ),
            "conversion_ab_variants": v_map,
        }
        emit_funnel_event("quote_ready_reached", session_id=sid, case_id=cid, metadata=qr_meta)

        # Outcome: strategy weight from quote_ready variant drives handoff probability
        qr_v = assign_variant(sid, "quote_ready")
        strat = qr_v["strategy"]
        if _strategy_weight(strat, persona_name) >= 1.0 or persona_name == "happy_user":
            hs_meta = {
                "customer_turn_index": cfg["turn_qr"] + 1,
                "case_snapshot": _snap(
                    quote_ready_status="quote_ready",
                    still_needed_fields=[],
                    conversion_stage="handoff_ready",
                    customer_turn_index=cfg["turn_qr"] + 1,
                ),
                "conversion_ab_quote_variant_id": qr_v["variant_id"],
                "seconds_since_quote_ready": cfg["seconds_to_handoff"] or 120,
            }
            emit_funnel_event("handoff_started", session_id=sid, case_id=cid, metadata=hs_meta)
            for z in zone_ids:
                bump_v(v_map[z], z, "handoff_started")
            append_session_analytics_event(
                "conversion_ab_handoff_attributed",
                session_id=sid,
                case_id=cid,
                metadata={
                    "zone_id": "quote_ready",
                    "variant_id": qr_v["variant_id"],
                    "seconds_since_quote_ready": cfg["seconds_to_handoff"] or 120,
                    "persona": persona_name,
                },
            )
            rows.append({"session_id": sid, "variant": qr_v["variant_id"], "event": "handoff", "persona": persona_name})
            emit_funnel_event(
                "handoff_confirmed",
                session_id=sid,
                case_id=cid,
                metadata={
                    "customer_turn_index": cfg["turn_qr"] + 2,
                    "case_snapshot": _snap(quote_ready_status="quote_ready", conversion_stage="handoff_confirmed", customer_turn_index=cfg["turn_qr"] + 2),
                },
            )
        else:
            append_session_analytics_event(
                "conversion_ab_drop_after_message",
                session_id=sid,
                case_id=cid,
                metadata={
                    "zone_id": "silence_after_quote_ready",
                    "variant_id": v_map["silence_after_quote_ready"],
                    "seconds_since_last_bot_message": 900,
                    "persona": persona_name,
                },
            )
            rows.append({"session_id": sid, "event": "drop", "persona": persona_name})
            bump_v(v_map["silence_after_quote_ready"], "silence_after_quote_ready", "drops")

    events = iter_funnel_events()
    funnel = compute_funnel(events)

    # Per-variant conversion (quote_ready zone only; primary KPI)
    variant_stats: list[dict[str, Any]] = []
    for vid, stats in sorted(per_variant.items()):
        imp = int(stats.get("impressions", 0))
        ho = float(stats.get("handoff_started", 0))
        if stats.get("zone_id") != "quote_ready":
            continue
        variant_stats.append(
            {
                "variant_id": vid,
                "zone_id": "quote_ready",
                "impressions": imp,
                "handoff_started": int(ho),
                "conversion_rate": round(ho / imp, 4) if imp else 0.0,
            }
        )

    variant_stats.sort(key=lambda x: x["conversion_rate"], reverse=True)
    winners: dict[str, Any] = {}
    by_zone: dict[str, list[dict[str, Any]]] = {}
    for z in zone_ids:
        by_zone[z] = []
    for vid, stats in per_variant.items():
        z = stats["zone_id"]
        imp = int(stats.get("impressions", 0))
        ho = float(stats.get("handoff_started", 0))
        by_zone[z].append(
            {
                "variant_id": vid,
                "impressions": imp,
                "handoff_started": int(ho),
                "drops_after_message": int(stats.get("drops", 0)),
                "conversion_rate": round(ho / imp, 4) if imp else 0.0,
            }
        )
    for z, lst in by_zone.items():
        lst.sort(key=lambda x: x["conversion_rate"], reverse=True)
        if lst:
            winners[z] = lst[0]["variant_id"]

    # Worst per zone -> next iteration plan
    next_plan: list[dict[str, str]] = []
    for z, lst in by_zone.items():
        if not lst:
            continue
        worst = min(lst, key=lambda x: (x["conversion_rate"], x["variant_id"]))
        next_plan.append(
            {
                "zone_id": z,
                "retire_variant_id": worst["variant_id"],
                "replace_with_strategy": "hybrid_safety_convenience",
                "next_copy_zh_hint": "把“无骚扰/单向联系”合并成一句更短的行动召唤",
            }
        )

    # Session scores
    by_session: dict[str, list[dict[str, Any]]] = {}
    for e in events:
        sid = str(e.get("session_id") or "")
        if sid.startswith("sim-ab-"):
            by_session.setdefault(sid, []).append(e)

    scores = {}
    for sid, evs in by_session.items():
        scores[sid] = compute_north_star_score(evs, None)["total_score"]

    report = {
        "test_zones": list(TEST_ZONES),
        "copy_variants": COPY_VARIANTS,
        "variant_assignment_logic": assignment_logic_description(),
        "metric_schema": METRIC_SCHEMA,
        "simulation_personas": personas,
        "simulation_event_trace": rows,
        "ab_test_results": {
            "per_zone_rankings": by_zone,
            "quote_ready_leaderboard": variant_stats,
        },
        "north_star_by_persona": scores,
        "funnel": funnel,
        "winning_variants": winners,
        "next_iteration_plan": next_plan,
        "simulation_notes": [
            "Deterministic persona outcomes; quote_ready variant strategy nudges convert probability.",
            "silent_user may drop unless convenience/speed hash favors conversion.",
        ],
    }
    return report


def format_conversion_ab_report() -> str:
    """JSON block for inclusion in simulation stdout."""
    payload = simulate_conversion_ab_batch()
    return "CONVERSION_AB_TEST_REPORT\n" + json.dumps(payload, indent=2, ensure_ascii=False) + "\n/CONVERSION_AB_TEST_REPORT"
