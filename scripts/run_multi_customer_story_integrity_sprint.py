#!/usr/bin/env python3
"""
MULTI_CUSTOMER_STORY_DRIVEN_CLOSED_LOOP_INTEGRITY_SPRINT — bounded API runner.

Uses httpx.AsyncClient + ASGITransport (same handlers as live HTTP). Isolated JSON
case/session files via UNIFIED_INTAKE_CASES_PATH / UNIFIED_INTAKE_SESSIONS_PATH.
Clears DB env to avoid PG. No Role C LLM calls.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _isolate_store() -> Path:
    tdir = Path(tempfile.mkdtemp(prefix="mc_story_integrity_"))
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(tdir / "unified_intake_cases.json")
    os.environ["UNIFIED_INTAKE_SESSIONS_PATH"] = str(tdir / "unified_intake_sessions.json")
    for k in (
        "DATABASE_URL",
        "SERVICE_RECORD_DATABASE_URL",
        "UNIFIED_INTAKE_DB_PRIMARY_READS",
        "UNIFIED_INTAKE_DB_PRIMARY_WRITES",
        "UNIFIED_INTAKE_PG_DUAL_WRITE",
    ):
        os.environ.pop(k, None)
    return tdir


@dataclass
class StepTrace:
    story: str
    step: str
    request_summary: str
    status_code: int
    keys: dict[str, Any] = field(default_factory=dict)


async def _post_triage(client: Any, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    r = await client.post("/api/inbox/triage", json=payload, timeout=120.0)
    try:
        body = r.json() if r.content else {}
    except Exception:
        body = {"_raw": r.text[:800]}
    return r.status_code, body if isinstance(body, dict) else {"_parsed": body}


async def _append(client: Any, case_id: str, new_message: str, client_id: str) -> tuple[int, dict[str, Any]]:
    r = await client.post(
        f"/api/inbox/cases/{case_id}/append-message",
        json={"new_message": new_message, "client_id": client_id},
        timeout=120.0,
    )
    try:
        body = r.json() if r.content else {}
    except Exception:
        body = {"_raw": r.text[:800]}
    return r.status_code, body if isinstance(body, dict) else {"_parsed": body}


def _pick(body: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": body.get("case_id"),
        "service_lane": body.get("service_lane"),
        "formal_submitted_at": body.get("formal_submitted_at"),
        "case_boundary": body.get("case_boundary"),
        "case_boundary_action": body.get("case_boundary_action"),
        "boundary_reason": (body.get("boundary_reason") or "")[:220],
        "append_blocked_new_issue": body.get("append_blocked_new_issue"),
        "lifecycle_status": body.get("lifecycle_status"),
        "handoff_ready": body.get("handoff_ready"),
        "still_needed_fields": body.get("still_needed_fields"),
        "collected_fields": body.get("collected_fields"),
        "case_persisted": body.get("case_persisted"),
        "issue_category": body.get("issue_category"),
        "vehicle_key": body.get("vehicle_key"),
    }


async def _run_stories() -> dict[str, Any]:
    store_dir = _isolate_store()
    import httpx

    from httpx import ASGITransport

    from services.fiqa_api.app_main import app  # noqa: WPS433

    transport = ASGITransport(app=app)
    traces: list[StepTrace] = []
    case_map: dict[str, str] = {}
    client_id = "chen_kui"

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        async def triage(story: str, step: str, payload: dict[str, Any]) -> dict[str, Any]:
            sc, body = await _post_triage(client, payload)
            summ = (
                f"text_len={len(payload.get('text') or '')} persist={payload.get('persist_case')} "
                f"formal={payload.get('formal_submit')} case_id={payload.get('case_id')}"
            )
            traces.append(
                StepTrace(
                    story=story,
                    step=step,
                    request_summary=summ,
                    status_code=sc,
                    keys=_pick(body) if sc == 200 else {"http_error": body},
                )
            )
            return body

        async def append_msg(story: str, step: str, cid: str, msg: str) -> dict[str, Any]:
            sc, body = await _append(client, cid, msg, client_id)
            traces.append(
                StepTrace(
                    story=story,
                    step=step,
                    request_summary=f"append case_id={cid}",
                    status_code=sc,
                    keys=_pick(body) if sc == 200 else {"http_error": body},
                )
            )
            return body

        # --- Story D: incomplete then complete ---
        sid_d = str(uuid.uuid4())
        await triage(
            "D",
            "turn1_vague",
            {
                "text": "想加车",
                "client_id": client_id,
                "soft_route": "add_car",
                "session_id": sid_d,
                "persist_case": False,
            },
        )
        full_add = (
            "我想给2024款BMW 330i做加车报价，邮编90210，下周三提车，主驾是我本人，姓名张三，电话415-555-0101。"
        )
        body_d = await triage(
            "D",
            "turn2_formal_submit",
            {
                "text": full_add,
                "client_id": client_id,
                "soft_route": "add_car",
                "session_id": sid_d,
                "conversation_turns": [{"role": "customer", "text": "想加车"}],
                "formal_submit": True,
                "persist_case": True,
            },
        )
        if body_d.get("case_id"):
            case_map["D"] = body_d["case_id"]

        # --- Story A: same_case continuation ---
        sid_a = str(uuid.uuid4())
        full_a = (
            "加车需求：2024 Honda Accord，邮编94105，下周五提车，主驾本人，姓名李四，电话650-555-0001。"
        )
        body_a = await triage(
            "A",
            "create_formal",
            {
                "text": full_a,
                "client_id": client_id,
                "soft_route": "add_car",
                "session_id": sid_a,
                "formal_submit": True,
                "persist_case": True,
            },
        )
        if body_a.get("case_id"):
            case_map["A"] = body_a["case_id"]
            await append_msg(
                "A",
                "append_price_followup",
                body_a["case_id"],
                "谢谢。我想问一下，如果全险太贵，能不能只买半险？大概能便宜多少？",
            )

        # --- Story C: new_issue (claim) ---
        sid_c = str(uuid.uuid4())
        body_c = await triage(
            "C",
            "create_add_car",
            {
                "text": "想加一辆2023 Toyota Camry，邮编90210，明天提车，主驾我，姓名赵六，电话310-555-0202。",
                "client_id": client_id,
                "soft_route": "add_car",
                "session_id": sid_c,
                "formal_submit": True,
                "persist_case": True,
            },
        )
        if body_c.get("case_id"):
            case_map["C"] = body_c["case_id"]
            await append_msg(
                "C",
                "append_claim_new_issue",
                body_c["case_id"],
                "另外我这边昨天小车祸了，需要走理赔，请帮我开一个新案子。",
            )

        # --- Story G: borderline pivot ---
        sid_g = str(uuid.uuid4())
        body_g = await triage(
            "G",
            "create_add_car",
            {
                "text": "加车：2022 Mazda CX-5，邮编94501，下周提车，主驾本人，姓名钱七，电话510-555-0303。",
                "client_id": client_id,
                "soft_route": "add_car",
                "session_id": sid_g,
                "formal_submit": True,
                "persist_case": True,
            },
        )
        if body_g.get("case_id"):
            case_map["G"] = body_g["case_id"]
            await append_msg(
                "G",
                "append_borderline_pivot",
                body_g["case_id"],
                "先不问加车细节了，我想顺便问一下：我另一张保单续保的事能不能和这辆车一起让办公室看？",
            )

        # --- Story B: multi-vehicle ---
        await triage(
            "B",
            "two_vehicles_one_message",
            {
                "text": "我想同时给两辆车报价：2024 Honda Civic 90210 下周提车 我开；还有一辆2021 Toyota Prius 同地址 给我老婆开。电话 408-555-0404，姓名孙八。",
                "client_id": client_id,
                "soft_route": "add_car",
                "session_id": str(uuid.uuid4()),
                "formal_submit": True,
                "persist_case": True,
            },
        )

        # --- Story E / F: isolation ---
        for label, name, phone in (
            ("E", "陈九", "650-111-2222"),
            ("F", "周十", "650-333-4444"),
        ):
            body = await triage(
                label,
                "isolation_add_car",
                {
                    "text": f"加车 2024 Tesla Model Y {phone} 邮编 94107 下周提车 主驾本人 姓名{name}",
                    "client_id": client_id,
                    "soft_route": "add_car",
                    "session_id": str(uuid.uuid4()),
                    "formal_submit": True,
                    "persist_case": True,
                },
            )
            if body.get("case_id"):
                case_map[label] = body["case_id"]

        # --- Story H: correction same_case ---
        sid_h = str(uuid.uuid4())
        body_h = await triage(
            "H",
            "create",
            {
                "text": "加车 2024 Subaru Outback 95814 下周提车 主驾本人 姓名吴十一 电话916-555-0505",
                "client_id": client_id,
                "soft_route": "add_car",
                "session_id": sid_h,
                "formal_submit": True,
                "persist_case": True,
            },
        )
        if body_h.get("case_id"):
            case_map["H"] = body_h["case_id"]
            await append_msg(
                "H",
                "append_correction",
                body_h["case_id"],
                "不好意思，车型写错了，是2024 Subaru Forester 不是 Outback，其他不变。",
            )

        lr = await client.get("/api/inbox/cases?limit=50", timeout=60.0)
        list_body: dict[str, Any] = {}
        if lr.status_code == 200:
            list_body = lr.json()

    return {
        "store_dir": str(store_dir),
        "case_map": case_map,
        "traces": [
            {
                "story": t.story,
                "step": t.step,
                "request_summary": t.request_summary,
                "status_code": t.status_code,
                "snapshot": t.keys,
            }
            for t in traces
        ],
        "list_cases": list_body,
    }


def main() -> int:
    out = asyncio.run(_run_stories())
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
