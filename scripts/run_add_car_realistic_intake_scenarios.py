#!/usr/bin/env python3
"""
Add-Car realistic North American Chinese-style intake battery (rule-based).

Usage:
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_add_car_realistic_intake_scenarios.py

Requires triage_conversation (same path as Unified Intake API merge semantics).
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

from services.fiqa_api.inbox_triage.triage import triage_conversation  # noqa: E402

SCENARIOS: list[dict[str, str]] = [
    {
        "id": "R1",
        "name": "simple_direct",
        "text": "我要加一台2024 Tesla Model 3，95131，明天提车，我自己开",
    },
    {
        "id": "R2",
        "name": "office_style_polite_question",
        "text": "我明天提一辆2024 Model 3，邮编95131，主要我本人开，要不要先发你行驶证或者购车文件？",
    },
    {
        "id": "R3",
        "name": "date_correction",
        "text": "我准备加车，2025 BMW X5，邮编92705，我开。哦对，不是明天提，是这个周五提车。",
    },
    {
        "id": "R4",
        "name": "repeated_calendar_date",
        "text": "我这个车大概3月8号提，哦不对，应该是3月10号提车，BMW X5，92705，我自己开。",
    },
    {
        "id": "R5",
        "name": "mixed_zh_en",
        "text": "想加个新车 quote，2024 Tesla Model Y，zip 95131，this Friday pick up，我本人开，要不要先把VIN发你？",
    },
    {
        "id": "R6",
        "name": "incomplete_materials",
        "text": "我想先加车报价，2024 Honda CRV，Irvine 92618，下周提车，我跟我老婆都可能开，VIN还没拿到，可以先报吗？",
    },
    {
        "id": "R7",
        "name": "supplement_material_wording",
        "text": "加一台2024 Toyota Camry，95131，周五提车，我本人开。购车文件还没出来，车牌也没有。行驶证昨天已经发过了。VIN我等等发你。",
    },
]


def main() -> int:
    out: list[dict[str, object]] = []
    for s in SCENARIOS:
        r = triage_conversation(s["text"], [], client_id="chen_kui")
        out.append(
            {
                "id": s["id"],
                "name": s["name"],
                "issue_category": r.get("issue_category"),
                "quote_ready_status": r.get("quote_ready_status"),
                "collected_fields": r.get("collected_fields"),
                "still_needed_fields": r.get("still_needed_fields"),
                "handoff_ready": r.get("handoff_ready"),
                "triage_path": r.get("triage_path"),
            }
        )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
