#!/usr/bin/env python3
"""
Deterministic Add-Car C+ scenario library runner (triage_conversation).

Usage:
  PYTHONPATH=. LLM_GENERATION_ENABLED=0 python3 scripts/run_add_car_cplus_scenario_library.py \\
    --output results/add_car_cplus_baseline.json

Optional:
  --library-path tests/scenario_libraries/add_car_cplus_scenarios.py
  --markdown results/add_car_cplus_baseline.md
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.environ.setdefault("LLM_GENERATION_ENABLED", "0")

from services.fiqa_api.inbox_triage.triage import triage_conversation  # noqa: E402


def _load_scenario_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("add_car_cplus_scenarios", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load scenario library: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _get_field(result: dict[str, Any], field: str) -> Any:
    if "." in field:
        cur: Any = result
        for part in field.split("."):
            if not isinstance(cur, dict):
                return None
            cur = cur.get(part)
        return cur
    return result.get(field)


def _check_assertion(result: dict[str, Any], check: dict[str, Any]) -> tuple[bool, str]:
    op = (check.get("op") or "").strip().lower()
    field = str(check.get("field") or "")
    got = _get_field(result, field)

    if op == "eq":
        exp = check.get("value")
        if isinstance(exp, bool) or isinstance(got, bool):
            return bool(got) == bool(exp), f"{field}: got {got!r} expected {exp!r}"
        if str(got).strip().lower() == str(exp).strip().lower():
            return True, ""
        return False, f"{field}: got {got!r} expected {exp!r}"

    if op == "ne":
        exp = check.get("value")
        if str(got).strip().lower() != str(exp).strip().lower():
            return True, ""
        return False, f"{field}: expected != {exp!r} got {got!r}"

    if op == "contains":
        sub = str(check.get("value") or "")
        hay = "" if got is None else str(got)
        if sub.lower() in hay.lower():
            return True, ""
        return False, f"{field}: missing substring {sub!r} in {hay[:120]!r}"

    if op == "not_contains":
        sub = str(check.get("value") or "")
        hay = "" if got is None else str(got)
        if sub.lower() not in hay.lower():
            return True, ""
        return False, f"{field}: should not contain {sub!r}"

    if op == "not_regex":
        pat = str(check.get("pattern") or "")
        hay = "" if got is None else str(got)
        if not re.search(pat, hay, re.I):
            return True, ""
        return False, f"{field}: matched forbidden pattern {pat!r}"

    if op == "still_needed_excludes":
        # field is the tier1 slot name that should NOT appear in still_needed_fields
        slot = str(check.get("field") or "")
        sn = result.get("still_needed_fields") or []
        if not isinstance(sn, list):
            return False, "still_needed_fields not a list"
        flat = [str(x).lower() for x in sn]
        if slot.lower() in flat:
            return False, f"still_needed_fields still lists {slot!r}"
        return True, ""

    if op == "in_list":
        lst = result.get(field) or []
        if not isinstance(lst, list):
            return False, f"{field} not a list"
        exp = str(check.get("value") or "").strip().lower()
        if any(str(x).strip().lower() == exp for x in lst):
            return True, ""
        return False, f"{field} missing value {exp!r}"

    return False, f"unknown op {op!r}"


def _turn_index(assert_turn: int, n_turns: int) -> int:
    if assert_turn == -1:
        return n_turns - 1
    return assert_turn


def _extract_turn_snapshot(result: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "service_type",
        "primary_vehicle_summary",
        "collected_fields",
        "still_needed_fields",
        "handoff_ready",
        "action_ready",
        "follow_up_type",
        "client_reply_draft",
        "broker_next_step",
        "quote_ready_status",
        "issue_category",
        "triage_path",
    )
    return {k: result.get(k) for k in keys}


def _classify_failure(msg: str) -> str:
    m = msg.lower()
    if "handoff_ready" in m:
        return "handoff_ready_mismatch"
    if "service_type" in m:
        return "service_type_mismatch"
    if "follow_up_type" in m:
        return "follow_up_type_mismatch"
    if "primary_vehicle_summary" in m or "substring" in m:
        return "summary_or_substring_mismatch"
    if "forbidden pattern" in m or "matched forbidden" in m:
        return "forbidden_price_or_tone_in_draft"
    if "not_regex" in m:
        return "draft_regex_guardrail"
    return "other_assertion_failure"


def run_all(
    scenarios: list[dict[str, Any]],
    *,
    client_id: str = "chen_kui",
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    t0 = time.perf_counter()

    for s in scenarios:
        sid = s.get("id", "?")
        turns: list[str] = list(s.get("user_turns") or [])
        soft_route = s.get("soft_route")
        conv: list[dict[str, str]] = []
        turn_records: list[dict[str, Any]] = []
        fail_msgs: list[str] = []
        assertion_results: list[dict[str, Any]] = []

        for i, text in enumerate(turns):
            kwargs: dict[str, Any] = {"client_id": client_id}
            if soft_route:
                kwargs["soft_route"] = soft_route
            out = triage_conversation(text, conv, **kwargs)
            snap = _extract_turn_snapshot(out)
            snap["turn_index"] = i
            snap["user_text"] = text
            turn_records.append({"snapshot": snap, "raw_keys": sorted(out.keys())})

            conv.append({"role": "customer", "text": text})

        last = out
        passed = True
        for ag in s.get("assertions") or []:
            idx = _turn_index(int(ag.get("turn", -1)), len(turns))
            if idx < 0 or idx >= len(turn_records):
                passed = False
                msg = f"assertion block turn {ag.get('turn')!r} out of range (n={len(turns)})"
                fail_msgs.append(msg)
                assertion_results.append({"turn": ag.get("turn"), "ok": False, "detail": msg})
                continue
            target = turn_records[idx]["snapshot"]
            # Re-run not stored full result — snapshot only. Assertions run on full out per turn.
            # Reconstruct by re-running triage up to idx (cheap for library size).
            conv2: list[dict[str, str]] = []
            kwargs2: dict[str, Any] = {"client_id": client_id}
            if soft_route:
                kwargs2["soft_route"] = soft_route
            res_at: dict[str, Any] | None = None
            for j in range(idx + 1):
                res_at = triage_conversation(turns[j], conv2, **kwargs2)
                conv2.append({"role": "customer", "text": turns[j]})
            assert res_at is not None
            for chk in ag.get("checks") or []:
                ok, detail = _check_assertion(res_at, chk)
                assertion_results.append(
                    {
                        "turn": ag.get("turn"),
                        "resolved_index": idx,
                        "check": chk,
                        "ok": ok,
                        "detail": detail,
                    }
                )
                if not ok:
                    passed = False
                    fail_msgs.append(f"turn {idx}: {detail}")

        status = "pass" if passed else "fail"

        results.append(
            {
                "id": sid,
                "category": s.get("category"),
                "description": s.get("description"),
                "expected_risk_tags": s.get("expected_risk_tags"),
                "status": status,
                "failed_assertions": fail_msgs,
                "assertion_results": assertion_results,
                "turns": turn_records,
                "final_snapshot": _extract_turn_snapshot(last),
            }
        )

    elapsed = time.perf_counter() - t0

    by_cat: Counter[str] = Counter()
    by_cat_pass: Counter[str] = Counter()
    fail_patterns: Counter[str] = Counter()

    for row in results:
        c = str(row.get("category") or "unknown")
        by_cat[c] += 1
        if row.get("status") == "pass":
            by_cat_pass[c] += 1
        for fm in row.get("failed_assertions") or []:
            fail_patterns[_classify_failure(fm)] += 1

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "llm_generation_enabled": os.environ.get("LLM_GENERATION_ENABLED", ""),
        "scenario_count": len(scenarios),
        "pass_count": sum(1 for r in results if r["status"] == "pass"),
        "fail_count": sum(1 for r in results if r["status"] == "fail"),
        "partial_count": sum(
            1
            for r in results
            if r["status"] == "pass"
            and str((r.get("final_snapshot") or {}).get("service_type") or "").lower() == "add_car"
            and (r.get("final_snapshot") or {}).get("handoff_ready") is not True
        ),
        "elapsed_seconds": round(elapsed, 3),
        "by_category_total": dict(by_cat),
        "by_category_pass": dict(by_cat_pass),
        "top_failure_patterns": fail_patterns.most_common(20),
    }

    return {"summary": summary, "results": results}


def _markdown_report(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    lines = [
        "# Add-Car C+ scenario library run",
        "",
        f"- Generated: {s.get('generated_at')}",
        f"- Scenarios: {s.get('scenario_count')}",
        f"- Pass: {s.get('pass_count')}  Fail: {s.get('fail_count')}",
        f"- Elapsed: {s.get('elapsed_seconds')}s",
        "",
        "## By category",
        "",
    ]
    totals = s.get("by_category_total") or {}
    passes = s.get("by_category_pass") or {}
    for cat in sorted(totals.keys()):
        lines.append(f"- **{cat}**: {passes.get(cat, 0)}/{totals[cat]} pass")
    lines.extend(["", "## Top failure patterns", ""])
    for pat, n in (s.get("top_failure_patterns") or [])[:12]:
        lines.append(f"- {pat}: {n}")
    lines.extend(["", "## Failed scenarios (sample)", ""])
    for r in payload["results"]:
        if r.get("status") != "fail":
            continue
        lines.append(f"### {r.get('id')}")
        lines.append("")
        for fm in (r.get("failed_assertions") or [])[:5]:
            lines.append(f"- {fm}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--library-path",
        type=Path,
        default=REPO / "tests/scenario_libraries/add_car_cplus_scenarios.py",
    )
    ap.add_argument("--output", type=Path, default=REPO / "results/add_car_cplus_baseline.json")
    ap.add_argument("--markdown", type=Path, default=None)
    ap.add_argument("--client-id", default="chen_kui")
    args = ap.parse_args()

    mod = _load_scenario_module(args.library_path)
    scenarios = list(getattr(mod, "SCENARIOS", []))
    if not scenarios:
        print("No scenarios in library.", file=sys.stderr)
        return 2

    payload = run_all(scenarios, client_id=args.client_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))

    md_path = args.markdown
    if md_path is None:
        md_path = args.output.with_suffix(".md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_markdown_report(payload), encoding="utf-8")
    print(f"Wrote {args.output} and {md_path}", file=sys.stderr)
    return 0 if payload["summary"]["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
