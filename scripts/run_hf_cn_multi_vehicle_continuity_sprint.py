#!/usr/bin/env python3
"""
HIGH_FREQUENCY_REAL_LANGUAGE + MULTI_VEHICLE_CONTINUITY — bounded triage harness.

Uses triage_for_append only (no FastAPI import) to avoid app_main stdout noise.
JSON to stdout. Prior threads are minimal add_car formal-style text.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_for_append  # noqa: E402

CTX = {"formal_submitted_at": "2026-04-04T12:00:00Z", "service_record_append": True}
CLIENT = "chen_kui"

TAGGED_PRIOR = (
    "[客户] 我想加车，2024 Toyota Camry，ZIP 90210，下周提车，我自己开\n\n"
    "[系统] 已记录加车信息，会继续整理。"
)
PLAIN_PRIOR = "加车：2022 Mazda CX-5，邮编94501，下周提车，主驾本人，姓名钱七，电话510-555-0303。"


def _run() -> dict:
    rows: list[dict] = []
    scenarios: list[tuple[str, str, str, str]] = [
        # id, role, prior, append
        ("S1", "C", TAGGED_PRIOR, "那台车再帮我看看能不能便宜一点"),
        ("S2", "C", TAGGED_PRIOR, "再确认一下刚才那辆的报价"),
        ("S3", "C", TAGGED_PRIOR, "再报一次价，还是刚才那台"),
        ("S4", "C", TAGGED_PRIOR, "全险太贵了，能不能只买半险？大概差多少？"),
        ("S5", "C+", TAGGED_PRIOR, "不好意思不是X5是X3，其他不变"),
        ("S6", "C+", TAGGED_PRIOR, "还有一辆2021 Prius也想问，同地址"),
        ("S7", "C+", PLAIN_PRIOR, "续保太贵，那台车也一起帮我看看"),
        ("S8", "C+", TAGGED_PRIOR, "我想顺便问一下：我另一张保单续保的事能不能和这辆车一起让办公室看？"),
        ("S9", "C", TAGGED_PRIOR, "另外我昨天小车祸了，要走理赔，请帮我开新案子"),
        ("S10", "C+", TAGGED_PRIOR, "那张保单和刚才加车能不能一起让办公室看？"),
        ("S11", "C+", TAGGED_PRIOR, "先不问细节了，另一台车也要加进去，Prius"),
        ("S12", "C", TAGGED_PRIOR, "嗯嗯"),
    ]
    for sid, role, prior, append in scenarios:
        out = triage_for_append(
            prior,
            append,
            client_id=CLIENT,
            reply_truth_context=CTX,
        )
        rows.append(
            {
                "story_id": sid,
                "role_pattern": role,
                "append_excerpt": append[:72] + ("…" if len(append) > 72 else ""),
                "case_boundary": out.get("case_boundary"),
                "case_boundary_action": out.get("case_boundary_action"),
                "append_blocked_new_issue": out.get("append_blocked_new_issue"),
                "boundary_reason": (out.get("boundary_reason") or "")[:240],
                "service_type": out.get("service_type"),
            }
        )
    return {"scenarios": rows, "harness": "triage_for_append_only", "client_id": CLIENT}


def main() -> int:
    print(json.dumps(_run(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
