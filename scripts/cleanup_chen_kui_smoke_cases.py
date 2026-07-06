#!/usr/bin/env python3
"""
Hide or backfill Chen Kui QA smoke/test cases — demo hygiene only.

Never truncates tables. Only touches explicit case IDs or smoke-tagged external_userid patterns.

Usage:
  PYTHONPATH=. python3 scripts/cleanup_chen_kui_smoke_cases.py --target qa --dry-run
  PYTHONPATH=. python3 scripts/cleanup_chen_kui_smoke_cases.py --target qa --apply
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

from scripts.demo_db_resolve import Target, apply_qa_postgres_env, resolve_db_identity

# Loop 2C simulated + Loop 2B partial smoke
HIDE_CASE_IDS: tuple[str, ...] = (
    "case_497318468f8c",
    "case_3c401096f5b2",
    "case_51bbb171f017",
    "case_cc82c457ca2b",
)

# Loop 2D live WeCom smoke — keep visible, backfill display fields
LIVE_SMOKE_CASE_IDS: tuple[str, ...] = (
    "case_2a1e00dc3b75",
    "case_16c897a66fe1",
)

SMOKE_EXT_PREFIXES: tuple[str, ...] = (
    "wm_loop2c_",
    "loop2b_",
)


def _configure(target: Target) -> None:
    if target == "qa":
        apply_qa_postgres_env(for_write=True)
        os.environ.setdefault("UNIFIED_INTAKE_DB_PRIMARY_READS", "1")
        os.environ.setdefault("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "1")
        os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "0"
    else:
        os.environ.setdefault("UNIFIED_INTAKE_JSON_CASE_WRITES", "1")
        os.environ.setdefault("UNIFIED_INTAKE_CASES_PATH", "data/unified_intake_cases.json")
        os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
        os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_READS", None)


def _load_case(case_id: str) -> dict[str, Any] | None:
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

    return get_case_for_read(case_id)


def _is_smoke_external(ext: str) -> bool:
    e = (ext or "").strip()
    return any(e.startswith(p) for p in SMOKE_EXT_PREFIXES)


def plan_actions() -> list[dict[str, Any]]:
    from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read

    actions: list[dict[str, Any]] = []
    seen: set[str] = set()

    for cid in HIDE_CASE_IDS:
        case = _load_case(cid)
        if not case:
            actions.append({"action": "skip", "case_id": cid, "reason": "not_found"})
            continue
        seen.add(cid)
        actions.append(
            {
                "action": "hide",
                "case_id": cid,
                "external_userid": case.get("wecom_external_userid"),
                "lane": case.get("service_lane"),
                "archived": case.get("workbench_archived"),
            }
        )

    for case in list_all_cases_for_read():
        cid = str(case.get("case_id") or "").strip()
        if not cid or cid in seen:
            continue
        ext = str(case.get("wecom_external_userid") or "")
        if _is_smoke_external(ext) and cid not in LIVE_SMOKE_CASE_IDS:
            seen.add(cid)
            actions.append(
                {
                    "action": "hide",
                    "case_id": cid,
                    "external_userid": ext,
                    "lane": case.get("service_lane"),
                    "archived": case.get("workbench_archived"),
                    "reason": "smoke_ext_prefix",
                }
            )

    for cid in LIVE_SMOKE_CASE_IDS:
        case = _load_case(cid)
        if not case:
            actions.append({"action": "skip", "case_id": cid, "reason": "not_found"})
            continue
        actions.append(
            {
                "action": "backfill",
                "case_id": cid,
                "external_userid": case.get("wecom_external_userid"),
                "lane": case.get("service_lane"),
                "customer_name": case.get("customer_name"),
                "workbench_tags": case.get("workbench_tags"),
            }
        )
    return actions


def _backfill_live_case(case_id: str, *, apply: bool) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation, _persist_case_after_update
    from services.fiqa_api.wecom.identity import wecom_customer_display_label
    from services.fiqa_api.wecom.lane_extractors import extract_claim_facts, extract_premium_facts
    from services.fiqa_api.wecom.minimal_lanes import _claim_tags, _premium_tags

    case = _load_case_for_mutation(case_id)
    if not case:
        return {"case_id": case_id, "status": "not_found"}

    ext = str(case.get("wecom_external_userid") or "")
    phone = str(case.get("customer_phone") or "").strip() or None
    display = wecom_customer_display_label(ext, customer_phone=phone)
    source = str(case.get("source_text") or "")
    lane = str(case.get("service_lane") or "")
    tags: list[str] = list(case.get("workbench_tags") or [])
    if not tags:
        if lane == "policy_review":
            tags = _premium_tags(extract_premium_facts(source))
        elif lane == "claim_lite":
            tags = _claim_tags(extract_claim_facts(source))

    changes: dict[str, Any] = {}
    if not str(case.get("customer_name") or "").strip():
        changes["customer_name"] = display
    if tags and not case.get("workbench_tags"):
        changes["workbench_tags"] = tags

    if not changes:
        return {"case_id": case_id, "status": "unchanged"}

    if not apply:
        return {"case_id": case_id, "status": "would_backfill", **changes}

    if changes.get("customer_name"):
        case["customer_name"] = changes["customer_name"]
    if changes.get("workbench_tags"):
        case["workbench_tags"] = changes["workbench_tags"]
    if not _persist_case_after_update(case_id, case):
        return {"case_id": case_id, "status": "persist_failed"}
    return {"case_id": case_id, "status": "backfilled", **changes}


def _hide_case(case_id: str, *, apply: bool) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_store import update_case_workbench_flags

    case = _load_case(case_id)
    if not case:
        return {"case_id": case_id, "status": "not_found"}
    if case.get("workbench_archived"):
        return {"case_id": case_id, "status": "already_archived"}
    if not apply:
        return {"case_id": case_id, "status": "would_hide"}
    updated = update_case_workbench_flags(case_id, archived=True)
    if not updated:
        return {"case_id": case_id, "status": "hide_failed"}
    return {"case_id": case_id, "status": "hidden"}


def run(*, target: Target, apply: bool) -> int:
    _configure(target)
    ident = resolve_db_identity(target, for_write=True)
    print(f"[INFO] target={target} db={ident.masked()} mode={'apply' if apply else 'dry-run'}")

    actions = plan_actions()
    results: list[dict[str, Any]] = []
    for item in actions:
        cid = item.get("case_id")
        if not cid:
            continue
        if item["action"] == "hide":
            print(f"[PLAN] hide {cid} ext={item.get('external_userid')} lane={item.get('lane')}")
            results.append(_hide_case(cid, apply=apply))
        elif item["action"] == "backfill":
            print(f"[PLAN] backfill {cid} lane={item.get('lane')}")
            results.append(_backfill_live_case(cid, apply=apply))
        else:
            print(f"[SKIP] {cid}: {item.get('reason')}")
            results.append(item)

    print("\n=== Results ===")
    for r in results:
        print(r)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Chen Kui smoke case cleanup (demo hygiene)")
    parser.add_argument("--target", choices=("qa", "local"), default="qa")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Explicit dry-run (default when --apply omitted)")
    args = parser.parse_args()
    if not args.apply:
        print("[INFO] DRY-RUN — pass --apply to execute")
    return run(target=args.target, apply=bool(args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
