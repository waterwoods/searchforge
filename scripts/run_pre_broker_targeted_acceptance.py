#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.environ.setdefault("LLM_GENERATION_ENABLED", "0")

from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_for_append  # noqa: E402


SCENARIOS: list[dict] = [
    {
        "id": "PBTA-01",
        "name": "Add-Car clean path",
        "kind": "conversation",
        "turns": [
            "我想加新车报价",
            "2024 Tesla Model Y，邮编95131，下周五提车，主要驾驶人本人",
        ],
        "checks": {"handoff_ready": True, "quote_ready_status": "quote_ready"},
    },
    {
        "id": "PBTA-02",
        "name": "Add-Car partial to completion",
        "kind": "conversation",
        "turns": [
            "我想给新车加保报价。年份2023；车型Honda CR-V",
            "邮编90012，下周三提车，老婆开",
        ],
        "checks": {"handoff_ready": True, "quote_ready_status": "quote_ready"},
    },
    {
        "id": "PBTA-03",
        "name": "Add-Car correction path",
        "kind": "conversation",
        "turns": [
            "加一台2022宝马X5，邮编94506，明天提车，我开",
            "不对，是2023宝马X5",
        ],
        "checks": {"handoff_ready": True, "quote_ready_status": "quote_ready"},
    },
    {
        "id": "PBTA-04",
        "name": "Add-Car materials already sent",
        "kind": "conversation",
        "turns": [
            "2024 Tesla Model 3 加保 邮编95110 明天提车 本人开 行驶证照片发你微信了",
        ],
        "checks": {"handoff_ready": True, "follow_up_type": "already_sent"},
    },
    {
        "id": "PBTA-05",
        "name": "Add-Car ask-to-send prospective",
        "kind": "conversation",
        "turns": [
            "2024特斯拉Model 3，95131，明天提车，我自己开，要不要发你行驶证截图",
        ],
        "checks": {"handoff_ready": True, "follow_up_type": "new_info"},
    },
    {
        "id": "PBTA-06",
        "name": "Add-Car price-sensitive ballpark",
        "kind": "conversation",
        "turns": [
            "我想加一台2024 凯美瑞，邮编95131，下周提车，我开，大概会贵多少？先给我个大概范围",
        ],
        "checks": {"handoff_ready": True, "quote_ready_status": "quote_ready"},
    },
    {
        "id": "PBTA-07",
        "name": "Add-Car handoff and office-processing clarity",
        "kind": "conversation",
        "turns": [
            "我想加新车报价。年份2025；车型Tesla Model Y；邮编95131；预计下周五提车；主要驾驶人本人。",
        ],
        "checks": {"handoff_ready": True, "quote_ready_status": "quote_ready"},
    },
    {
        "id": "PBTA-08",
        "name": "Append boundary new issue",
        "kind": "append",
        "client_id": "chen_kui",
        "existing_source_text": "[客户] 2024 BMW X5 94102 下周提车 我开\n[系统] 报价资料已收集，办公室会尽快出价，有结果会联系您。",
        "latest_text": "另外我账单好像多扣了一笔，能帮我看下吗",
        "checks": {"case_boundary": "new_issue", "handoff_ready": True},
    },
    {
        "id": "PBTA-09A",
        "name": "Client isolation spot check (chen_kui)",
        "kind": "append",
        "client_id": "chen_kui",
        "existing_source_text": "[客户] 我想加一台2024宝马X5，zip 95131，下周提车，我自己开\n\n[系统] 报价资料已收集，办公室会尽快出价，有结果会联系您。",
        "latest_text": "发你微信了，行驶证截图",
        "checks": {"handoff_ready": True, "draft_contains": "办公室"},
    },
    {
        "id": "PBTA-09B",
        "name": "Client isolation spot check (socal_precision)",
        "kind": "append",
        "client_id": "socal_precision",
        "existing_source_text": "[客户] 我想加一台2024宝马X5，zip 95131，下周提车，我自己开\n\n[系统] 报价资料已收集，办公室会尽快出价，有结果会联系您。",
        "latest_text": "发你微信了，行驶证截图",
        "checks": {"handoff_ready": True, "draft_contains": "本所"},
    },
    {
        "id": "PBTA-10",
        "name": "Flagship all-info single message",
        "kind": "conversation",
        "turns": [
            "2024 Tesla Model Y，邮编95131，我自己开，想加进现有保单报价",
        ],
        "checks": {"handoff_ready": True, "quote_ready_status": "quote_incomplete"},
    },
]


def run_conversation(turns: list[str]) -> dict:
    conversation: list[dict[str, str]] = []
    result: dict = {}
    for msg in turns:
        result = triage_conversation(msg, conversation, client_id="chen_kui")
        draft = result.get("client_reply_draft") or ""
        conversation.append({"role": "customer", "text": msg})
        conversation.append({"role": "system", "text": draft})
    return result


def run_append(client_id: str, existing_source_text: str, latest_text: str) -> dict:
    return triage_for_append(existing_source_text, latest_text, client_id=client_id)


def evaluate(result: dict, checks: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []
    for key, expected in checks.items():
        if key == "draft_contains":
            draft = result.get("client_reply_draft") or ""
            if expected not in draft:
                failures.append(f"client_reply_draft missing '{expected}'")
            continue
        got = result.get(key)
        if got != expected:
            failures.append(f"{key}: got={got!r} expected={expected!r}")
    return len(failures) == 0, failures


def main() -> int:
    rows: list[dict] = []
    passed = 0

    for sc in SCENARIOS:
        if sc["kind"] == "conversation":
            result = run_conversation(sc["turns"])
        else:
            result = run_append(sc["client_id"], sc["existing_source_text"], sc["latest_text"])

        ok, failures = evaluate(result, sc["checks"])
        if ok:
            passed += 1

        rows.append(
            {
                "id": sc["id"],
                "name": sc["name"],
                "kind": sc["kind"],
                "checks": sc["checks"],
                "pass": ok,
                "failures": failures,
                "observed": {
                    "issue_category": result.get("issue_category"),
                    "handoff_ready": result.get("handoff_ready"),
                    "quote_ready_status": result.get("quote_ready_status"),
                    "follow_up_type": result.get("follow_up_type"),
                    "case_boundary": result.get("case_boundary"),
                    "client_reply_draft": result.get("client_reply_draft"),
                    "broker_next_step": result.get("broker_next_step"),
                    "still_needed_fields": result.get("still_needed_fields"),
                    "collected_fields": result.get("collected_fields"),
                },
            }
        )

    out = {
        "sprint": "PRE_BROKER_TARGETED_ACCEPTANCE_SPRINT",
        "llm_generation_enabled": os.getenv("LLM_GENERATION_ENABLED"),
        "passed": passed,
        "total": len(SCENARIOS),
        "results": rows,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if passed == len(SCENARIOS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
