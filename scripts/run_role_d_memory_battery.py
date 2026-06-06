#!/usr/bin/env python3
"""
P16-Z7 Role D memory battery — paste + append simulation across multi-day journeys.

Usage:
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_role_d_memory_battery.py [--verbose]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_for_append

JOURNEYS_PATH = REPO / "configs" / "role_d_journeys.json"
CLAIMS_PATH = REPO / "configs" / "role_d_claims_battery.json"
OUT_DIR = REPO / "docs" / "product_constitution" / ".role_d_results"

GENERIC_BROKER_MARKERS = (
    "review the",
    "follow up shortly",
    "provide more details",
    "request clarification",
    "earliest convenience",
)


def _build_source_text(messages: list[str]) -> str:
    return "".join(f"[客户] {m.strip()}" for m in messages if m.strip())


def _keyword_hits(text: str, keywords: list[str]) -> int:
    t = (text or "").lower()
    return sum(1 for k in keywords if k.lower() in t)


def _score_summary_quality(result: dict) -> tuple[int, list[str]]:
    notes: list[str] = []
    summary = (result.get("conversation_summary") or "").strip()
    if len(summary) < 40:
        notes.append("summary thin")
        return 8, notes
    score = 18
    if "customer message" in summary.lower() or re.search(r"\d customer message", summary.lower()):
        score += 4
    if "prior turn" in summary.lower():
        score += 3
    return min(score, 25), notes


def _score_field_retention(journey: dict, result: dict, all_messages: list[str]) -> tuple[int, list[str]]:
    notes: list[str] = []
    collected = [str(x).lower() for x in (result.get("collected_fields") or [])]
    still = [str(x).lower() for x in (result.get("still_needed_fields") or [])]
    blob = " ".join(collected + still + [(result.get("conversation_summary") or "").lower()])
    hints = journey.get("expected_intent_hints") or []
    hits = _keyword_hits(blob, hints)
    merged = " ".join(all_messages).lower()
    merged_hits = _keyword_hits(merged, hints)
    if merged_hits == 0:
        return 15, notes
    ratio = hits / max(merged_hits, 1)
    if ratio >= 0.5:
        return 22, notes
    if ratio >= 0.25:
        notes.append(f"field retention partial: {hits}/{merged_hits} hints in structured output")
        return 14, notes
    notes.append(f"field retention weak: {hits}/{merged_hits}")
    return 8, notes


def _score_next_action(result: dict) -> tuple[int, list[str]]:
    notes: list[str] = []
    step = (result.get("broker_next_step") or "").strip()
    if not step or len(step) < 20:
        notes.append("broker_next_step empty/short")
        return 5, notes
    low = step.lower()
    if any(m in low for m in GENERIC_BROKER_MARKERS):
        notes.append("broker_next_step generic")
        return 12, notes
    draft = (result.get("client_reply_draft") or "").strip()
    if len(draft) < 30:
        notes.append("client draft thin")
        return 16, notes
    return 23, notes


def _reread_score(journey: dict, result: dict) -> tuple[int, bool]:
    """0-100: can broker understand case from triage output alone?"""
    must = journey.get("reread_must_have_any") or []
    parts = [
        result.get("conversation_summary") or "",
        result.get("broker_next_step") or "",
        result.get("client_reply_draft") or "",
        str(result.get("suggested_waiting_on") or ""),
        " ".join(str(x) for x in (result.get("collected_fields") or [])),
        " ".join(str(x) for x in (result.get("still_needed_fields") or [])),
    ]
    blob = " ".join(parts).lower()
    if not must:
        return 70, False
    hits = sum(1 for m in must if m.lower() in blob)
    ratio = hits / len(must)
    score = int(min(100, 40 + ratio * 60))
    needs_wechat = ratio < 0.45
    return score, needs_wechat


def run_journey(j: dict, verbose: bool) -> dict:
    days = j.get("days") or []
    messages: list[str] = []
    turn_results: list[dict] = []
    final = {}

    for i, day_block in enumerate(days):
        msg = (day_block.get("message") or "").strip()
        if not msg:
            continue
        if i == 0:
            result = triage_conversation(msg, [])
        else:
            existing = _build_source_text(messages)
            prior = turn_results[-1] if turn_results else {}
            ctx = {
                "persisted_collected_fields": list(prior.get("collected_fields") or []),
                "still_needed_fields": list(prior.get("still_needed_fields") or []),
                "service_record_append": True,
            }
            result = triage_for_append(existing, msg, reply_truth_context=ctx)
        messages.append(msg)
        turn_results.append(
            {
                "day": day_block.get("day"),
                "message_preview": msg[:80],
                "issue_category": result.get("issue_category"),
                "urgency": result.get("urgency"),
                "conversation_summary": result.get("conversation_summary"),
                "collected_fields": result.get("collected_fields"),
                "still_needed_fields": result.get("still_needed_fields"),
                "broker_next_step": result.get("broker_next_step"),
            }
        )
        final = result
        if verbose:
            print(f"  {j['id']} day {day_block.get('day')}: {result.get('issue_category')} — {(result.get('conversation_summary') or '')[:60]}…")

    sq, sq_notes = _score_summary_quality(final)
    fr, fr_notes = _score_field_retention(j, final, messages)
    na, na_notes = _score_next_action(final)
    reread, needs_wechat = _reread_score(j, final)

    exp_cat = (j.get("expected_category") or "").lower()
    got_cat = (final.get("issue_category") or "").lower()
    cat_ok = got_cat == exp_cat

    return {
        "id": j["id"],
        "category": j.get("category"),
        "title": j.get("title"),
        "turn_count": len(messages),
        "category_match": cat_ok,
        "expected_category": exp_cat,
        "got_category": got_cat,
        "final": {
            "conversation_summary": final.get("conversation_summary"),
            "broker_next_step": final.get("broker_next_step"),
            "collected_fields": final.get("collected_fields"),
            "still_needed_fields": final.get("still_needed_fields"),
            "client_reply_draft": (final.get("client_reply_draft") or "")[:200],
        },
        "turn_results": turn_results,
        "scores": {
            "summary_quality": sq,
            "field_retention": fr,
            "next_action_quality": na,
            "memory_total": sq + fr + na,
            "reread_0_100": reread,
            "needs_wechat": needs_wechat,
        },
        "notes": sq_notes + fr_notes + na_notes,
    }


WAITING_ON_SCENARIOS: list[tuple[str, str]] = [
    ("carrier那边有回复吗？还是说还要等？", "carrier"),
    ("Any update from underwriting or billing? Still showing lapse.", "underwriting"),
    ("UW还有别的要求吗？我下周要用车", "underwriting"),
    ("Did carrier accept the forms? Deadline is Friday.", "carrier"),
    ("adjuster有联系我吗？还是要我再打电话？", "carrier"),
    ("quote出来了吗？大概加多少钱？", "broker"),
    ("refund大概多少？什么时候生效？", "broker"),
    ("有便宜方案了吗？还是只能续保？", "broker"),
    ("carrier确认恢复了吗？还要等多久？", "carrier"),
]


def _score_waiting_on() -> tuple[int, int, list[dict]]:
    from services.fiqa_api.inbox_triage.triage import _suggest_waiting_on

    hits = 0
    rows: list[dict] = []
    for msg, expected in WAITING_ON_SCENARIOS:
        got = _suggest_waiting_on(f"[客户] {msg}", [], "")
        ok = got == expected
        if ok:
            hits += 1
        rows.append({"message": msg[:60], "expected": expected, "got": got, "ok": ok})
    return hits, len(WAITING_ON_SCENARIOS), rows


def run_claims_case(c: dict, verbose: bool) -> dict:
    turns = c.get("turns") or []
    messages: list[str] = []
    final = {}
    turn_results: list[dict] = []
    for i, msg in enumerate(turns):
        msg = (msg or "").strip()
        if not msg:
            continue
        if i == 0:
            result = triage_conversation(msg, [])
        else:
            prior = turn_results[-1] if turn_results else {}
            ctx = {
                "persisted_collected_fields": list(prior.get("collected_fields") or []),
                "still_needed_fields": list(prior.get("still_needed_fields") or []),
                "service_record_append": True,
            }
            result = triage_for_append(_build_source_text(messages), msg, reply_truth_context=ctx)
        messages.append(msg)
        turn_results.append(
            {
                "collected_fields": result.get("collected_fields"),
                "suggested_waiting_on": result.get("suggested_waiting_on"),
            }
        )
        final = result
    keywords = c.get("memory_keywords") or []
    blob = " ".join(
        [
            final.get("conversation_summary") or "",
            " ".join(str(x) for x in (final.get("collected_fields") or [])),
            final.get("broker_next_step") or "",
        ]
    ).lower()
    hits = _keyword_hits(blob, keywords)
    retention_pct = int(100 * hits / max(len(keywords), 1))
    return {
        "id": c["id"],
        "title": c.get("title"),
        "turn_count": len(messages),
        "memory_keyword_hits": hits,
        "memory_keyword_total": len(keywords),
        "retention_pct": retention_pct,
        "final_summary": final.get("conversation_summary"),
        "got_category": final.get("issue_category"),
        "collected_fields": final.get("collected_fields"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    journeys = json.loads(JOURNEYS_PATH.read_text()).get("journeys", [])
    claims = json.loads(CLAIMS_PATH.read_text()).get("cases", [])

    journey_results = [run_journey(j, args.verbose) for j in journeys]
    claims_results = [run_claims_case(c, args.verbose) for c in claims]
    wo_hits, wo_total, wo_rows = _score_waiting_on()

    mem_scores = [r["scores"]["memory_total"] for r in journey_results]
    reread_scores = [r["scores"]["reread_0_100"] for r in journey_results]
    report = {
        "sprint": "P16-Z10B",
        "journey_count": len(journey_results),
        "avg_memory_score": sum(mem_scores) / len(mem_scores) if mem_scores else 0,
        "avg_reread_score": sum(reread_scores) / len(reread_scores) if reread_scores else 0,
        "needs_wechat_count": sum(1 for r in journey_results if r["scores"]["needs_wechat"]),
        "category_match_count": sum(1 for r in journey_results if r["category_match"]),
        "waiting_on_auto_hits": wo_hits,
        "waiting_on_auto_total": wo_total,
        "waiting_on_scenarios": wo_rows,
        "journeys": journey_results,
        "claims": claims_results,
        "avg_claims_retention_pct": sum(c["retention_pct"] for c in claims_results) / len(claims_results)
        if claims_results
        else 0,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "role_d_battery.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    print(f"P16-Z10B Role D battery")
    print(f"  journeys: {len(journey_results)}")
    print(f"  avg memory (0-75): {report['avg_memory_score']:.1f}")
    print(f"  avg reread (0-100): {report['avg_reread_score']:.1f}")
    print(f"  needs WeChat: {report['needs_wechat_count']}/{len(journey_results)}")
    print(f"  category match: {report['category_match_count']}/{len(journey_results)}")
    print(f"  waiting_on auto: {report['waiting_on_auto_hits']}/{report['waiting_on_auto_total']}")
    print(f"  claims retention avg: {report['avg_claims_retention_pct']:.0f}%")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
