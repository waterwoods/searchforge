#!/usr/bin/env python3
"""
P16-Y Case Intelligence battery runner.

Runs 50 cases through triage_conversation, scores with P16Y rubric, writes JSON report.

Usage:
  PYTHONPATH=. python3 scripts/run_p16y_case_battery.py [--label before|after] [--verbose]
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

from services.fiqa_api.inbox_triage.triage import triage_conversation

CASES_PATH = REPO / "configs" / "p16y_50_cases.json"
OUT_DIR = REPO / "docs" / "product_constitution" / ".p16y_results"

GENERIC_BROKER_MARKERS = (
    "review the",
    "follow up shortly",
    "provide more details",
    "request clarification",
    "reach out shortly",
    "earliest convenience",
)


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _load_cases() -> list[dict]:
    data = json.loads(CASES_PATH.read_text())
    return data.get("cases", [])


def _run_case(case: dict) -> dict:
    turns = case.get("turns") or []
    latest = case.get("input") or ""
    result = triage_conversation(latest, turns)
    return result


def _score_understanding(case: dict, result: dict) -> tuple[int, list[str]]:
    """0-25: category + urgency + summary intent."""
    notes: list[str] = []
    score = 0
    exp_cat = (case.get("expected_category") or "").lower()
    got_cat = (result.get("issue_category") or "").lower()
    if got_cat == exp_cat:
        score += 12
    else:
        notes.append(f"category: got {got_cat}, expected {exp_cat}")

    exp_urg = (case.get("expected_urgency") or "").lower()
    got_urg = (result.get("urgency") or "").lower()
    if got_urg == exp_urg:
        score += 8
    elif abs(["low", "medium", "high", "critical"].index(got_urg) - ["low", "medium", "high", "critical"].index(exp_urg)) == 1:
        score += 4
        notes.append(f"urgency near-miss: got {got_urg}, expected {exp_urg}")
    else:
        notes.append(f"urgency: got {got_urg}, expected {exp_urg}")

    summary = (result.get("conversation_summary") or "").lower()
    intent_hint = case.get("expected_intent_hint") or ""
    if intent_hint:
        hint_map = {
            "address": ("address", "garaging", "搬家", "moved"),
            "driver": ("driver", "司机", "驾照", "teen"),
            "claim": ("claim", "accident", "事故", "追尾"),
            "add car": ("add car", "加车", "quote", "报价", "camry", "vin"),
        }
        markers = hint_map.get(intent_hint, (intent_hint,))
        if any(m in summary or m in (result.get("broker_next_step") or "").lower() for m in markers):
            score += 5
        else:
            notes.append(f"summary missing intent hint: {intent_hint}")
    else:
        if summary and len(summary) > 20:
            score += 5
        else:
            notes.append("summary too thin")
    return min(score, 25), notes


def _score_missing_info(case: dict, result: dict) -> tuple[int, list[str]]:
    """0-25: still_needed + collected gap detection."""
    notes: list[str] = []
    score = 8  # baseline for having structured fields
    still = [str(x).lower() for x in (result.get("still_needed_fields") or [])]
    collected = [str(x).lower() for x in (result.get("collected_fields") or [])]
    summary = (result.get("conversation_summary") or "").lower()
    broker = (result.get("broker_next_step") or "").lower()
    prep = (result.get("client_prep") or "").lower()

    exp_still = case.get("expected_still_any") or []
    if exp_still:
        if any(e.lower() in still for e in exp_still):
            score += 8
        else:
            notes.append(f"still_needed miss: expected one of {exp_still}, got {still}")
    else:
        score += 4

    exp_collected = case.get("expected_collected_any") or []
    if exp_collected:
        if any(e.lower() in collected or e.lower().replace("_", " ") in summary for e in exp_collected):
            score += 8
        else:
            notes.append(f"collected miss: expected one of {exp_collected}, got {collected}")
    else:
        score += 4

    if case.get("expected_deadline"):
        deadline_found = any(
            m in summary or m in broker or m in prep or m in collected
            for m in ("deadline", "7 day", "14 day", "10 day", "days", "due", "期限", "今天", "friday", "3/15")
        )
        if deadline_found:
            score += 5
        else:
            notes.append("deadline not surfaced in case output")

    if case.get("expected_policy_number"):
        pol_found = any(m in summary or m in collected for m in ("policy", "8829101", "ca-8829101"))
        if pol_found:
            score += 4
        else:
            notes.append("policy number not extracted")

    return min(score, 25), notes


def _score_office_actionability(case: dict, result: dict) -> tuple[int, list[str]]:
    """0-25: broker_next_step quality + draft language."""
    notes: list[str] = []
    score = 0
    broker = (result.get("broker_next_step") or "").strip()
    draft = (result.get("client_reply_draft") or "").strip()
    prep = (result.get("client_prep") or "").strip()

    if broker and len(broker) > 25:
        score += 8
        if not any(m in broker.lower() for m in GENERIC_BROKER_MARKERS):
            score += 7
        else:
            score += 3
            notes.append("broker_next_step feels generic")
    else:
        notes.append("broker_next_step too short or empty")

    if prep and prep.lower() not in ("n/a", "na"):
        score += 4
    else:
        notes.append("client_prep thin")

    if draft and len(draft) > 15:
        score += 3
        if case.get("expected_draft_zh") and not _contains_chinese(draft):
            notes.append("expected Chinese draft")
            score -= 2
        if case.get("expected_draft_en") and _contains_chinese(draft):
            notes.append("expected English draft")
            score -= 2
    else:
        notes.append("draft too short")

    if result.get("manual_followup_needed") is not None:
        score += 3

    return min(max(score, 0), 25), notes


def _score_multi_message(case: dict, result: dict) -> tuple[int, list[str]]:
    """0-25: multi-turn context merge."""
    notes: list[str] = []
    if not case.get("multi_turn"):
        # Single-turn: credit if summary mentions message count
        summary = result.get("conversation_summary") or ""
        if "customer message" in summary.lower() or "1 customer" in summary.lower():
            return 22, []
        return 20, []

    score = 5
    turns = case.get("turns") or []
    summary = (result.get("conversation_summary") or "").lower()
    collected = [str(x).lower() for x in (result.get("collected_fields") or [])]

    if f"{len(turns) + 1} customer message" in summary or "2 customer message" in summary or "3 customer message" in summary:
        score += 8
    else:
        notes.append("multi-turn message count not reflected")

    # Prior turn content should influence output
    prior_text = " ".join(t.get("text", "") for t in turns).lower()
    if prior_text:
        keywords = [w for w in re.findall(r"\w{4,}", prior_text) if w not in ("customer", "the", "this", "that")]
        hits = sum(1 for k in keywords[:5] if k in summary or k in " ".join(collected))
        if hits >= 1:
            score += 7
        else:
            notes.append("prior turn context weak in summary/collected")

    exp_collected = case.get("expected_collected_any") or []
    if exp_collected and any(e.lower() in collected for e in exp_collected):
        score += 5

    return min(score, 25), notes


def score_case(case: dict, result: dict) -> dict:
    u, u_notes = _score_understanding(case, result)
    m, m_notes = _score_missing_info(case, result)
    o, o_notes = _score_office_actionability(case, result)
    mt, mt_notes = _score_multi_message(case, result)
    total = u + m + o + mt
    return {
        "understanding": u,
        "missing_info": m,
        "office_actionability": o,
        "multi_message": mt,
        "total": total,
        "notes": u_notes + m_notes + o_notes + mt_notes,
    }


def run_battery(label: str, verbose: bool) -> dict:
    cases = _load_cases()
    results = []
    for case in cases:
        cid = case["id"]
        triage = _run_case(case)
        scores = score_case(case, triage)
        entry = {
            "id": cid,
            "category": case.get("category"),
            "input_preview": (case.get("input") or "")[:100],
            "multi_turn": case.get("multi_turn", False),
            "expected_category": case.get("expected_category"),
            "got_category": triage.get("issue_category"),
            "got_urgency": triage.get("urgency"),
            "conversation_summary": triage.get("conversation_summary"),
            "broker_next_step": triage.get("broker_next_step"),
            "still_needed_fields": triage.get("still_needed_fields"),
            "collected_fields": triage.get("collected_fields"),
            "client_reply_draft": triage.get("client_reply_draft"),
            "scores": scores,
        }
        results.append(entry)
        if verbose:
            print(f"{cid}: {scores['total']}/100 — {scores['notes'][:2]}")

    totals = [r["scores"]["total"] for r in results]
    dims = ["understanding", "missing_info", "office_actionability", "multi_message"]
    dim_avgs = {d: sum(r["scores"][d] for r in results) / len(results) for d in dims}
    report = {
        "label": label,
        "case_count": len(results),
        "avg_total": sum(totals) / len(totals),
        "avg_by_dimension": dim_avgs,
        "cases": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"p16y_battery_{label}.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"\n{label}: avg {report['avg_total']:.1f}/100")
    for d, v in dim_avgs.items():
        print(f"  {d}: {v:.1f}/25")
    print(f"Wrote {out_path}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="before", choices=["before", "after"])
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    run_battery(args.label, args.verbose)


if __name__ == "__main__":
    main()
